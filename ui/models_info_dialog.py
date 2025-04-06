# -*- coding: utf-8 -*-
"""
Всплывающее диалоговое окно с информацией о различных моделях поиска изображений.
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTabWidget, QWidget, QScrollArea, QGridLayout, QSpacerItem,
                             QSizePolicy)
from PyQt5.QtGui import QPixmap, QIcon, QFont
from PyQt5.QtCore import Qt, QSize, QSettings


class ModelsInfoDialog(QDialog):
    """
    Диалоговое окно с информацией о моделях поиска изображений.
    Предоставляет сравнение, характеристики и рекомендации по использованию.
    """

    def __init__(self, parent=None):
        """
        Инициализация диалогового окна.

        Args:
            parent: Родительский виджет
        """
        super(ModelsInfoDialog, self).__init__(parent)

        self.settings = QSettings("ImageSearchApp", "ModelDialog")

        self.setWindowTitle("Сравнение моделей поиска изображений")
        self.setMinimumSize(800, 600)

        # Восстанавливаем размер и положение окна, если были сохранены
        if self.settings.contains("dialog_geometry"):
            self.restoreGeometry(self.settings.value("dialog_geometry"))
        else:
            # Устанавливаем окно по центру родительского окна
            if parent:
                self.setGeometry(
                    parent.x() + parent.width() // 2 - 400,
                    parent.y() + parent.height() // 2 - 300,
                    800, 600
                )

        # Создаем интерфейс
        self.init_ui()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        main_layout = QVBoxLayout(self)

        # Вкладки для разных представлений информации
        self.tab_widget = QTabWidget()

        # Вкладка сравнения
        self.comparison_tab = QWidget()
        self.init_comparison_tab()
        self.tab_widget.addTab(self.comparison_tab, "Сравнение моделей")

        # Вкладка деталей
        self.details_tab = QWidget()
        self.init_details_tab()
        self.tab_widget.addTab(self.details_tab, "Подробные характеристики")

        # Вкладка рекомендаций
        self.recommendations_tab = QWidget()
        self.init_recommendations_tab()
        self.tab_widget.addTab(self.recommendations_tab, "Рекомендации по выбору")

        main_layout.addWidget(self.tab_widget)

        # Кнопки
        buttons_layout = QHBoxLayout()

        # Растягивающий элемент для выравнивания кнопок по правому краю
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout.addItem(spacer)

        self.close_button = QPushButton("Закрыть")
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)

    def init_comparison_tab(self):
        """
        Инициализация вкладки общего сравнения моделей.
        """
        layout = QVBoxLayout(self.comparison_tab)

        # Заголовок
        title_label = QLabel("Сравнение методов поиска изображений")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Область прокрутки для инфографики
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Инфографика сравнения
        info_image_label = QLabel()
        info_image_path = os.path.join("ui", "resources", "models_comparison.svg")

        if os.path.exists(info_image_path):
            pixmap = QPixmap(info_image_path)
            info_image_label.setPixmap(pixmap)
            info_image_label.setAlignment(Qt.AlignCenter)
        else:
            info_image_label.setText("Изображение сравнения моделей не найдено")
            info_image_label.setAlignment(Qt.AlignCenter)

        scroll_layout.addWidget(info_image_label)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def init_details_tab(self):
        """
        Инициализация вкладки подробных характеристик моделей.
        """
        layout = QVBoxLayout(self.details_tab)

        # Область прокрутки для таблицы
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Создаем таблицу характеристик
        grid_layout = QGridLayout()

        # Заголовки
        headers = ["Метод", "Использование", "Преимущества", "Недостатки"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setFont(QFont("Arial", 12, QFont.Bold))
            label.setAlignment(Qt.AlignCenter)
            grid_layout.addWidget(label, 0, col)

        # Данные моделей
            # Данные моделей
            models_data = [
                ("SIFT", "Поиск похожих объектов и форм",
                 "• Устойчив к изменению масштаба и поворота\n• Высокая точность распознавания объектов\n• Хорошо работает с частичным перекрытием",
                 "• Требует больше вычислительных ресурсов\n• Медленнее, чем базовые методы"),

                ("Цветовая гистограмма", "Поиск изображений с похожей цветовой гаммой",
                 "• Очень быстрый\n• Нечувствителен к содержимому\n• Хорошо находит похожие сцены/пейзажи",
                 "• Не учитывает форму и структуру\n• Может давать ложные срабатывания"),

                ("CNN (ResNet50)", "Поиск изображений, основанный на глубоком обучении",
                 "• Высокая точность распознавания содержимого\n• Устойчивость к изменениям освещения и ракурса\n• Может распознавать абстрактные характеристики",
                 "• Требует значительных вычислительных ресурсов\n• Нуждается в GPU для быстрой работы\n• Зависит от обучающих данных"),

                ("DeepFace", "Поиск лиц и распознавание людей",
                 "• Высокая точность распознавания лиц\n• Устойчивость к ракурсу и освещению\n• Современный метод на основе нейросетей",
                 "• Требует дополнительной установки\n• Медленнее других методов\n• Работает только с лицами")
            ]

        for row, (model, usage, pros, cons) in enumerate(models_data, 1):
            # Название модели
            model_label = QLabel(model)
            model_label.setFont(QFont("Arial", 11, QFont.Bold))
            grid_layout.addWidget(model_label, row, 0)

            # Использование
            usage_label = QLabel(usage)
            usage_label.setWordWrap(True)
            grid_layout.addWidget(usage_label, row, 1)

            # Преимущества
            pros_label = QLabel(pros)
            pros_label.setStyleSheet("color: #10b981;")
            grid_layout.addWidget(pros_label, row, 2)

            # Недостатки
            cons_label = QLabel(cons)
            cons_label.setStyleSheet("color: #ef4444;")
            grid_layout.addWidget(cons_label, row, 3)

        # Настраиваем одинаковые размеры колонок
        for col in range(4):
            grid_layout.setColumnStretch(col, 1)

        scroll_layout.addLayout(grid_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def init_recommendations_tab(self):
        """
        Инициализация вкладки рекомендаций по выбору моделей.
        """
        layout = QVBoxLayout(self.recommendations_tab)

        # Область прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Заголовок
        title_label = QLabel("Рекомендации по выбору модели")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(title_label)

        # Рекомендации
        recommendations = [
            ("<b>Для поиска похожих фотографий людей:</b> DeepFace",
             "Используйте модель DeepFace, если вам нужно искать лица людей. Она обеспечивает высокую точность распознавания даже при разном освещении, выражении лица и небольших поворотах. Обратите внимание, что для работы требуется установка дополнительных библиотек."),

            ("<b>Для поиска похожих объектов независимо от их размера или поворота:</b> SIFT",
             "Модель SIFT отлично подходит для поиска конкретных объектов или логотипов. Она устойчива к изменениям масштаба, вращению и частичному перекрытию. Идеально для каталогизации товаров, логотипов компаний или архитектурных элементов."),

            ("<b>Для глубокого анализа содержимого изображений:</b> CNN (ResNet50)",
             "Модель ResNet50 обеспечивает наиболее точный анализ содержимого изображений благодаря использованию глубоких нейронных сетей. Она способна распознавать сложные визуальные концепции, понимать что именно изображено на картинке, и находить похожие изображения даже при значительных различиях в деталях."),

            ("<b>Для поиска изображений с похожей цветовой схемой:</b> Цветовая гистограмма",
             "Для поиска изображений с похожей цветовой палитрой (например, закаты, пейзажи, морские виды) лучше всего подходит модель цветовой гистограммы. Она очень быстрая и эффективно сравнивает общую цветовую композицию, не обращая внимания на конкретные объекты.")
        ]

        for i, (title, description) in enumerate(recommendations):
            # Заголовок рекомендации
            rec_title = QLabel(title)
            rec_title.setFont(QFont("Arial", 11))
            scroll_layout.addWidget(rec_title)

            # Описание
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setContentsMargins(20, 0, 0, 20)
            scroll_layout.addWidget(desc_label)

        # Технические особенности
        tech_title = QLabel("<b>Технические особенности</b>")
        tech_title.setFont(QFont("Arial", 12, QFont.Bold))
        scroll_layout.addWidget(tech_title)

        tech_details = QLabel(
            "• <b>SIFT</b> (Scale-Invariant Feature Transform) - выделяет особые точки и их "
            "дескрипторы, инвариантные к масштабированию, вращению и изменению освещения.<br><br>"
            "• <b>Цветовая гистограмма</b> - вычисляет распределение цветов в пространстве HSV, "
            "эффективно сравнивая общую цветовую композицию изображений.<br><br>"
            "• <b>CNN (ResNet50)</b> - глубокая сверточная нейронная сеть, состоящая из 50 слоев. "
            "Использует остаточные связи для решения проблемы исчезающих градиентов, что позволяет "
            "эффективно извлекать высокоуровневые признаки из изображений.<br><br>"
            "• <b>DeepFace</b> - использует глубокие нейронные сети для извлечения высокоуровневых "
            "признаков лиц, что обеспечивает высокую точность распознавания."
        )
        tech_details.setWordWrap(True)
        tech_details.setContentsMargins(20, 0, 0, 0)
        scroll_layout.addWidget(tech_details)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def closeEvent(self, event):
        """
        Обрабатывает событие закрытия диалога, сохраняя его геометрию.

        Args:
            event: Событие закрытия
        """
        self.settings.setValue("dialog_geometry", self.saveGeometry())
        event.accept()