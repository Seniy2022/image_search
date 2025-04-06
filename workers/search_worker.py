# -*- coding: utf-8 -*-
"""
Рабочий поток для поиска похожих изображений.
"""

from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker


class SearchWorker(QThread):
    """
    Рабочий поток для поиска похожих изображений.

    Signals:
        progress_update (int): Сигнал обновления прогресса (0-100)
        result_ready (list): Сигнал готовности результатов
        error_occurred (str): Сигнал возникновения ошибки
        search_cancelled (): Сигнал отмены поиска
    """
    progress_update = pyqtSignal(int)
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    search_cancelled = pyqtSignal()

    def __init__(self, query_image_path, search_folder, extractor, similarity_threshold, max_results):
        """
        Инициализация рабочего потока.

        Args:
            query_image_path (str): Путь к изображению запроса
            search_folder (str): Путь к папке для поиска
            extractor (FeatureExtractor): Экстрактор признаков
            similarity_threshold (float): Порог сходства (0-1)
            max_results (int): Максимальное количество результатов (0 - без ограничений)
        """
        super().__init__()
        self.query_image_path = query_image_path
        self.search_folder = search_folder
        self.extractor = extractor
        self.similarity_threshold = similarity_threshold
        self.max_results = max_results

        # Флаг для отслеживания состояния потока
        self.running = True
        self.mutex = QMutex()
        self.cancelled = False

    def stop(self):
        """
        Остановка рабочего потока.
        """
        with QMutexLocker(self.mutex):
            self.running = False
            self.cancelled = True

    def run(self):
        """
        Основной метод, выполняющийся в отдельном потоке.
        Ищет похожие изображения и отправляет результаты через сигналы.
        """
        try:
            # Получаем дескрипторы запроса
            query_features = self.extractor.extract_features(self.query_image_path)

            if query_features is None or len(query_features) == 0:
                self.error_occurred.emit("Не удалось извлечь признаки из изображения запроса")
                return

            # Список для хранения результатов (путь к изображению, сходство)
            results = []

            # Получаем список всех файлов изображений в папке
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            image_files = []

            for ext in image_extensions:
                image_files.extend(list(Path(self.search_folder).glob(f'*{ext}')))
                image_files.extend(list(Path(self.search_folder).glob(f'*{ext.upper()}')))

            total_files = len(image_files)

            # Если нет файлов, возвращаем пустой результат
            if total_files == 0:
                self.result_ready.emit([])
                self.progress_update.emit(100)
                return

            for i, img_path in enumerate(image_files):
                # Проверяем, не была ли запрошена остановка
                with QMutexLocker(self.mutex):
                    if not self.running:
                        # Если работа была отменена, отправляем сигнал
                        if self.cancelled:
                            self.search_cancelled.emit()
                        break

                # Обновляем прогресс
                self.progress_update.emit(int(100 * i / total_files))

                try:
                    # Получаем дескрипторы текущего изображения
                    current_features = self.extractor.extract_features(str(img_path))

                    if current_features is not None and len(current_features) > 0:
                        # Сравниваем дескрипторы
                        similarity = self.extractor.compare_features(query_features, current_features)

                        # Если сходство выше порога, добавляем в результаты
                        if similarity >= self.similarity_threshold:
                            results.append((str(img_path), similarity))
                except Exception as e:
                    print(f"Ошибка при обработке {img_path}: {e}")

            # Сортируем результаты по сходству (по убыванию)
            results.sort(key=lambda x: x[1], reverse=True)

            # Ограничиваем количество результатов, если указано
            if self.max_results > 0:
                results = results[:self.max_results]

            # Отправляем результаты
            self.result_ready.emit(results)
            self.progress_update.emit(100)

        except Exception as e:
            self.error_occurred.emit(f"Произошла ошибка при поиске: {str(e)}")