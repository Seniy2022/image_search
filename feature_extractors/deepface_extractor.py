# -*- coding: utf-8 -*-
"""
Экстрактор признаков лиц на основе библиотеки DeepFace.
Это более продвинутая альтернатива dlib/face_recognition.
"""

import numpy as np
from feature_extractors.base_extractor import FeatureExtractor


class DeepFaceExtractor(FeatureExtractor):
    """
    Экстрактор признаков лиц на основе библиотеки DeepFace.
    Использует предобученные модели глубокого обучения для распознавания лиц.
    """

    def __init__(self, model_name="VGG-Face"):
        """
        Инициализация экстрактора.

        Args:
            model_name (str): Название модели для извлечения признаков
                Варианты: "VGG-Face", "Facenet", "OpenFace", "DeepFace", "ArcFace"
                VGG-Face самая быстрая, но менее точная
                Facenet и ArcFace более точные, но медленнее
        """
        super().__init__()

        # Инициализация необходимых модулей
        try:
            from deepface import DeepFace
            self.DeepFace = DeepFace
            self.model_name = model_name
            self.name = f"DeepFace (распознавание лиц)"
            self.initialized = True
        except ImportError:
            print("Библиотека DeepFace не установлена.")
            print("Установите её командой: pip install deepface")
            self.name = "DeepFace (не установлен)"
            self.initialized = False

    def extract_features(self, image_path):
        """
        Извлечение дескрипторов лиц из изображения.

        Args:
            image_path (str): Путь к изображению

        Returns:
            numpy.ndarray: Массив дескрипторов лиц или пустой массив, если лица не найдены
        """
        # Проверка, что библиотека инициализирована
        if not self.initialized:
            return np.array([])

        try:
            # Используем DeepFace для получения эмбеддингов (векторов признаков) лица
            # Параметр detector="opencv" обеспечивает более быструю, но менее точную детекцию лиц
            # Параметр detector="retinaface" обеспечивает более точную, но медленную детекцию
            result = self.DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                detector_backend="opencv",
                enforce_detection=False  # Не выбрасывать ошибку, если лицо не найдено
            )

            # DeepFace может вернуть список дескрипторов, если на изображении несколько лиц
            if isinstance(result, list):
                # Если есть хотя бы один дескриптор
                if len(result) > 0:
                    # Извлекаем все дескрипторы
                    embeddings = [np.array(item["embedding"]) for item in result]
                    return np.array(embeddings)
                else:
                    return np.array([])
            else:
                # Один дескриптор, оформляем его в список
                return np.array([np.array(result["embedding"])])

        except Exception as e:
            print(f"Ошибка при обработке изображения {image_path}: {e}")
            return np.array([])

    def compare_features(self, features1, features2):
        """
        Сравнение дескрипторов лиц.

        Args:
            features1 (numpy.ndarray): Первый набор дескрипторов лиц
            features2 (numpy.ndarray): Второй набор дескрипторов лиц

        Returns:
            float: Значение сходства от 0 до 1, где 1 - полное сходство
        """
        # Проверка, что библиотека инициализирована и дескрипторы не пустые
        if not self.initialized or features1 is None or len(features1) == 0 or features2 is None or len(features2) == 0:
            return 0.0

        try:
            # Сравниваем каждое лицо в features1 с каждым лицом в features2
            best_similarity = 0.0

            for face1 in features1:
                for face2 in features2:
                    # Вычисляем косинусное сходство
                    dot_product = np.dot(face1, face2)
                    norm_product = np.linalg.norm(face1) * np.linalg.norm(face2)

                    if norm_product > 0:
                        cosine_similarity = dot_product / norm_product
                        # Переводим в диапазон [0, 1]
                        similarity = (cosine_similarity + 1) / 2
                    else:
                        similarity = 0.0

                    # Сохраняем лучший результат
                    best_similarity = max(best_similarity, similarity)

            return best_similarity

        except Exception as e:
            print(f"Ошибка при сравнении дескрипторов лиц: {e}")
            return 0.0