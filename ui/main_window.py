# -*- coding: utf-8 -*-
"""
Главное окно приложения поиска изображений по образцу.
"""

import os
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QWidget, QVBoxLayout, QStatusBar, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread

from ui.control_panel import ControlPanel
from ui.index_dialog import IndexDialog
from ui.results_dialog import ResultsDialog
from workers.search_worker import SearchWorker
from workers.index_worker import IndexWorker
from utils.file_utils import create_results_folder, save_search_results
from batch_processing.batch_search import BatchSearchProcessor


# Создаем отдельный класс для выполнения индексированного поиска в фоновом потоке
class IndexedSearchWorker(QThread):
    """
    Рабочий поток для выполнения поиска по индексу.
    """
    progress_update = pyqtSignal(int)
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, query_image_path, index_path, extractor, similarity_threshold, max_results):
        """
        Инициализация рабочего потока.

        Args:
            query_image_path (str): Путь к изображению запроса
            index_path (str): Путь к индексу
            extractor: Экстрактор признаков
            similarity_threshold (float): Порог сходства
            max_results (int): Максимальное количество результатов
        """
        super().__init__()
        self.query_image_path = query_image_path
        self.index_path = index_path
        self.extractor = extractor
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results
        self.batch_processor = BatchSearchProcessor()

    def run(self):
        """
        Выполнение поиска по индексу.
        """
        try:
            # Обновляем прогресс
            self.progress_update.emit(10)

            # Извлекаем признаки из запроса
            query_features = self.extractor.extract_features(self.query_image_path)

            if query_features is None:
                self.error_occurred.emit("Не удалось извлечь признаки из изображения запроса")
                return

            self.progress_update.emit(30)

            # Загружаем индекс и выполняем поиск
            results = self.batch_processor.search_in_index(
                query_features,
                self.index_path,
                self.similarity_threshold,
                self.max_results
            )

            self.progress_update.emit(90)

            # Отправляем результаты
            self.result_ready.emit(results)

            self.progress_update.emit(100)

        except Exception as e:
            self.error_occurred.emit(f"Ошибка при поиске: {str(e)}")


class ImageSearchApp(QMainWindow):
    """
    Главное окно приложения для поиска изображений по образцу.
    """

    def __init__(self):
        """
        Инициализация главного окна приложения.
        """
        super().__init__()

        # Инициализация переменных
        self.search_worker = None
        self.index_worker = None
        self.indexed_search_worker = None
        self.last_results = []

        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        self.setWindowTitle("Поиск изображений по образцу")
        self.setGeometry(100, 100, 800, 600)  # Уменьшаем размер, так как убираем панель результатов

        # Установка иконки приложения
        icon_path = "ui/styles/app-icon.svg"
        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        # Основной виджет и компоновка
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Только панель управления
        self.control_panel = ControlPanel()
        self.control_panel.search_requested.connect(self.start_search)
        self.control_panel.save_results_requested.connect(self.show_last_results)
        self.control_panel.cancel_search_requested.connect(self.cancel_search)
        self.control_panel.index_folder_requested.connect(self.show_index_dialog)

        main_layout.addWidget(self.control_panel)

        # Устанавливаем центральный виджет окна
        self.setCentralWidget(main_widget)

        # Добавляем статусную строку
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("Готово к поиску")
        self.statusBar.addWidget(self.status_label)

        # Индикатор прогресса
        self.progress_label = QLabel()
        self.statusBar.addPermanentWidget(self.progress_label)
        self.progress_label.setVisible(False)

    def start_search(self, query_image_path, search_folder, extractor, similarity_threshold, max_results):
        """
        Запуск поиска похожих изображений.

        Args:
            query_image_path (str): Путь к изображению запроса
            search_folder (str): Путь к папке для поиска
            extractor (FeatureExtractor): Экстрактор признаков
            similarity_threshold (float): Порог сходства (0-1)
            max_results (int): Максимальное количество результатов
        """
        # Отключаем кнопки и показываем индикатор прогресса
        self.control_panel.set_search_in_progress(True)
        self.progress_label.setVisible(True)
        self.update_progress(0)

        # Очищаем предыдущие результаты
        self.last_results = []
        self.status_label.setText("Выполняется поиск...")

        # Проверяем, нужно ли использовать индекс
        use_index = self.control_panel.use_index_enabled()

        if use_index:
            # Проверяем наличие индекса
            index_dir = os.path.join(search_folder, ".index")
            if os.path.exists(index_dir):
                # Поиск индексов для текущего экстрактора
                extractor_name = extractor.name.replace(" ", "_").lower()
                index_path = os.path.join(index_dir, f"image_index_{extractor_name}.pkl")

                if os.path.exists(index_path):
                    # Если индекс существует, используем его для поиска
                    self.start_indexed_search(
                        query_image_path,
                        index_path,
                        extractor,
                        similarity_threshold,
                        max_results
                    )
                    return

        # Если индекс не используется или не найден, выполняем обычный поиск
        self.start_regular_search(
            query_image_path,
            search_folder,
            extractor,
            similarity_threshold,
            max_results
        )

    def start_regular_search(self, query_image_path, search_folder, extractor, similarity_threshold, max_results):
        """
        Запуск обычного поиска без использования индекса.

        Args:
            query_image_path (str): Путь к изображению запроса
            search_folder (str): Путь к папке для поиска
            extractor (FeatureExtractor): Экстрактор признаков
            similarity_threshold (float): Порог сходства (0-1)
            max_results (int): Максимальное количество результатов
        """
        # Создаем и запускаем рабочий поток
        self.search_worker = SearchWorker(
            query_image_path,
            search_folder,
            extractor,
            similarity_threshold,
            max_results
        )

        self.search_worker.progress_update.connect(self.update_progress)
        self.search_worker.result_ready.connect(self.display_results)
        self.search_worker.error_occurred.connect(self.show_error)
        self.search_worker.search_cancelled.connect(self.search_cancelled)
        self.search_worker.finished.connect(self.search_finished)

        self.search_worker.start()

    def start_indexed_search(self, query_image_path, index_path, extractor, similarity_threshold, max_results):
        """
        Запуск поиска с использованием индекса.

        Args:
            query_image_path (str): Путь к изображению запроса
            index_path (str): Путь к индексу
            extractor (FeatureExtractor): Экстрактор признаков
            similarity_threshold (float): Порог сходства (0-1)
            max_results (int): Максимальное количество результатов
        """
        # Создаем и запускаем поток для индексированного поиска
        self.indexed_search_worker = IndexedSearchWorker(
            query_image_path,
            index_path,
            extractor,
            similarity_threshold,
            max_results
        )

        # Подключаем сигналы
        self.indexed_search_worker.progress_update.connect(self.update_progress)
        self.indexed_search_worker.result_ready.connect(self.display_results)
        self.indexed_search_worker.error_occurred.connect(self.show_error)
        self.indexed_search_worker.finished.connect(self.search_finished)

        # Запускаем поток
        self.indexed_search_worker.start()

    def update_progress(self, value):
        """
        Обновление индикатора прогресса.

        Args:
            value (int): Значение прогресса (0-100)
        """
        self.progress_label.setText(f"Прогресс: {value}%")

    def display_results(self, results):
        """
        Отображение результатов поиска.

        Args:
            results (list): Список кортежей (путь к изображению, сходство)
        """
        # Сохраняем результаты для последующего использования
        self.last_results = results

        # Включаем кнопку просмотра результатов, если есть результаты
        self.control_panel.enable_save_results(len(results) > 0)

        # Обновляем статус
        if len(results) > 0:
            self.status_label.setText(f"Поиск завершен. Найдено {len(results)} изображений")
        else:
            self.status_label.setText("Поиск завершен. Похожие изображения не найдены")

        # Отображаем всплывающее окно с результатами
        if results:
            self.show_results_dialog(results)

    def show_results_dialog(self, results=None):
        """
        Показывает диалог с результатами поиска.

        Args:
            results (list, optional): Список результатов или None для использования последних результатов
        """
        if results is None:
            results = self.last_results

        if not results:
            QMessageBox.information(self, "Информация", "Нет результатов для отображения")
            return

        query_image_path = self.control_panel.query_image_path
        extractor_name = self.control_panel.get_current_extractor_name()
        similarity_threshold = self.control_panel.get_similarity_threshold()

        results_dialog = ResultsDialog(
            query_image_path,
            results,
            extractor_name,
            similarity_threshold,
            self
        )
        results_dialog.exec_()

    def show_last_results(self):
        """
        Показывает диалог с последними результатами поиска.
        """
        self.show_results_dialog()

    def show_error(self, message):
        """
        Отображение сообщения об ошибке.

        Args:
            message (str): Текст сообщения об ошибке
        """
        QMessageBox.critical(self, "Ошибка", message)
        self.status_label.setText(f"Ошибка: {message}")

    def search_cancelled(self):
        """
        Обработка отмены поиска.
        """
        self.status_label.setText("Поиск был отменен пользователем")

    def cancel_search(self):
        """
        Отмена текущего поиска.
        """
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()

        if self.indexed_search_worker and self.indexed_search_worker.isRunning():
            self.indexed_search_worker.terminate()
            self.search_finished()

    def search_finished(self):
        """
        Обработка завершения поиска.
        """
        # Включаем кнопки и скрываем индикатор прогресса
        self.control_panel.set_search_in_progress(False)
        self.progress_label.setVisible(False)

    def show_index_dialog(self, folder_path, extractor, output_path=None):
        """
        Отображение диалога индексации папки.

        Args:
            folder_path (str): Путь к папке для индексации
            extractor: Экстрактор признаков
            output_path (str, optional): Путь для сохранения индекса
        """
        dialog = IndexDialog(folder_path, extractor, output_path, self)
        dialog.index_completed.connect(self.handle_index_completed)
        dialog.exec_()

    def handle_index_completed(self, index_path):
        """
        Обработка завершения индексации.

        Args:
            index_path (str): Путь к созданному индексу
        """
        QMessageBox.information(
            self,
            "Индексация завершена",
            f"Индекс успешно создан и сохранен в:\n{index_path}"
        )
        self.status_label.setText(f"Индексация завершена: {os.path.basename(index_path)}")

    def closeEvent(self, event):
        """
        Обработка события закрытия окна.

        Args:
            event: Событие закрытия
        """
        # Останавливаем рабочие потоки, если они активны
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.stop()
            self.search_worker.wait()

        if self.index_worker and self.index_worker.isRunning():
            self.index_worker.stop()
            self.index_worker.wait()

        if self.indexed_search_worker and self.indexed_search_worker.isRunning():
            self.indexed_search_worker.terminate()
            self.indexed_search_worker.wait()

        event.accept()