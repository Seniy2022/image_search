# -*- coding: utf-8 -*-
"""
Утилиты для работы с изображениями.
"""

import cv2
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


def load_image_pixmap(image_path, max_width=None, max_height=None):
    """
    Загружает изображение и возвращает QPixmap.

    Args:
        image_path (str): Путь к изображению
        max_width (int, optional): Максимальная ширина
        max_height (int, optional): Максимальная высота

    Returns:
        QPixmap: Объект QPixmap или None при ошибке
    """
    try:
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            return None

        # Масштабирование, если указаны размеры
        if max_width is not None and max_height is not None:
            pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

        return pixmap

    except Exception as e:
        print(f"Ошибка при загрузке изображения {image_path}: {e}")
        return None


def cv_to_qpixmap(cv_img):
    """
    Преобразует изображение OpenCV в QPixmap.

    Args:
        cv_img: Изображение OpenCV (numpy array)

    Returns:
        QPixmap: Объект QPixmap или None при ошибке
    """
    try:
        height, width, channels = cv_img.shape

        # Преобразование BGR -> RGB
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        # Создание QImage
        bytes_per_line = channels * width
        q_img = QImage(
            rgb_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

        # Создание QPixmap
        return QPixmap.fromImage(q_img)

    except Exception as e:
        print(f"Ошибка при преобразовании изображения OpenCV в QPixmap: {e}")
        return None


def resize_image(image_path, max_dim=800):
    """
    Загружает и изменяет размер изображения для предварительной обработки.

    Args:
        image_path (str): Путь к изображению
        max_dim (int): Максимальный размер большей стороны

    Returns:
        numpy.ndarray: Измененное изображение или None при ошибке
    """
    try:
        # Загрузка изображения
        img = cv2.imread(image_path)

        if img is None:
            return None

        height, width = img.shape[:2]

        # Определение коэффициента масштабирования
        if max(height, width) > max_dim:
            if height > width:
                scale = max_dim / height
            else:
                scale = max_dim / width

            new_height = int(height * scale)
            new_width = int(width * scale)

            # Изменение размера
            resized = cv2.resize(
                img,
                (new_width, new_height),
                interpolation=cv2.INTER_AREA
            )

            return resized

        return img

    except Exception as e:
        print(f"Ошибка при изменении размера изображения {image_path}: {e}")
        return None