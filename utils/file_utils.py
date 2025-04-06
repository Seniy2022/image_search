# -*- coding: utf-8 -*-
"""
Утилиты для работы с файлами и каталогами.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def get_image_files(folder_path):
    """
    Получает список всех файлов изображений в указанной папке.

    Args:
        folder_path (str): Путь к папке

    Returns:
        list: Список путей к файлам изображений
    """
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    image_files = []

    for ext in image_extensions:
        image_files.extend(list(Path(folder_path).glob(f'*{ext}')))
        image_files.extend(list(Path(folder_path).glob(f'*{ext.upper()}')))

    return [str(path) for path in image_files]


def create_results_folder(base_folder, query_name):
    """
    Создает папку для сохранения результатов.

    Args:
        base_folder (str): Базовая папка
        query_name (str): Имя запроса

    Returns:
        str: Путь к созданной папке для результатов
    """
    # Формируем имя папки с текущей датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = f"results_{query_name}_{timestamp}"

    # Полный путь к папке результатов
    result_dir = os.path.join(base_folder, folder_name)

    # Создаем папку, если она не существует
    os.makedirs(result_dir, exist_ok=True)

    return result_dir


def save_search_results(query_image_path, results, result_dir, extractor_name, similarity_threshold):
    """
    Сохраняет результаты поиска в указанную папку.

    Args:
        query_image_path (str): Путь к изображению запроса
        results (list): Список кортежей (путь к изображению, сходство)
        result_dir (str): Путь к папке для сохранения результатов
        extractor_name (str): Название использованного экстрактора
        similarity_threshold (float): Порог сходства

    Returns:
        bool: True если успешно, False в случае ошибки
    """
    try:
        # Копируем запрос
        query_dest = os.path.join(result_dir, f"query_{os.path.basename(query_image_path)}")
        shutil.copy2(query_image_path, query_dest)

        # Копируем результаты
        for i, (img_path, similarity) in enumerate(results):
            ext = os.path.splitext(img_path)[1]
            dest_path = os.path.join(result_dir, f"result_{i + 1:03d}_sim_{similarity:.2f}{ext}")
            shutil.copy2(img_path, dest_path)

        # Создаем текстовый файл с информацией
        with open(os.path.join(result_dir, "info.txt"), "w", encoding="utf-8") as f:
            f.write(f"Запрос: {query_image_path}\n")
            f.write(f"Модель: {extractor_name}\n")
            f.write(f"Коэффициент похожести: {similarity_threshold}\n")
            f.write(f"Количество результатов: {len(results)}\n")
            f.write(f"Дата и время поиска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for i, (img_path, similarity) in enumerate(results):
                f.write(f"{i + 1}. {img_path} - сходство: {similarity:.4f}\n")

        return True

    except Exception as e:
        print(f"Ошибка при сохранении результатов: {e}")
        return False