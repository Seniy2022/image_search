# -*- coding: utf-8 -*-
"""
Модуль для индексации признаков изображений.
"""

import os
import time
import pickle
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker


class FeatureIndexer(QThread):
    """
    Создает индекс признаков изображений для быстрого поиска.
    Работает в фоновом режиме и сохраняет результаты в файл.
    """
    progress_update = pyqtSignal(int)
    index_completed = pyqtSignal(str)
    index_failed = pyqtSignal(str)

    def __init__(self, folder_path, extractor, output_path=None):
        """
        Инициализация индексатора.

        Args:
            folder_path (str): Путь к папке с изображениями
            extractor: Экстрактор признаков
            output_path (str, optional): Путь для сохранения индекса
        """
        super().__init__()
        self.folder_path = folder_path
        self.extractor = extractor

        # Если путь для сохранения не указан, создаем его в папке с изображениями
        if output_path is None:
            extractor_name = extractor.name.replace(" ", "_").lower()
            index_dir = os.path.join(folder_path, ".index")
            os.makedirs(index_dir, exist_ok=True)
            self.output_path = os.path.join(
                index_dir,
                f"image_index_{extractor_name}.pkl"
            )
        else:
            self.output_path = output_path

        # Флаги для контроля выполнения
        self.mutex = QMutex()
        self.running = True
        self.cancelled = False

    def stop(self):
        """
        Остановка индексации.
        """
        with QMutexLocker(self.mutex):
            self.running = False
            self.cancelled = True

    def run(self):
        """
        Выполняет индексацию изображений в указанной папке.
        """
        try:
            # Получаем список изображений
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            image_files = []

            for ext in image_extensions:
                image_files.extend(list(Path(self.folder_path).glob(f'*{ext}')))
                image_files.extend(list(Path(self.folder_path).glob(f'*{ext.upper()}')))

            image_files = [str(path) for path in image_files]
            total_files = len(image_files)

            if total_files == 0:
                self.index_failed.emit("В указанной папке не найдены изображения")
                return

            # Словарь для хранения признаков {путь_к_файлу: признаки}
            features_dict = {}

            # Обрабатываем каждое изображение
            for i, img_path in enumerate(image_files):
                # Проверяем флаг остановки
                with QMutexLocker(self.mutex):
                    if not self.running:
                        if self.cancelled:
                            self.index_failed.emit("Индексация была отменена")
                        return

                try:
                    # Извлекаем признаки
                    features = self.extractor.extract_features(img_path)

                    # Если признаки успешно извлечены, добавляем в словарь
                    if features is not None:
                        features_dict[img_path] = features

                except Exception as e:
                    # Пропускаем файлы с ошибками
                    print(f"Ошибка при обработке {img_path}: {e}")

                # Обновляем прогресс
                progress = int(100 * (i + 1) / total_files)
                self.progress_update.emit(progress)

            # Сохраняем индекс в файл
            with open(self.output_path, 'wb') as f:
                pickle.dump({
                    'extractor_name': self.extractor.name,
                    'features': features_dict,
                    'timestamp': time.time()
                }, f)

            # Отправляем сигнал о завершении
            self.index_completed.emit(self.output_path)

        except Exception as e:
            self.index_failed.emit(f"Ошибка при создании индекса: {str(e)}")