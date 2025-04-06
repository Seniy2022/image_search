# -*- coding: utf-8 -*-
"""
Диалоговое окно для отображения результатов поиска изображений.
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QGridLayout, QGroupBox, QPushButton,
                             QFileDialog, QMessageBox, QSplitter, QFrame,
                             QWidget, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon

from utils.image_utils import load_image_pixmap
from utils.file_utils import create_results_folder, save_search_results


class ResultsDialog(QDialog):
    """
    Диалоговое окно для отображения и сохранения результатов поиска.
    """

    def __init__(self, query_image_path, results, extractor_name, similarity_threshold, parent=None):
        """
        Инициализация диалогового окна.

        Args:
            query_image_path (str): Путь к изображению запроса
            results (list): Список кортежей (путь к изображению, сходство)
            extractor_name (str): Название использованного экстрактора
            similarity_threshold (float): Порог сходства
            parent: Родительский виджет
        """
        super(ResultsDialog, self).__init__(parent)

        self.query_image_path = query_image_path
        self.results = results
        self.extractor_name = extractor_name
        self.similarity_threshold = similarity_threshold
        self.results_folder = None

        # Устанавливаем заголовок и размер
        self.setWindowTitle("Результаты поиска изображений")
        self.resize(1200, 800)  # Увеличиваем размер диалога

        # Инициализируем интерфейс
        self.init_ui()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Верхняя панель с информацией о запросе
        top_panel = QWidget()
        top_layout = QHBoxLayout(top_panel)

        # Изображение запроса
        query_group = QGroupBox("Изображение запроса")
        query_layout = QVBoxLayout(query_group)

        query_image_label = QLabel()
        query_pixmap = load_image_pixmap(self.query_image_path, 250, 250)  # Увеличиваем размер
        if query_pixmap:
            query_image_label.setPixmap(query_pixmap)
        else:
            query_image_label.setText("Не удалось загрузить изображение")
        query_image_label.setAlignment(Qt.AlignCenter)
        query_layout.addWidget(query_image_label)

        # Добавляем имя файла запроса
        query_filename = os.path.basename(self.query_image_path)
        query_filename_label = QLabel(query_filename)
        query_filename_label.setAlignment(Qt.AlignCenter)
        query_filename_label.setWordWrap(True)
        query_layout.addWidget(query_filename_label)

        top_layout.addWidget(query_group)

        # Информация о запросе
        info_group = QGroupBox("Информация о поиске")
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel(
            f"<b>Модель:</b> {self.extractor_name}<br>"
            f"<b>Порог сходства:</b> {self.similarity_threshold:.2f}<br>"
            f"<b>Найдено результатов:</b> {len(self.results)}<br>"
        )
        info_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(info_label)

        # Кнопки для сохранения
        save_buttons_layout = QHBoxLayout()

        self.select_folder_btn = QPushButton("Выбрать папку для сохранения")
        self.select_folder_btn.clicked.connect(self.select_results_folder)
        save_buttons_layout.addWidget(self.select_folder_btn)

        self.save_results_btn = QPushButton("Сохранить результаты")
        self.save_results_btn.clicked.connect(self.save_results)
        save_buttons_layout.addWidget(self.save_results_btn)

        info_layout.addLayout(save_buttons_layout)

        # Статус сохранения
        self.status_label = QLabel()
        info_layout.addWidget(self.status_label)

        top_layout.addWidget(info_group)
        top_layout.setStretch(0, 1)  # Изображение занимает меньше места
        top_layout.setStretch(1, 2)  # Информация занимает больше места

        main_layout.addWidget(top_panel)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Основная область с результатами
        results_label = QLabel("Найденные изображения:")
        results_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(results_label)

        # Область прокрутки для результатов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        results_container = QWidget()
        self.results_layout = QGridLayout(results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)  # Увеличиваем расстояние между изображениями

        # Добавляем результаты в сетку
        if self.results:
            self.display_results()
        else:
            no_results_label = QLabel("Похожие изображения не найдены")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(no_results_label, 0, 0)

        scroll_area.setWidget(results_container)
        main_layout.addWidget(scroll_area)

        # Нижняя панель с кнопками
        bottom_layout = QHBoxLayout()

        # Растягивающийся элемент
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bottom_layout.addWidget(spacer)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(close_button)

        main_layout.addLayout(bottom_layout)

        # Соотношение частей: верхняя панель занимает меньше места
        main_layout.setStretch(0, 1)  # Верхняя панель
        main_layout.setStretch(3, 5)  # Область с результатами

    def display_results(self):
        """
        Отображение найденных изображений в сетке.
        """
        row, col = 0, 0
        max_cols = 3  # Уменьшаем количество столбцов для увеличения размера изображений

        for i, (img_path, similarity) in enumerate(self.results):
            # Создаем группу для изображения и информации
            result_group = QGroupBox()
            result_group.setObjectName("result_group")
            result_layout = QVBoxLayout(result_group)
            result_layout.setContentsMargins(10, 10, 10, 10)  # Увеличиваем отступы

            # Загружаем и отображаем миниатюру с увеличенным размером
            pixmap = load_image_pixmap(img_path, 400, 400)  # Значительно увеличиваем размер
            if pixmap:
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setMinimumSize(350, 300)  # Увеличиваем минимальный размер
                result_layout.addWidget(img_label)

                # Добавляем метку с информацией
                info_label = QLabel(f"Сходство: {similarity:.2f}")
                info_label.setAlignment(Qt.AlignCenter)
                info_label.setStyleSheet("font-size: 12pt;")  # Увеличиваем размер шрифта
                result_layout.addWidget(info_label)

                # Добавляем название файла
                filename_label = QLabel(os.path.basename(img_path))
                filename_label.setAlignment(Qt.AlignCenter)
                filename_label.setWordWrap(True)
                filename_label.setStyleSheet("font-size: 10pt;")  # Увеличиваем размер шрифта
                result_layout.addWidget(filename_label)

                # Добавляем группу в сетку
                self.results_layout.addWidget(result_group, row, col)

                # Переходим к следующей ячейке сетки
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def select_results_folder(self):
        """
        Выбор папки для сохранения результатов.
        """
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения результатов"
        )

        if folder_path:
            self.results_folder = folder_path
            self.select_folder_btn.setText(f"Папка: {os.path.basename(folder_path)}")
            self.status_label.setText(f"Выбрана папка: {folder_path}")
            self.status_label.setStyleSheet("color: green;")

    def save_results(self):
        """
        Сохранение результатов в указанную папку.
        """
        if not self.results:
            QMessageBox.warning(self, "Предупреждение", "Нет результатов для сохранения")
            return

        if not self.results_folder:
            self.select_results_folder()
            if not self.results_folder:  # Если пользователь отменил выбор
                return

        try:
            # Получаем имя запроса
            query_name = os.path.splitext(os.path.basename(self.query_image_path))[0]

            # Создаем папку для результатов
            result_dir = create_results_folder(self.results_folder, query_name)

            # Сохраняем результаты
            success = save_search_results(
                self.query_image_path,
                self.results,
                result_dir,
                self.extractor_name,
                self.similarity_threshold
            )

            if success:
                self.status_label.setText(f"Результаты сохранены в папку: {result_dir}")
                self.status_label.setStyleSheet("color: green;")

                QMessageBox.information(
                    self,
                    "Успешно",
                    f"Результаты сохранены в папку:\n{result_dir}"
                )
            else:
                self.status_label.setText("Ошибка при сохранении результатов")
                self.status_label.setStyleSheet("color: red;")

        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
            self.status_label.setStyleSheet("color: red;")

            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка при сохранении результатов: {str(e)}"
            )