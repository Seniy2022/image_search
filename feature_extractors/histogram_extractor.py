# -*- coding: utf-8 -*-
"""
Экстрактор признаков на основе гистограмм цветов.
Позволяет находить изображения с похожими цветовыми характеристиками.
"""

import cv2
import numpy as np
from feature_extractors.base_extractor import FeatureExtractor


class ColorHistogramExtractor(FeatureExtractor):
    """
    Экстрактор признаков на основе цветовых гистограмм.
    Хорошо работает для поиска изображений с похожей цветовой гаммой.
    """

    def __init__(self):
        """
        Инициализация экстрактора гистограмм.
        """
        super().__init__()
        self.name = "Цветовая гистограмма"

        # Параметры гистограммы
        self.bins = [8, 8, 8]  # Количество бинов для каждого канала (H, S, V)
        self.hist_ranges = [0, 180, 0, 256, 0, 256]  # Диапазоны для каждого канала

    def extract_features(self, image_path):
        """
        Извлечение цветовых гистограмм из изображения.

        Args:
            image_path (str): Путь к изображению

        Returns:
            numpy.ndarray: Гистограмма изображения или None в случае ошибки
        """
        try:
            # Загружаем изображение
            img = cv2.imread(image_path)
            if img is None:
                return None

            # Изменяем размер для ускорения обработки и стандартизации
            img = cv2.resize(img, (256, 256))

            # Преобразуем в пространство HSV, которое лучше передает цветовые характеристики
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            # Вычисляем гистограмму по трем каналам (H, S, V)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, self.bins, self.hist_ranges)

            # Нормализуем гистограмму для сравнения изображений разных размеров
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

            return hist.flatten()

        except Exception as e:
            print(f"Ошибка при извлечении цветовой гистограммы из {image_path}: {e}")
            return None

    def compare_features(self, features1, features2):
        """
        Сравнение цветовых гистограмм.

        Args:
            features1 (numpy.ndarray): Гистограмма первого изображения
            features2 (numpy.ndarray): Гистограмма второго изображения

        Returns:
            float: Значение сходства от 0 до 1, где 1 - полное сходство
        """
        # Проверка на пустые дескрипторы
        if features1 is None or features2 is None:
            return 0.0

        try:
            # Вычисляем расстояние между гистограммами с помощью различных метрик
            # и берем среднее значение для более точного результата

            # 1. Корреляция (1 = идеальное совпадение, -1 = полная противоположность)
            correlation = cv2.compareHist(features1, features2, cv2.HISTCMP_CORREL)
            # Преобразуем в диапазон [0, 1]
            correlation = (correlation + 1) / 2

            # 2. Пересечение гистограмм (выше = лучше)
            intersection = cv2.compareHist(features1, features2, cv2.HISTCMP_INTERSECT)
            # Нормализуем к [0, 1]
            intersection = intersection / np.sum(features1)

            # 3. Хи-квадрат (ниже = лучше)
            chi_square = cv2.compareHist(features1, features2, cv2.HISTCMP_CHISQR)
            # Преобразуем в [0, 1], где 1 = лучшее совпадение
            chi_square = np.exp(-chi_square / 10)

            # Вычисляем средний показатель сходства
            similarity = (correlation + intersection + chi_square) / 3

            return float(similarity)

        except Exception as e:
            print(f"Ошибка при сравнении цветовых гистограмм: {e}")
            return 0.0

    def analyze_dominant_colors(self, hist, hsv_img):
        """
        Анализирует доминирующие цвета на основе гистограммы HSV.

        Args:
            hist: Гистограмма HSV
            hsv_img: Изображение в формате HSV

        Returns:
            list: Список доминирующих цветов в формате BGR
        """
        # Находим индексы максимальных значений в гистограмме
        h_bins, s_bins, v_bins = self.bins
        hist = hist.reshape(h_bins, s_bins, v_bins)

        dom_colors = []
        # Находим топ-5 значений гистограммы
        for _ in range(5):
            idx = np.unravel_index(hist.argmax(), hist.shape)
            h, s, v = idx

            # Переводим индексы бинов в значения H, S, V
            h_val = int(180 * h / h_bins + 180 / (2 * h_bins))
            s_val = int(255 * s / s_bins + 255 / (2 * s_bins))
            v_val = int(255 * v / v_bins + 255 / (2 * v_bins))

            # Преобразуем HSV в BGR
            hsv_color = np.array([[[h_val, s_val, v_val]]], dtype=np.uint8)
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)
            dom_colors.append(bgr_color[0, 0].tolist())

            # Убираем найденное значение из гистограммы
            hist[h, s, v] = 0

        return dom_colors