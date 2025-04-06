# -*- coding: utf-8 -*-
"""
Пакет с экстракторами признаков для поиска изображений.
"""

from feature_extractors.base_extractor import FeatureExtractor
from feature_extractors.sift_extractor import SIFTFeatureExtractor
from feature_extractors.histogram_extractor import ColorHistogramExtractor

# Пытаемся импортировать DeepFace экстрактор
try:
    from feature_extractors.deepface_extractor import DeepFaceExtractor
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

# Пытаемся импортировать CNN экстрактор
try:
    from feature_extractors.cnn_extractor import CNNFeatureExtractor
    CNN_AVAILABLE = True
except ImportError:
    CNN_AVAILABLE = False

AVAILABLE_EXTRACTORS = [
    SIFTFeatureExtractor(),
    ColorHistogramExtractor()
]

# Добавляем DeepFace экстрактор, если он доступен
if DEEPFACE_AVAILABLE:
    AVAILABLE_EXTRACTORS.append(DeepFaceExtractor())

# Добавляем ResNet50, но убираем VGG16
if CNN_AVAILABLE:
    AVAILABLE_EXTRACTORS.append(CNNFeatureExtractor("resnet50"))

__all__ = [
    'FeatureExtractor',
    'SIFTFeatureExtractor',
    'ColorHistogramExtractor',
    'AVAILABLE_EXTRACTORS'
]

# Добавляем DeepFaceExtractor в __all__, если он доступен
if DEEPFACE_AVAILABLE:
    __all__.append('DeepFaceExtractor')

# Добавляем CNNFeatureExtractor в __all__, если он доступен
if CNN_AVAILABLE:
    __all__.append('CNNFeatureExtractor')