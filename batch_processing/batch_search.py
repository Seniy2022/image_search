# -*- coding: utf-8 -*-
"""
Модуль для быстрого поиска по предварительно проиндексированным изображениям.
"""

import os
import pickle
import threading
import numpy as np


class BatchSearchProcessor:
    """
    Класс для быстрого поиска по предварительно проиндексированным изображениям.
    """

    def __init__(self):
        """
        Инициализация процессора.
        """
        self.indexes = {}  # {путь_к_индексу: данные_индекса}

    def load_index(self, index_path):
        """
        Загрузка индекса из файла.

        Args:
            index_path (str): Путь к файлу индекса

        Returns:
            bool: True если индекс успешно загружен
        """
        try:
            with open(index_path, 'rb') as f:
                self.indexes[index_path] = pickle.load(f)
            return True
        except Exception as e:
            print(f"Ошибка при загрузке индекса {index_path}: {e}")
            return False

    def search_in_index(self, query_features, index_path, similarity_threshold=0.7, max_results=0):
        """
        Поиск похожих изображений в индексе.

        Args:
            query_features: Признаки изображения запроса
            index_path (str): Путь к индексу
            similarity_threshold (float): Порог сходства
            max_results (int): Максимальное количество результатов (0 - без ограничения)

        Returns:
            list: Список кортежей (путь_к_изображению, сходство)
        """
        # Загружаем индекс, если он еще не загружен
        if index_path not in self.indexes:
            if not self.load_index(index_path):
                return []

        index_data = self.indexes[index_path]
        features_dict = index_data['features']
        extractor_name = index_data['extractor_name']

        # Получаем экстрактор, соответствующий индексу
        from feature_extractors import AVAILABLE_EXTRACTORS
        extractor = None

        for ext in AVAILABLE_EXTRACTORS:
            if ext.name == extractor_name:
                extractor = ext
                break

        if extractor is None:
            print(f"Не найден экстрактор {extractor_name} для индекса {index_path}")
            return []

        # Проверяем и преобразуем размерность вектора запроса
        if hasattr(query_features, 'ndim') and query_features.ndim > 1:
            query_features = query_features.reshape(-1)

        # Ищем похожие изображения
        results = []

        for img_path, features in features_dict.items():
            # Пропускаем изображения, которых больше нет на диске
            if not os.path.exists(img_path):
                continue

            # Преобразуем признаки из индекса, если необходимо
            if hasattr(features, 'ndim') and features.ndim > 1:
                features = features.reshape(-1)

            # Проверяем совпадение размерностей
            if hasattr(query_features, 'shape') and hasattr(features, 'shape'):
                if query_features.shape != features.shape:
                    # Если размерности не совпадают, пропускаем
                    print(f"Несовпадение размерностей для {img_path}: {query_features.shape} vs {features.shape}")
                    continue

            try:
                # Сравниваем признаки
                similarity = extractor.compare_features(query_features, features)

                # Если сходство выше порога, добавляем в результаты
                if similarity >= similarity_threshold:
                    results.append((img_path, similarity))
            except Exception as e:
                print(f"Ошибка при сравнении признаков для {img_path}: {e}")

        # Сортируем результаты по убыванию сходства
        results.sort(key=lambda x: x[1], reverse=True)

        # Ограничиваем количество результатов, если нужно
        if max_results > 0:
            results = results[:max_results]

        return results


class MultiIndexSearch:
    """
    Класс для параллельного поиска по нескольким индексам.
    """

    def __init__(self):
        """
        Инициализация поисковика.
        """
        self.processor = BatchSearchProcessor()

    def search_in_multiple_indexes(self, query_features, index_paths, similarity_threshold=0.7, max_results=0):
        """
        Поиск изображения в нескольких индексах параллельно.

        Args:
            query_features: Признаки запроса
            index_paths (list): Список путей к индексам
            similarity_threshold (float): Порог сходства
            max_results (int): Максимальное количество результатов

        Returns:
            list: Объединенный список результатов
        """
        # Результаты поиска для каждого индекса
        results_per_index = {}

        # Функция поиска для каждого индекса
        def search_in_one_index(index_path):
            results = self.processor.search_in_index(
                query_features,
                index_path,
                similarity_threshold,
                max_results
            )
            results_per_index[index_path] = results

        # Создаем потоки для каждого индекса
        threads = []
        for index_path in index_paths:
            thread = threading.Thread(target=search_in_one_index, args=(index_path,))
            threads.append(thread)
            thread.start()

        # Ожидаем завершения всех потоков
        for thread in threads:
            thread.join()

        # Объединяем результаты
        all_results = []
        for results in results_per_index.values():
            all_results.extend(results)

        # Удаляем дубликаты (одно и то же изображение может быть в нескольких индексах)
        unique_results = {}
        for img_path, similarity in all_results:
            if img_path not in unique_results or similarity > unique_results[img_path]:
                unique_results[img_path] = similarity

        # Преобразуем обратно в список кортежей и сортируем
        combined_results = [(img_path, similarity) for img_path, similarity in unique_results.items()]
        combined_results.sort(key=lambda x: x[1], reverse=True)

        # Ограничиваем количество результатов, если нужно
        if max_results > 0:
            combined_results = combined_results[:max_results]

        return combined_results