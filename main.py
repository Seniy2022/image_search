#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль запуска приложения для поиска изображений по образцу.
"""

import os
import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import ImageSearchApp


def main():
    """
    Главная функция запуска приложения.
    """
    app = QApplication(sys.argv)

    # Устанавливаем стили для всего приложения
    style_path = "ui/styles/style.qss"
    try:
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"Файл стилей {style_path} не найден.")
    except Exception as e:
        print(f"Ошибка при загрузке стилей: {e}")

    window = ImageSearchApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()