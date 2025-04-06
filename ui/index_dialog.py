# -*- coding: utf-8 -*-
"""
Диалоговое окно для индексации папки с изображениями.
"""

import os
import re
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QComboBox, QFormLayout,
                             QRadioButton, QGroupBox, QButtonGroup, QListWidget,
                             QTabWidget, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

from feature_extractors import AVAILABLE_EXTRACTORS
from workers.index_worker import IndexWorker


class IndexDialog(QDialog):
    """
    Диалоговое окно для индексации папки с изображениями.

    Signals:
        index_completed (str): Сигнал успешного завершения индексации
        index_progress (int): Сигнал прогресса индексации
    """
    index_completed = pyqtSignal(str)
    index_progress = pyqtSignal(int)

    def __init__(self, folder_path, extractor, output_path=None, parent=None):
        """
        Инициализация диалогового окна.

        Args:
            folder_path (str): Путь к папке с изображениями
            extractor: Экстрактор признаков по умолчанию
            output_path (str, optional): Путь для сохранения индекса
            parent: Родительский виджет
        """
        super(IndexDialog, self).__init__(parent)

        self.folder_path = folder_path
        self.extractor = extractor
        self.output_path = output_path
        self.index_worker = None
        self.existing_indexes = []

        # Устанавливаем заголовок и размер
        self.setWindowTitle("Индексация папки с изображениями")
        self.resize(600, 400)
        self.setModal(True)

        # Находим существующие индексы
        self.find_existing_indexes()

        # Инициализируем интерфейс
        self.init_ui()

    def find_existing_indexes(self):
        """
        Поиск существующих индексов в папке.
        """
        index_dir = os.path.join(self.folder_path, ".index")
        if not os.path.exists(index_dir):
            return

        # Ищем файлы индексов
        index_files = [f for f in os.listdir(index_dir) if f.startswith("image_index_") and f.endswith(".pkl")]

        # Извлекаем информацию о моделях из имен файлов
        for index_file in index_files:
            index_path = os.path.join(index_dir, index_file)

            # Извлекаем имя модели из имени файла
            match = re.search(r"image_index_(.+)\.pkl", index_file)
            if match:
                model_name = match.group(1).replace("_", " ")

                # Находим соответствующий экстрактор
                matching_extractor = None
                for ext in AVAILABLE_EXTRACTORS:
                    if ext.name.lower().replace(" ", "_") == model_name.lower().replace(" ", "_"):
                        matching_extractor = ext
                        break

                if matching_extractor:
                    # Если найден соответствующий экстрактор, добавляем в список
                    self.existing_indexes.append({
                        'path': index_path,
                        'name': model_name,
                        'extractor': matching_extractor,
                        'file': index_file
                    })

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        main_layout = QVBoxLayout(self)

        # Информация о папке
        folder_info = QLabel(f"Папка: {self.folder_path}")
        folder_info.setWordWrap(True)
        main_layout.addWidget(folder_info)

        # Вкладки для разных режимов
        tab_widget = QTabWidget()

        # Вкладка создания нового индекса
        new_index_tab = QWidget()
        self.init_new_index_tab(new_index_tab)
        tab_widget.addTab(new_index_tab, "Создать новый индекс")

        # Вкладка с существующими индексами
        if self.existing_indexes:
            existing_index_tab = QWidget()
            self.init_existing_index_tab(existing_index_tab)
            tab_widget.addTab(existing_index_tab, "Использовать существующий индекс")

        main_layout.addWidget(tab_widget)

        # Индикатор прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Статусная строка
        self.status_label = QLabel("Готово к индексации")
        main_layout.addWidget(self.status_label)

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        buttons_layout.addStretch()

        self.start_button = QPushButton("Начать индексацию")
        self.start_button.clicked.connect(self.start_indexing)
        buttons_layout.addWidget(self.start_button)

        main_layout.addLayout(buttons_layout)

    def init_new_index_tab(self, tab_widget):
        """
        Инициализация вкладки создания нового индекса.

        Args:
            tab_widget: Виджет вкладки
        """
        layout = QVBoxLayout(tab_widget)

        # Форма с настройками
        form_layout = QFormLayout()

        # Выбор экстрактора признаков
        self.extractor_combo = QComboBox()
        for ext in AVAILABLE_EXTRACTORS:
            self.extractor_combo.addItem(ext.name)

        # Устанавливаем текущий экстрактор
        for i, ext in enumerate(AVAILABLE_EXTRACTORS):
            if ext.name == self.extractor.name:
                self.extractor_combo.setCurrentIndex(i)
                break

        # Добавляем информацию о том, какие модели уже проиндексированы
        if self.existing_indexes:
            existing_models = [index['name'] for index in self.existing_indexes]
            existing_info = QLabel(f"<i>Уже проиндексированы: {', '.join(existing_models)}</i>")
            existing_info.setStyleSheet("color: gray;")
            layout.addWidget(existing_info)

        form_layout.addRow("Экстрактор признаков:", self.extractor_combo)
        layout.addLayout(form_layout)

        # Добавляем описание
        description = QLabel("Создание нового индекса ускорит повторные поиски с выбранной моделью. "
                             "Этот процесс может занять некоторое время в зависимости от количества изображений в папке.")
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addStretch()

    def init_existing_index_tab(self, tab_widget):
        """
        Инициализация вкладки с существующими индексами.

        Args:
            tab_widget: Виджет вкладки
        """
        layout = QVBoxLayout(tab_widget)

        # Список существующих индексов
        self.index_list = QListWidget()

        # Заполняем список
        for index in self.existing_indexes:
            self.index_list.addItem(f"{index['name']} ({os.path.basename(index['path'])})")

        # Выбираем первый элемент
        if self.index_list.count() > 0:
            self.index_list.setCurrentRow(0)

        layout.addWidget(QLabel("Выберите существующий индекс:"))
        layout.addWidget(self.index_list)

        # Добавляем описание
        description = QLabel(
            "Вы можете использовать уже созданный индекс или создать новый на вкладке 'Создать новый индекс'.")
        description.setWordWrap(True)
        layout.addWidget(description)

        # Опции
        options_group = QGroupBox("Опции")
        options_layout = QVBoxLayout(options_group)

        self.update_existing_radio = QRadioButton("Обновить выбранный индекс (добавить новые изображения)")
        self.recreate_radio = QRadioButton("Пересоздать индекс (полная переиндексация)")

        self.update_existing_radio.setChecked(True)

        options_layout.addWidget(self.update_existing_radio)
        options_layout.addWidget(self.recreate_radio)

        layout.addWidget(options_group)
        layout.addStretch()

    def start_indexing(self):
        """
        Запуск процесса индексации.
        """
        # Проверяем, на какой вкладке находимся
        tab_index = self.findChild(QTabWidget).currentIndex()

        if tab_index == 0 or not self.existing_indexes:
            # Создание нового индекса
            selected_extractor = AVAILABLE_EXTRACTORS[self.extractor_combo.currentIndex()]

            # Создаем путь для сохранения индекса, если не указан
            if not self.output_path:
                extractor_name = selected_extractor.name.replace(" ", "_").lower()
                index_dir = os.path.join(self.folder_path, ".index")
                os.makedirs(index_dir, exist_ok=True)
                self.output_path = os.path.join(index_dir, f"image_index_{extractor_name}.pkl")

        else:
            # Использование существующего индекса
            selected_index = self.existing_indexes[self.index_list.currentRow()]
            selected_extractor = selected_index['extractor']
            self.output_path = selected_index['path']

            # Проверяем, нужно ли пересоздать индекс
            if self.recreate_radio.isChecked():
                # Предупреждаем пользователя о пересоздании
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    f"Вы действительно хотите пересоздать индекс '{selected_index['name']}'?\n"
                    "Это удалит существующий индекс и создаст новый.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.No:
                    return

        # Обновляем статус
        self.status_label.setText("Начинаем индексацию...")
        self.start_button.setEnabled(False)
        if hasattr(self, 'extractor_combo'):
            self.extractor_combo.setEnabled(False)
        if hasattr(self, 'index_list'):
            self.index_list.setEnabled(False)
        if hasattr(self, 'update_existing_radio'):
            self.update_existing_radio.setEnabled(False)
        if hasattr(self, 'recreate_radio'):
            self.recreate_radio.setEnabled(False)

        self.cancel_button.setText("Остановить индексацию")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.stop_indexing)

        # Создаем и запускаем рабочий поток
        self.index_worker = IndexWorker(
            self.folder_path,
            selected_extractor,
            self.output_path
        )

        # Подключаем сигналы
        self.index_worker.progress_update.connect(self.update_progress)
        self.index_worker.index_completed.connect(self.handle_index_completed)
        self.index_worker.index_failed.connect(self.handle_index_failed)
        self.index_worker.index_cancelled.connect(self.handle_index_cancelled)

        # Запускаем поток
        self.index_worker.start()

    def stop_indexing(self):
        """
        Остановка процесса индексации.
        """
        if self.index_worker and self.index_worker.isRunning():
            self.status_label.setText("Останавливаем индексацию...")
            self.cancel_button.setEnabled(False)
            self.index_worker.stop()

    def update_progress(self, value):
        """
        Обновление индикатора прогресса.

        Args:
            value (int): Значение прогресса (0-100)
        """
        self.progress_bar.setValue(value)
        self.index_progress.emit(value)

    def handle_index_completed(self, index_path):
        """
        Обработка успешного завершения индексации.

        Args:
            index_path (str): Путь к созданному индексу
        """
        self.status_label.setText(f"Индексация завершена. Индекс сохранен в: {index_path}")
        self.progress_bar.setValue(100)
        self.cancel_button.setText("Закрыть")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.accept)
        self.index_completed.emit(index_path)

    def handle_index_failed(self, error_message):
        """
        Обработка ошибки индексации.

        Args:
            error_message (str): Сообщение об ошибке
        """
        self.status_label.setText(f"Ошибка индексации: {error_message}")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(True)
        if hasattr(self, 'extractor_combo'):
            self.extractor_combo.setEnabled(True)
        if hasattr(self, 'index_list'):
            self.index_list.setEnabled(True)
        if hasattr(self, 'update_existing_radio'):
            self.update_existing_radio.setEnabled(True)
        if hasattr(self, 'recreate_radio'):
            self.recreate_radio.setEnabled(True)
        self.cancel_button.setText("Закрыть")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.reject)

    def handle_index_cancelled(self):
        """
        Обработка отмены индексации.
        """
        self.status_label.setText("Индексация была отменена")
        self.progress_bar.setValue(0)
        self.start_button.setEnabled(True)
        if hasattr(self, 'extractor_combo'):
            self.extractor_combo.setEnabled(True)
        if hasattr(self, 'index_list'):
            self.index_list.setEnabled(True)
        if hasattr(self, 'update_existing_radio'):
            self.update_existing_radio.setEnabled(True)
        if hasattr(self, 'recreate_radio'):
            self.recreate_radio.setEnabled(True)
        self.cancel_button.setText("Закрыть")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.reject)

    def closeEvent(self, event):
        """
        Обработка события закрытия диалога.

        Args:
            event: Событие закрытия
        """
        # Останавливаем рабочий поток, если он активен
        if self.index_worker and self.index_worker.isRunning():
            self.index_worker.stop()
            self.index_worker.wait()

        event.accept()