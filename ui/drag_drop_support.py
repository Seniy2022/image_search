# -*- coding: utf-8 -*-
"""
Расширение функциональности перетаскивания файлов (drag & drop) для панели управления.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class DragDropMixin:
    """
    Миксин для добавления функциональности перетаскивания к виджетам.
    """

    def setup_drag_drop(self):
        """
        Настройка поддержки перетаскивания.
        """
        # Включаем прием событий перетаскивания
        self.setAcceptDrops(True)

        # Проверяем, есть ли методы для обработки загрузки изображения
        if not hasattr(self, 'handle_image_drop') or not callable(self.handle_image_drop):
            raise NotImplementedError("Класс должен реализовать метод handle_image_drop")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """
        Обработка события начала перетаскивания над виджетом.

        Args:
            event (QDragEnterEvent): Событие перетаскивания
        """
        # Проверяем, есть ли в событии URL-адреса (файлы)
        if event.mimeData().hasUrls():
            # Принимаем только файлы изображений
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                extension = file_path.lower().split('.')[-1]

                # Проверяем расширение файла
                if extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']:
                    event.acceptProposedAction()
                    return

        # Если нет подходящих файлов, игнорируем событие
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        """
        Обработка события сброса перетаскиваемого объекта.

        Args:
            event (QDropEvent): Событие сброса
        """
        # Получаем первый URL из перетаскиваемых данных
        urls = event.mimeData().urls()

        if urls:
            # Берем только первый файл
            file_path = urls[0].toLocalFile()
            extension = file_path.lower().split('.')[-1]

            # Проверяем, что это изображение
            if extension in ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']:
                # Вызываем обработчик
                self.handle_image_drop(file_path)
                event.acceptProposedAction()
                return

        event.ignore()