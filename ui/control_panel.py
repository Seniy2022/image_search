# -*- coding: utf-8 -*-
"""
Панель управления приложением поиска изображений.
"""

import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QLabel, QPushButton, QComboBox, QSlider, QSpinBox, QFileDialog,
                             QDoubleSpinBox, QCheckBox, QApplication, QStyle, QToolButton,
                             QMenu)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon

from feature_extractors import AVAILABLE_EXTRACTORS
from ui.models_info_dialog import ModelsInfoDialog
from ui.drag_drop_support import DragDropMixin


class ControlPanel(QWidget, DragDropMixin):
    """
    Панель управления с настройками поиска.

    Signals:
        search_requested: Сигнал запроса поиска с параметрами
        save_results_requested: Сигнал запроса сохранения результатов
        cancel_search_requested: Сигнал запроса отмены поиска
        index_folder_requested: Сигнал запроса индексации папки
    """
    search_requested = pyqtSignal(str, str, object, float, int)
    save_results_requested = pyqtSignal()
    cancel_search_requested = pyqtSignal()
    index_folder_requested = pyqtSignal(str, object, str)

    def __init__(self, parent=None):
        """
        Инициализация панели управления.

        Args:
            parent: Родительский виджет
        """
        super(ControlPanel, self).__init__(parent)

        # Инициализация переменных
        self.query_image_path = None
        self.search_folder = None
        self.results_folder = None
        self.indexed_folders = []  # Список проиндексированных папок

        # Создание UI
        self.init_ui()

        # Настройка поддержки перетаскивания
        self.setup_drag_drop()

    def init_ui(self):
        """
        Инициализация пользовательского интерфейса.
        """
        main_layout = QVBoxLayout(self)

        # Группа настроек изображения
        image_group = QGroupBox("Изображение для поиска")
        image_layout = QHBoxLayout()

        # Левая часть - предпросмотр изображения
        self.preview_label = QLabel("Перетащите сюда изображение\nили нажмите кнопку загрузки")
        self.preview_label.setObjectName("preview_label")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 200)
        image_layout.addWidget(self.preview_label)

        # Правая часть - кнопки выбора
        image_buttons_layout = QVBoxLayout()

        self.load_image_btn = QPushButton("Загрузить изображение")
        self.load_image_btn.clicked.connect(self.load_query_image)
        image_buttons_layout.addWidget(self.load_image_btn)

        self.select_folder_btn = QPushButton("Выбрать папку с изображениями")
        self.select_folder_btn.clicked.connect(self.select_search_folder)
        image_buttons_layout.addWidget(self.select_folder_btn)

        # Новая кнопка для индексации папки
        self.index_folder_btn = QPushButton("Индексировать папку")
        self.index_folder_btn.clicked.connect(self.index_folder)
        image_buttons_layout.addWidget(self.index_folder_btn)

        self.select_output_btn = QPushButton("Выбрать папку для сохранения результатов")
        self.select_output_btn.clicked.connect(self.select_results_folder)
        image_buttons_layout.addWidget(self.select_output_btn)

        image_layout.addLayout(image_buttons_layout)
        image_group.setLayout(image_layout)
        main_layout.addWidget(image_group)

        # Группа настроек поиска
        search_group = QGroupBox("Настройки поиска")
        search_layout = QFormLayout()

        # Выбор модели экстрактора
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        for extractor in AVAILABLE_EXTRACTORS:
            self.model_combo.addItem(extractor.name)

        # Добавляем кнопку информации о моделях
        self.model_info_btn = QToolButton()
        self.model_info_btn.setIcon(QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))
        self.model_info_btn.setToolTip("Информация о методах поиска")
        self.model_info_btn.clicked.connect(self.show_models_info)
        self.model_info_btn.setFixedSize(28, 28)

        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(self.model_info_btn)

        search_layout.addRow("Модель для дескрипторов:", model_layout)

        # Ползунок коэффициента похожести
        similarity_layout = QHBoxLayout()
        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setMinimum(0)
        self.similarity_slider.setMaximum(100)
        self.similarity_slider.setValue(70)  # По умолчанию 0.7
        self.similarity_slider.setTickPosition(QSlider.TicksBelow)
        self.similarity_slider.setTickInterval(10)

        # Добавляем SpinBox для ввода с клавиатуры
        self.similarity_spinbox = QDoubleSpinBox()
        self.similarity_spinbox.setMinimum(0.0)
        self.similarity_spinbox.setMaximum(1.0)
        self.similarity_spinbox.setSingleStep(0.01)
        self.similarity_spinbox.setValue(0.7)
        self.similarity_spinbox.setDecimals(2)
        self.similarity_spinbox.setFixedWidth(80)

        # Синхронизируем ползунок и спинбокс
        self.similarity_slider.valueChanged.connect(self.slider_value_changed)
        self.similarity_spinbox.valueChanged.connect(self.spinbox_value_changed)

        similarity_layout.addWidget(self.similarity_slider)
        similarity_layout.addWidget(self.similarity_spinbox)
        search_layout.addRow("Коэффициент похожести:", similarity_layout)

        # Выбор максимального количества результатов
        results_layout = QHBoxLayout()

        self.results_spinbox = QSpinBox()
        self.results_spinbox.setMinimum(0)
        self.results_spinbox.setMaximum(1000)
        self.results_spinbox.setValue(20)
        self.results_spinbox.setSpecialValueText("Все")

        self.show_all_results_checkbox = QCheckBox("Показать все найденные результаты")
        self.show_all_results_checkbox.setChecked(True)
        self.show_all_results_checkbox.stateChanged.connect(self.toggle_show_all_results)

        results_layout.addWidget(self.results_spinbox)
        results_layout.addWidget(self.show_all_results_checkbox)
        search_layout.addRow("Количество результатов:", results_layout)

        # Флажок для использования индекса
        self.use_index_checkbox = QCheckBox("Использовать индекс (если доступен)")
        self.use_index_checkbox.setChecked(True)
        search_layout.addRow("Опции поиска:", self.use_index_checkbox)

        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.search_btn = QPushButton("Найти похожие изображения")
        self.search_btn.clicked.connect(self.start_search)
        buttons_layout.addWidget(self.search_btn)

        self.cancel_search_btn = QPushButton("Отменить поиск")
        self.cancel_search_btn.clicked.connect(self.cancel_search)
        self.cancel_search_btn.setVisible(False)  # Изначально скрыта
        buttons_layout.addWidget(self.cancel_search_btn)

        self.save_results_btn = QPushButton("Показать результаты")
        self.save_results_btn.clicked.connect(self.save_results)
        self.save_results_btn.setEnabled(False)
        buttons_layout.addWidget(self.save_results_btn)

        main_layout.addLayout(buttons_layout)

        # Индикатор прогресса
        progress_layout = QHBoxLayout()
        self.progress_bar_label = QLabel("Прогресс поиска:")
        self.progress_bar_label.setVisible(False)
        progress_layout.addWidget(self.progress_bar_label)

        # Дополнительный статус для отмены
        self.status_label = QLabel("")
        progress_layout.addWidget(self.status_label, 1)  # 1 - чтобы растягивалась

        main_layout.addLayout(progress_layout)

    def handle_image_drop(self, file_path):
        """
        Обработка события сброса перетаскиваемого изображения.

        Args:
            file_path (str): Путь к изображению
        """
        self.query_image_path = file_path

        # Отображаем предпросмотр
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(pixmap)

            # Обновляем статус
            self.status_label.setText(f"Загружено изображение: {os.path.basename(file_path)}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.preview_label.setText("Не удалось загрузить изображение")
            self.status_label.setText("Ошибка загрузки изображения")
            self.status_label.setStyleSheet("color: red;")

    def slider_value_changed(self, value):
        """
        Обработчик изменения значения ползунка.
        Обновляет значение спинбокса.

        Args:
            value (int): Значение ползунка (0-100)
        """
        # Блокируем сигналы спинбокса во избежание рекурсии
        self.similarity_spinbox.blockSignals(True)
        self.similarity_spinbox.setValue(value / 100.0)
        self.similarity_spinbox.blockSignals(False)

    def spinbox_value_changed(self, value):
        """
        Обработчик изменения значения спинбокса.
        Обновляет значение ползунка.

        Args:
            value (float): Значение спинбокса (0.0-1.0)
        """
        # Блокируем сигналы ползунка во избежание рекурсии
        self.similarity_slider.blockSignals(True)
        self.similarity_slider.setValue(int(value * 100))
        self.similarity_slider.blockSignals(False)

    def toggle_show_all_results(self, state):
        """
        Обработчик изменения состояния флажка "Показать все результаты".

        Args:
            state (int): Состояние флажка (Qt.Checked или Qt.Unchecked)
        """
        if state == Qt.Checked:
            # Если выбрано "показать все", устанавливаем значение 0 (специальное значение "Все")
            self.results_spinbox.setValue(0)
            self.results_spinbox.setEnabled(False)
        else:
            # Если флажок снят, восстанавливаем предыдущее значение (или устанавливаем 20 по умолчанию)
            self.results_spinbox.setValue(20)
            self.results_spinbox.setEnabled(True)

    def update_similarity_label(self):
        """
        Устаревший метод, оставлен для совместимости.
        """
        pass

    def load_query_image(self):
        """
        Загрузка изображения для поиска.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.bmp *.tiff *.webp)"
        )

        if file_path:
            self.query_image_path = file_path

            # Отображаем предпросмотр
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_label.setPixmap(pixmap)
            else:
                self.preview_label.setText("Не удалось загрузить изображение")

    def select_search_folder(self):
        """
        Выбор папки с изображениями для поиска.
        """
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку с изображениями"
        )

        if folder_path:
            self.search_folder = folder_path
            self.select_folder_btn.setText(f"Папка: {os.path.basename(folder_path)}")

            # Проверяем, есть ли индекс для этой папки
            self.check_folder_index(folder_path)

    def index_folder(self):
        """
        Инициирует индексацию выбранной папки с изображениями.
        """
        if not self.search_folder:
            self.select_search_folder()
            if not self.search_folder:  # Если пользователь отменил выбор
                return

        # Получаем экстрактор
        extractor = AVAILABLE_EXTRACTORS[self.model_combo.currentIndex()]

        # Формируем путь для сохранения индекса
        index_dir = os.path.join(self.search_folder, ".index")
        os.makedirs(index_dir, exist_ok=True)

        extractor_name = extractor.name.replace(" ", "_").lower()
        index_path = os.path.join(index_dir, f"image_index_{extractor_name}.pkl")

        # Отправляем сигнал для индексации
        self.index_folder_requested.emit(self.search_folder, extractor, index_path)

    def check_folder_index(self, folder_path):
        """
        Проверяет наличие индекса для указанной папки.

        Args:
            folder_path (str): Путь к папке
        """
        index_dir = os.path.join(folder_path, ".index")

        if os.path.exists(index_dir):
            index_files = [f for f in os.listdir(index_dir) if f.startswith("image_index_") and f.endswith(".pkl")]

            if index_files:
                self.indexed_folders.append(folder_path)
                self.status_label.setText(f"Найден индекс для папки {os.path.basename(folder_path)}")
                self.status_label.setStyleSheet("color: green;")
                self.use_index_checkbox.setEnabled(True)
            else:
                self.status_label.setText(f"Индекс для папки {os.path.basename(folder_path)} не найден")
                self.status_label.setStyleSheet("color: #FF8C00;")  # Dark orange
        else:
            self.status_label.setText("Папка не индексирована. Рекомендуется создать индекс для больших коллекций.")
            self.status_label.setStyleSheet("color: #FF8C00;")  # Dark orange

    def select_results_folder(self):
        """
        Выбор папки для сохранения результатов.
        """
        folder_path = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения результатов"
        )

        if folder_path:
            self.results_folder = folder_path
            self.select_output_btn.setText(f"Папка результатов: {os.path.basename(folder_path)}")

    def start_search(self):
        """
        Запуск поиска похожих изображений.
        """
        if not self.query_image_path or not self.search_folder:
            return

        # Получаем настройки поиска
        extractor = AVAILABLE_EXTRACTORS[self.model_combo.currentIndex()]
        similarity_threshold = self.similarity_spinbox.value()
        max_results = self.results_spinbox.value()

        # Отправляем сигнал с параметрами поиска
        self.search_requested.emit(
            self.query_image_path,
            self.search_folder,
            extractor,
            similarity_threshold,
            max_results
        )

    def save_results(self):
        """
        Запрос на сохранение результатов.
        """
        self.save_results_requested.emit()

    def cancel_search(self):
        """
        Запрос на отмену поиска.
        """
        self.cancel_search_requested.emit()
        self.status_label.setText("Отмена поиска...")
        self.status_label.setStyleSheet("color: var(--error-color);")
        self.cancel_search_btn.setEnabled(False)

    def set_search_in_progress(self, in_progress):
        """
        Установка состояния поиска (идет/завершен).

        Args:
            in_progress (bool): True, если поиск выполняется
        """
        self.search_btn.setVisible(not in_progress)
        self.cancel_search_btn.setVisible(in_progress)
        self.cancel_search_btn.setEnabled(True)  # Сбрасываем состояние кнопки отмены
        self.load_image_btn.setEnabled(not in_progress)
        self.select_folder_btn.setEnabled(not in_progress)
        self.progress_bar_label.setVisible(in_progress)
        self.index_folder_btn.setEnabled(not in_progress)

        # Отключаем элементы управления настройками при поиске
        self.model_combo.setEnabled(not in_progress)
        self.model_info_btn.setEnabled(not in_progress)
        self.similarity_slider.setEnabled(not in_progress)
        self.similarity_spinbox.setEnabled(not in_progress)
        self.results_spinbox.setEnabled(not in_progress and not self.show_all_results_checkbox.isChecked())
        self.show_all_results_checkbox.setEnabled(not in_progress)
        self.use_index_checkbox.setEnabled(not in_progress)

        # Сбрасываем статус при завершении поиска
        if not in_progress:
            self.status_label.setText("")
            self.status_label.setStyleSheet("")

    def enable_save_results(self, enable):
        """
        Включение/отключение кнопки сохранения результатов.

        Args:
            enable (bool): True для включения, False для отключения
        """
        self.save_results_btn.setEnabled(enable)

    def get_results_folder(self):
        """
        Получение папки для сохранения результатов.

        Returns:
            str: Путь к папке или None, если не выбрана
        """
        if not self.results_folder:
            self.select_results_folder()

        return self.results_folder

    def get_query_name(self):
        """
        Получение имени запроса (без расширения).

        Returns:
            str: Имя запроса
        """
        if self.query_image_path:
            return os.path.splitext(os.path.basename(self.query_image_path))[0]
        return "unknown"

    def get_current_extractor_name(self):
        """
        Получение названия текущего экстрактора.

        Returns:
            str: Название экстрактора
        """
        return AVAILABLE_EXTRACTORS[self.model_combo.currentIndex()].name

    def get_similarity_threshold(self):
        """
        Получение текущего порога сходства.

        Returns:
            float: Порог сходства (0-1)
        """
        return self.similarity_spinbox.value()

    def show_models_info(self):
        """
        Открывает диалоговое окно с информацией о моделях поиска.
        """
        dialog = ModelsInfoDialog(self)
        dialog.exec_()

    def use_index_enabled(self):
        """
        Проверяет, включено ли использование индекса.

        Returns:
            bool: True, если использование индекса включено
        """
        return self.use_index_checkbox.isChecked()