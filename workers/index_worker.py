# -*- coding: utf-8 -*-
"""
Рабочий поток для индексации папки с изображениями.
"""

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from batch_processing.feature_indexer import FeatureIndexer


class IndexWorker(QThread):
    """
    Рабочий поток для индексации папки с изображениями.

    Signals:
        progress_update (int): Сигнал обновления прогресса (0-100)
        index_completed (str): Сигнал успешного завершения индексации
        index_failed (str): Сигнал ошибки индексации
        index_cancelled (): Сигнал отмены индексации
    """
    progress_update = pyqtSignal(int)
    index_completed = pyqtSignal(str)
    index_failed = pyqtSignal(str)
    index_cancelled = pyqtSignal()

    def __init__(self, folder_path, extractor, output_path=None):
        """
        Инициализация рабочего потока для индексации.

        Args:
            folder_path (str): Путь к папке с изображениями
            extractor: Экстрактор признаков
            output_path (str, optional): Путь для сохранения индекса
        """
        super().__init__()
        self.folder_path = folder_path
        self.extractor = extractor
        self.output_path = output_path

        # Флаги для контроля выполнения
        self.mutex = QMutex()
        self.cancelled = False

    def stop(self):
        """
        Остановка индексации.
        """
        with QMutexLocker(self.mutex):
            self.cancelled = True
            if hasattr(self, 'indexer') and self.indexer:
                self.indexer.stop()

    def run(self):
        """
        Запуск процесса индексации.
        """
        try:
            # Создаем индексатор
            self.indexer = FeatureIndexer(
                self.folder_path,
                self.extractor,
                self.output_path
            )

            # Подключаем сигналы
            self.indexer.progress_update.connect(self.progress_update.emit)
            self.indexer.index_completed.connect(self.handle_index_completed)
            self.indexer.index_failed.connect(self.handle_index_failed)

            # Запускаем индексацию
            self.indexer.run()

        except Exception as e:
            self.index_failed.emit(f"Ошибка при индексации: {str(e)}")

    def handle_index_completed(self, index_path):
        """
        Обработка успешного завершения индексации.

        Args:
            index_path (str): Путь к созданному индексу
        """
        # Проверяем, не была ли отменена индексация
        with QMutexLocker(self.mutex):
            if self.cancelled:
                self.index_cancelled.emit()
                return

        # Отправляем сигнал о завершении
        self.index_completed.emit(index_path)

    def handle_index_failed(self, error_message):
        """
        Обработка ошибки индексации.

        Args:
            error_message (str): Сообщение об ошибке
        """
        # Проверяем, не была ли отменена индексация
        with QMutexLocker(self.mutex):
            if self.cancelled:
                self.index_cancelled.emit()
                return

        # Отправляем сигнал об ошибке
        self.index_failed.emit(error_message)