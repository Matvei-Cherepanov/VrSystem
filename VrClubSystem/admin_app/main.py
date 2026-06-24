#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Административное Desktop-приложение
Точка входа в приложение.
"""

import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import AdminApp

def main():
    """Запуск приложения."""
    try:
        app = AdminApp()
        app.run()
    except Exception as e:
        import tkinter.messagebox as msgbox
        # Если ошибка произошла до создания окна, покажем в консоли
        print(f"Критическая ошибка: {e}")
        # Пытаемся показать сообщение через Tkinter
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            msgbox.showerror(
                "Критическая ошибка",
                f"При запуске приложения произошла ошибка:\n\n{e}"
            )
            root.destroy()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()