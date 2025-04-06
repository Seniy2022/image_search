# -*- coding: utf-8 -*-
"""
Панель результатов поиска изображений.
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel,
                             QGroupBox, QScrollArea, QProgressBar,
                             QHBoxLayout, QSizePolicy, QFrame)
from PyQt5.QtCore import Qt

from utils.image_utils import load_image_pixmap


class ResultsPanel(QWidget):
    """
    Панель для отображения результатов поиска изображений.
    """

    def __init__(self, parent=None):
        """
        Инициализация панели результатов.

        Args:
            parent: Родительский виджет
        """
        super(ResultsPanel, self).__init__(parent)

        # Результаты поиска
        self.search_results = []

        # Создание UI
        self.init_ui()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        # Установка имени объекта для применения стилей
        self.setObjectName("results_panel")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Уменьшаем отступы для увеличения полезной площади

        # Панель заголовка
        header_layout = QHBoxLayout()

        # Заголовок
        results_label = QLabel("Результаты поиска")
        results_label.setObjectName("results_title")
        header_layout.addWidget(results_label)

        # Растягивающийся элемент для выравнивания
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header_layout.addWidget(spacer)

        # Индикатор прогресса
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)  # Фиксированная ширина
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)

        main_layout.addLayout(header_layout)

        # Разделительная линия
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        # Область прокрутки для результатов
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.results_container = QWidget()
        self.results_layout = QGridLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы для максимальной области отображения
        self.results_layout.setSpacing(10)  # Увеличиваем расстояние между миниатюрами

        self.scroll_area.setWidget(self.results_container)
        main_layout.addWidget(self.scroll_area)

        # Добавляем пустое сообщение
        self.no_results_label = QLabel("Здесь будут отображены результаты поиска")
        self.no_results_label.setAlignment(Qt.AlignCenter)
        self.results_layout.addWidget(self.no_results_label, 0, 0)

    def clear_results(self):
        """
        Очистка области результатов.
        """
        # Удаляем все виджеты из макета результатов
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def set_search_results(self, results):
        """
        Установка и отображение результатов поиска.

        Args:
            results (list): Список кортежей (путь к изображению, сходство)
        """
        self.search_results = results

        # Очищаем макет результатов
        self.clear_results()

        if not results:
            # Добавляем сообщение о том, что результаты не найдены
            no_results_label = QLabel("Похожие изображения не найдены")
            no_results_label.setAlignment(Qt.AlignCenter)
            self.results_layout.addWidget(no_results_label, 0, 0)
            return

        # Добавляем результаты в сетку
        row, col = 0, 0
        max_cols = 4  # Количество столбцов в сетке

        for i, (img_path, similarity) in enumerate(results):
            # Создаем группу для изображения и информации
            result_group = QGroupBox()
            result_group.setObjectName("result_group")
            result_layout = QVBoxLayout(result_group)
            result_layout.setContentsMargins(8, 8, 8, 8)  # Уменьшаем внутренние отступы

            # Загружаем и отображаем миниатюру с увеличенным размером
            pixmap = load_image_pixmap(img_path, 300, 300)  # Увеличиваем размер миниатюры
            if pixmap:
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setMinimumSize(250, 200)  # Устанавливаем минимальный размер для миниатюры
                result_layout.addWidget(img_label)

                # Добавляем метку с информацией
                info_label = QLabel(f"Сходство: {similarity:.2f}")
                info_label.setAlignment(Qt.AlignCenter)
                result_layout.addWidget(info_label)

                # Добавляем название файла
                filename_label = QLabel(os.path.basename(img_path))
                filename_label.setAlignment(Qt.AlignCenter)
                filename_label.setWordWrap(True)
                result_layout.addWidget(filename_label)

                # Добавляем группу в сетку
                self.results_layout.addWidget(result_group, row, col)

                # Переходим к следующей ячейке сетки
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def set_progress(self, value):
        """
        Установка значения прогресса поиска.

        Args:
            value (int): Значение прогресса (0-100)
        """
        self.progress_bar.setValue(value)

    def set_progress_visible(self, visible):
        """
        Установка видимости индикатора прогресса.

        Args:
            visible (bool): True для отображения, False для скрытия
        """
        self.progress_bar.setVisible(visible)

    def get_search_results(self):
        """
        Получение результатов поиска.

        Returns:
            list: Список кортежей (путь к изображению, сходство)
        """
        return self.search_results

    def show_cancelled_message(self):
        """
        Отображает сообщение о том, что поиск был отменен пользователем.
        """
        # Очищаем панель результатов
        self.clear_results()

        # Добавляем сообщение об отмене
        cancelled_label = QLabel("Поиск был отменен пользователем")
        cancelled_label.setAlignment(Qt.AlignCenter)
        cancelled_label.setStyleSheet("color: var(--error-color); font-size: 14px; margin: 20px;")
        self.results_layout.addWidget(cancelled_label, 0, 0)