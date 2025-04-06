# -*- coding: utf-8 -*-
"""
Экстрактор признаков на основе алгоритма SIFT (Scale-Invariant Feature Transform).
Позволяет находить изображения с похожими объектами вне зависимости от масштаба и поворота.
"""

import cv2
import numpy as np
from feature_extractors.base_extractor import FeatureExtractor


class SIFTFeatureExtractor(FeatureExtractor):
    """
    Экстрактор признаков на основе SIFT для распознавания объектов.
    Более мощный, чем ORB, и устойчивый к изменениям масштаба и поворота.
    """

    def __init__(self):
        """
        Инициализация экстрактора SIFT с настройками.
        """
        super().__init__()
        self.name = "SIFT (объекты и формы)"

        # Проверяем доступность SIFT в OpenCV
        try:
            # В OpenCV 4.x SIFT доступен без патентных ограничений
            self.sift = cv2.SIFT_create(nfeatures=1000)
        except AttributeError:
            # Для совместимости со старыми версиями OpenCV
            self.sift = cv2.xfeatures2d.SIFT_create(nfeatures=1000)

        # FLANN параметры для быстрого поиска
        FLANN_INDEX_KDTREE = 1
        self.flann_index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        self.flann_search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(self.flann_index_params, self.flann_search_params)

    def extract_features(self, image_path):
        """
        Извлечение SIFT дескрипторов из изображения.

        Args:
            image_path (str): Путь к изображению

        Returns:
            tuple: (key_points, descriptors) - ключевые точки и их дескрипторы
            или (None, None) в случае ошибки
        """
        try:
            # Загружаем изображение
            img = cv2.imread(image_path)
            if img is None:
                return (None, None)

            # Преобразуем в оттенки серого
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Находим ключевые точки и дескрипторы с помощью SIFT
            keypoints, descriptors = self.sift.detectAndCompute(gray, None)

            if descriptors is None:
                return (None, None)

            return (keypoints, descriptors)

        except Exception as e:
            print(f"Ошибка при извлечении SIFT признаков из {image_path}: {e}")
            return (None, None)

    def compare_features(self, features1, features2):
        """
        Сравнение SIFT дескрипторов с использованием алгоритма ближайших соседей.

        Args:
            features1: (keypoints1, descriptors1) - ключевые точки и дескрипторы первого изображения
            features2: (keypoints2, descriptors2) - ключевые точки и дескрипторы второго изображения

        Returns:
            float: Значение сходства от 0 до 1, где 1 - полное сходство
        """
        # Проверка на пустые дескрипторы
        if None in features1 or None in features2:
            return 0.0

        _, des1 = features1
        _, des2 = features2

        if des1 is None or len(des1) == 0 or des2 is None or len(des2) == 0:
            return 0.0

        try:
            # Находим соответствия между дескрипторами с помощью kNN
            try:
                matches = self.flann.knnMatch(des1, des2, k=2)
            except cv2.error:
                # Если не удалось найти k=2 соседей, пробуем с k=1
                matches = self.flann.knnMatch(des1, des2, k=1)
                good_matches = matches  # В этом случае все совпадения считаются "хорошими"
                return min(1.0, len(good_matches) / max(len(des1), len(des2)) * 3)

            # Применяем тест Лоу для фильтрации хороших совпадений
            good_matches = []
            for match in matches:
                if len(match) >= 2:
                    m, n = match
                    # Совпадение считается хорошим, если расстояние первого соседа
                    # значительно меньше расстояния до второго соседа
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
                elif len(match) == 1:
                    # Если найден только один сосед, считаем его хорошим совпадением
                    good_matches.append(match[0])

            # Вычисляем меру сходства
            # Масштабируем для получения более интуитивных значений
            similarity = min(1.0, len(good_matches) / max(len(des1), len(des2)) * 3)

            return similarity

        except Exception as e:
            print(f"Ошибка при сравнении SIFT дескрипторов: {e}")
            return 0.0

    def _filter_matches_with_homography(self, keypoints1, keypoints2, matches, threshold=3.0):
        """
        Дополнительная фильтрация совпадений с помощью вычисления гомографии.
        Это позволяет отфильтровать случайные совпадения.

        Args:
            keypoints1: Ключевые точки первого изображения
            keypoints2: Ключевые точки второго изображения
            matches: Найденные совпадения
            threshold: Порог для фильтрации выбросов

        Returns:
            list: Отфильтрованные совпадения
        """
        if len(matches) < 4:
            return matches

        # Преобразуем ключевые точки в numpy массивы
        src_pts = np.float32([keypoints1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

        # Вычисляем матрицу гомографии
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, threshold)

        if H is None:
            return matches

        # Выбираем только совпадения, соответствующие найденной модели
        good_matches = [matches[i] for i in range(len(matches)) if mask[i][0] > 0]

        return good_matches