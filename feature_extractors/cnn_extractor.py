# -*- coding: utf-8 -*-
"""
Экстрактор признаков на основе предобученных CNN моделей (ResNet, VGG и др.)
"""

import cv2
import numpy as np
from feature_extractors.base_extractor import FeatureExtractor

try:
    import torch
    import torchvision.models as models
    import torchvision.transforms as transforms
    from PIL import Image

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class CNNFeatureExtractor(FeatureExtractor):
    """
    Экстрактор признаков на основе глубоких нейронных сетей.
    Использует предобученные модели из torchvision для получения эмбеддингов изображений.
    """

    def __init__(self, model_name="resnet50"):
        """
        Инициализация экстрактора на основе CNN.

        Args:
            model_name (str): Название модели
                Варианты:  "resnet50"
        """
        super().__init__()

        self.model_name = model_name
        self.name = f"CNN ({model_name})"
        self.initialized = False

        if not TORCH_AVAILABLE:
            print("Библиотеки PyTorch не установлены.")
            print("Установите их командой: pip install torch torchvision pillow")
            return

        try:
            # Загружаем предобученную модель
            if model_name == "resnet50":
                self.model = models.resnet50(pretrained=True)
                self.output_size = 2048

            # Подготовка обработки изображений
            self.transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])

            # Переводим модель в режим оценки
            self.feature_extractor.eval()

            # Проверяем наличие CUDA
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.feature_extractor = self.feature_extractor.to(self.device)

            self.initialized = True

        except Exception as e:
            print(f"Ошибка при инициализации CNN экстрактора: {e}")

    def extract_features(self, image_path):
        """
        Извлечение глубоких признаков из изображения.

        Args:
            image_path (str): Путь к изображению

        Returns:
            numpy.ndarray: Вектор признаков или None, если не удалось извлечь
        """
        if not self.initialized:
            return None

        try:
            # Загружаем и преобразуем изображение
            img = Image.open(image_path).convert('RGB')
            img_tensor = self.transform(img).unsqueeze(0).to(self.device)

            # Извлекаем признаки (без вычисления градиентов)
            with torch.no_grad():
                features = self.feature_extractor(img_tensor)

            # Преобразуем тензор в плоский массив numpy
            features = features.squeeze().cpu().numpy()

            # Проверяем размерность и приводим к одномерному массиву
            if features.ndim > 1:
                features = features.reshape(-1)

            # Приводим к типу float32 для уменьшения размера и единообразия
            return features.astype(np.float32)

        except Exception as e:
            print(f"Ошибка при извлечении CNN признаков из {image_path}: {e}")
            return None

    def compare_features(self, features1, features2):
        """
        Сравнение векторов признаков с использованием косинусного сходства.

        Args:
            features1 (numpy.ndarray): Первый вектор признаков
            features2 (numpy.ndarray): Второй вектор признаков

        Returns:
            float: Значение сходства от 0 до 1, где 1 - полное сходство
        """
        if features1 is None or features2 is None:
            return 0.0

        try:
            # Проверяем и преобразуем размерности
            if features1.ndim > 1:
                features1 = features1.reshape(-1)
            if features2.ndim > 1:
                features2 = features2.reshape(-1)

            # Если размерности всё еще не совпадают, используем более короткий вектор
            # или возвращаем низкое сходство
            if features1.shape != features2.shape:
                print(
                    f"Предупреждение: несовпадающие размерности векторов признаков: {features1.shape} и {features2.shape}")
                return 0.1  # Низкое сходство для несовместимых векторов

            # Вычисляем косинусное сходство
            dot_product = np.dot(features1, features2)
            norm1 = np.linalg.norm(features1)
            norm2 = np.linalg.norm(features2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            cosine_similarity = dot_product / (norm1 * norm2)

            # Преобразуем в диапазон [0, 1]
            similarity = (cosine_similarity + 1) / 2

            return float(similarity)

        except Exception as e:
            print(f"Ошибка при сравнении CNN признаков: {e}")
            return 0.0