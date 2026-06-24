# -*- coding: utf-8 -*-

"""
Главный модуль приложения.
Содержит класс AdminApp — основной GUI интерфейс.
"""
import sys
import os
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import threading
import time

from DataBase.db import Database as DatabaseManager
from Config import DB_FILENAME, AUTO_REFRESH_INTERVAL_SECONDS, RECORD_TYPES, COLUMNS, COLUMN_NAMES, APP_TITLE, APP_GEOMETRY

class AdminApp:
    """Главное окно административного приложения."""

    def __init__(self):
        """Инициализация приложения."""
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(APP_GEOMETRY)
        self.root.minsize(900, 500)

        # Подключаем базу данных
        self.db = DatabaseManager(DB_FILENAME)

        # Состояние автообновления
        self.auto_refresh_enabled = tk.BooleanVar(value=True)
        self.auto_refresh_running = False
        self.auto_refresh_thread = None

        # Словарь для хранения ID записей в treeview
        self.tree_id_map = {}

        # Создаем интерфейс
        self._create_widgets()
        self._setup_bindings()

        # Загружаем данные
        self.refresh_data()

        # Запускаем автообновление
        self._start_auto_refresh()

    def _create_widgets(self):
        """Создание всех виджетов интерфейса."""
        # Главный контейнер с отступами
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== Верхняя панель инструментов =====
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # Кнопки действий
        btn_add = ttk.Button(
            toolbar_frame,
            text="➕ Добавить",
            command=self._add_record,
            width=14
        )
        btn_add.pack(side=tk.LEFT, padx=(0, 5))

        btn_edit = ttk.Button(
            toolbar_frame,
            text="✏️ Редактировать",
            command=self._edit_record,
            width=14
        )
        btn_edit.pack(side=tk.LEFT, padx=(0, 5))

        btn_delete = ttk.Button(
            toolbar_frame,
            text="🗑️ Удалить",
            command=self._delete_record,
            width=14
        )
        btn_delete.pack(side=tk.LEFT, padx=(0, 5))

        # Разделитель
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # Кнопка обновления
        btn_refresh = ttk.Button(
            toolbar_frame,
            text="🔄 Обновить",
            command=self.refresh_data,
            width=14
        )
        btn_refresh.pack(side=tk.LEFT, padx=(0, 5))

        # Автообновление (чекбокс)
        cb_auto = ttk.Checkbutton(
            toolbar_frame,
            text="⏱️ Автообновление",
            variable=self.auto_refresh_enabled,
            command=self._toggle_auto_refresh
        )
        cb_auto.pack(side=tk.LEFT, padx=(10, 0))

        # Метка с интервалом
        lbl_interval = ttk.Label(
            toolbar_frame,
            text=f"(каждые {AUTO_REFRESH_INTERVAL_SECONDS} сек)",
            font=("Segoe UI", 9)
        )
        lbl_interval.pack(side=tk.LEFT, padx=(5, 0))

        # Кнопка очистки фильтра (справа)
        btn_clear_filter = ttk.Button(
            toolbar_frame,
            text="🧹 Сбросить фильтр",
            command=self._clear_filter,
            width=14
        )
        btn_clear_filter.pack(side=tk.RIGHT, padx=(5, 0))

        # ===== Поле поиска =====
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="🔍 Поиск:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self._apply_filter())
        entry_search = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        entry_search.pack(side=tk.LEFT, padx=(0, 10))

        # Фильтр по типу записи
        ttk.Label(search_frame, text="Тип:").pack(side=tk.LEFT, padx=(5, 5))

        self.filter_type_var = tk.StringVar(value="Все")
        filter_types = ["Все"] + RECORD_TYPES
        cb_filter_type = ttk.Combobox(
            search_frame,
            textvariable=self.filter_type_var,
            values=filter_types,
            state="readonly",
            width=18
        )
        cb_filter_type.pack(side=tk.LEFT)
        cb_filter_type.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        # ===== Таблица записей (Treeview) =====
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Вертикальная прокрутка
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Горизонтальная прокрутка
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Создаем Treeview
        self.tree = ttk.Treeview(
            table_frame,
            columns=COLUMNS,
            show="headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set,
            selectmode="browse",
            height=18
        )
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Настраиваем скроллы
        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        # Настраиваем колонки
        for col, name, width in zip(COLUMNS, COLUMN_NAMES, [120, 90, 140, 180, 180]):
            self.tree.heading(col, text=name, anchor=tk.W)
            self.tree.column(col, width=width, minwidth=60, anchor=tk.W, stretch=False)

        # Добавляем возможность изменения размера колонок
        # Растягиваем последнюю колонку для заполнения
        self.tree.column("contact", stretch=True)

        # ===== Статусная строка =====
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Готов к работе")
        self.status_label.pack(side=tk.LEFT)

        self.record_count_label = ttk.Label(status_frame, text="Записей: 0")
        self.record_count_label.pack(side=tk.RIGHT)

        self.last_update_label = ttk.Label(
            status_frame,
            text=f"Обновлено: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.last_update_label.pack(side=tk.RIGHT, padx=(0, 15))

    def _setup_bindings(self):
        """Настройка горячих клавиш."""
        self.root.bind("<F5>", lambda e: self.refresh_data())
        self.root.bind("<Control-n>", lambda e: self._add_record())
        self.root.bind("<Control-e>", lambda e: self._edit_record())
        self.root.bind("<Delete>", lambda e: self._delete_record())
        self.root.bind("<Control-f>", lambda e: self.search_var.focus_set())

        # Двойной клик для редактирования
        self.tree.bind("<Double-1>", lambda e: self._edit_record())

    def refresh_data(self):
        """Обновление данных в таблице."""
        try:
            # Получаем все записи из БД
            records = self.db.get_all_records()

            # Очищаем таблицу
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.tree_id_map.clear()

            # Вставляем записи в таблицу
            for record in records:
                # Проверяем, что запись содержит все необходимые поля
                values = (
                    record.get("date", ""),
                    record.get("time", ""),
                    record.get("record_type", ""),
                    record.get("client_name", ""),
                    record.get("contact", ""),
                )
                item_id = self.tree.insert("", tk.END, values=values)
                # Сохраняем ID записи для редактирования/удаления
                self.tree_id_map[item_id] = record.get("id")

            # Обновляем статус
            total = len(records)
            self.record_count_label.config(text=f"Записей: {total}")
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.config(text=f"Обновлено: {now}")
            self.status_label.config(text=f"Данные обновлены ({total} записей)")

            # Применяем текущий фильтр
            self._apply_filter()

        except Exception as e:
            messagebox.showerror(
                "Ошибка обновления",
                f"Не удалось обновить данные:\n\n{e}"
            )
            self.status_label.config(text="Ошибка обновления данных")

    def _apply_filter(self):
        """Применение фильтрации к таблице."""
        search_text = self.search_var.get().strip().lower()
        filter_type = self.filter_type_var.get()

        # Проходим по всем видимым элементам
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            # Проверяем соответствие фильтру
            match = True

            # Фильтр по типу
            if filter_type != "Все" and values[2] != filter_type:
                match = False

            # Поиск по тексту
            if match and search_text:
                # Ищем в дате, времени, типе, имени, контактах
                row_text = " ".join(str(v).lower() for v in values)
                if search_text not in row_text:
                    match = False

            # Показываем/скрываем элемент
            if match:
                self.tree.reattach(item, "", tk.END)
            else:
                self.tree.detach(item)

    def _clear_filter(self):
        """Сброс фильтров и поиска."""
        self.search_var.set("")
        self.filter_type_var.set("Все")
        self._apply_filter()
        self.status_label.config(text="Фильтры сброшены")

    def _get_selected_record_id(self):
        """Получение ID выбранной записи."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбрана ни одна запись.")
            return None
        item_id = selected[0]
        record_id = self.tree_id_map.get(item_id)
        if record_id is None:
            messagebox.showerror("Ошибка", "Не удалось определить ID записи.")
            return None
        return record_id

    def _add_record(self):
        """Добавление новой записи."""
        dialog = RecordDialog(self.root, self.db, mode="add")
        if dialog.result:
            self.refresh_data()
            self.status_label.config(text="Запись успешно добавлена")

    def _edit_record(self):
        """Редактирование выбранной записи."""
        record_id = self._get_selected_record_id()
        if record_id is None:
            return

        # Получаем данные записи
        record = self.db.get_record_by_id(record_id)
        if not record:
            messagebox.showerror("Ошибка", "Запись не найдена в базе данных.")
            return

        dialog = RecordDialog(self.root, self.db, mode="edit", record=record)
        if dialog.result:
            self.refresh_data()
            self.status_label.config(text="Запись успешно обновлена")

    def _delete_record(self):
        """Удаление выбранной записи."""
        record_id = self._get_selected_record_id()
        if record_id is None:
            return

        # Подтверждение удаления
        if not messagebox.askyesno(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить выбранную запись?\n\nЭто действие нельзя отменить."
        ):
            return

        try:
            self.db.delete_record(record_id)
            self.refresh_data()
            self.status_label.config(text="Запись удалена")
        except Exception as e:
            messagebox.showerror(
                "Ошибка удаления",
                f"Не удалось удалить запись:\n\n{e}"
            )

    def _start_auto_refresh(self):
        """Запуск потока автообновления."""
        if self.auto_refresh_running:
            return

        self.auto_refresh_running = True
        self.auto_refresh_thread = threading.Thread(
            target=self._auto_refresh_worker,
            daemon=True
        )
        self.auto_refresh_thread.start()

    def _stop_auto_refresh(self):
        """Остановка потока автообновления."""
        self.auto_refresh_running = False
        if self.auto_refresh_thread:
            self.auto_refresh_thread.join(timeout=1.0)
            self.auto_refresh_thread = None

    def _auto_refresh_worker(self):
        """Рабочий поток автообновления."""
        while self.auto_refresh_running:
            # Проверяем, включено ли автообновление
            if self.auto_refresh_enabled.get():
                # Обновляем в главном потоке
                self.root.after(0, self._safe_refresh)
            # Ждем интервал
            for _ in range(AUTO_REFRESH_INTERVAL_SECONDS):
                if not self.auto_refresh_running:
                    return
                time.sleep(1)

    def _safe_refresh(self):
        """Безопасное обновление (с обработкой ошибок)."""
        try:
            if self.root.winfo_exists():
                self.refresh_data()
        except tk.TclError:
            # Окно закрыто
            self.auto_refresh_running = False
        except Exception as e:
            # Логируем ошибку, но не показываем диалог, чтобы не прерывать работу
            self.status_label.config(text=f"Ошибка автообновления: {e}")

    def _toggle_auto_refresh(self):
        """Переключение автообновления."""
        if self.auto_refresh_enabled.get():
            self.status_label.config(text="Автообновление включено")
        else:
            self.status_label.config(text="Автообновление отключено")

    def run(self):
        """Запуск главного цикла приложения."""
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()

    def _on_closing(self):
        """Обработка закрытия окна."""
        self._stop_auto_refresh()
        self.db.close()
        self.root.destroy()

class RecordDialog:
    """Диалог для добавления/редактирования записи."""

    def __init__(self, parent, db, mode="add", record=None):
        """
        Инициализация диалога.

        Args:
            parent: Родительское окно
            db: Экземпляр DatabaseManager
            mode: "add" или "edit"
            record: Данные записи для редактирования
        """
        self.parent = parent
        self.db = db
        self.mode = mode
        self.record = record or {}
        self.result = False

        # Создаем диалог
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление записи" if mode == "add" else "Редактирование записи")
        self.dialog.geometry("500x380")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.focus_set()

        # Центрируем диалог
        self._center_dialog()

        # Создаем интерфейс
        self._create_widgets()

        # Заполняем данными при редактировании
        if mode == "edit" and record:
            self._populate_fields()

        # Ожидаем закрытия
        self.dialog.wait_window()

    def _center_dialog(self):
        """Центрирование диалога относительно родителя."""
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - w) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")

    def _create_widgets(self):
        """Создание виджетов диалога."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Поля ввода
        fields = [
            ("record_type", "Тип записи", "combobox"),
            ("client_name", "Имя клиента", "entry"),
            ("contact", "Контакты (Телефон)", "entry"),
            ("date", "Дата (ГГГГ-ММ-ДД)", "entry"),
            ("time", "Время (ЧЧ:ММ)", "entry"),
        ]

        self.entries = {}

        for row, (field, label, ftype) in enumerate(fields):
            ttk.Label(main_frame, text=f"{label}:", font=("Segoe UI", 10)).grid(
                row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10)
            )

            if ftype == "combobox":
                var = tk.StringVar()
                combo = ttk.Combobox(
                    main_frame,
                    textvariable=var,
                    values=RECORD_TYPES,
                    state="readonly",
                    width=40
                )
                combo.grid(row=row, column=1, sticky=tk.W, pady=8)
                self.entries[field] = var
                self.entries[f"{field}_widget"] = combo
            else:
                var = tk.StringVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=42)
                entry.grid(row=row, column=1, sticky=tk.W, pady=8)
                self.entries[field] = var

        # Автозаполнение даты и времени
        now = datetime.now()
        if self.mode == "add":
            self.entries["date"].set(now.strftime("%d.%m.%Y"))
            self.entries["time"].set(now.strftime("%H:%M"))

        # Кнопки действий
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        btn_save = ttk.Button(
            btn_frame,
            text="💾 Сохранить",
            command=self._save,
            width=16
        )
        btn_save.pack(side=tk.LEFT, padx=(0, 10))

        btn_cancel = ttk.Button(
            btn_frame,
            text="❌ Отмена",
            command=self.dialog.destroy,
            width=16
        )
        btn_cancel.pack(side=tk.LEFT)

        # Привязываем Enter к сохранению
        self.dialog.bind("<Return>", lambda e: self._save())
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

    def _populate_fields(self):
        """Заполнение полей данными при редактировании."""
        field_map = {
            "record_type": "record_type",
            "client_name": "client_name",
            "contact": "contact",
            "date": "date",
            "time": "time",
        }
        for field, db_field in field_map.items():
            if db_field in self.record:
                self.entries[field].set(self.record[db_field] or "")

    def _save(self):
        """Сохранение записи."""
        # Сбор данных
        data = {
            "record_type": self.entries["record_type"].get().strip(),
            "client_name": self.entries["client_name"].get().strip(),
            "contact": self.entries["contact"].get().strip(),
            "date": self.entries["date"].get().strip(),
            "time": self.entries["time"].get().strip(),
        }

        # Валидация
        errors = []
        if not data["record_type"]:
            errors.append("Выберите тип записи")
        if not data["client_name"]:
            errors.append("Введите имя клиента")
        if not data["contact"]:
            errors.append("Введите контакты (телефон)")
        if not data["date"]:
            errors.append("Введите дату")
        if not data["time"]:
            errors.append("Введите время")

        # Проверка формата даты
        if data["date"]:
            try:
                datetime.strptime(data["date"], "%d.%m.%Y")
            except ValueError:
                errors.append("Неверный формат даты (используйте ДД.ММ.ГГГГ)")

        # Проверка формата времени
        if data["time"]:
            try:
                datetime.strptime(data["time"], "%H:%M")
            except ValueError:
                errors.append("Неверный формат времени (используйте ЧЧ:ММ)")

        if errors:
            messagebox.showerror("Ошибка валидации", "\n".join(errors))
            return

        try:
            if self.mode == "add":
                self.db.add_booking(data["client_name"], data["contact"], data["date"], data["time"], data["record_type"], "db")
            else:
                record_id = self.record.get("id")
                if record_id:
                    self.db.update_record(record_id, data)
                else:
                    raise ValueError("Не найден ID записи")

            self.result = True
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror(
                "Ошибка сохранения",
                f"Не удалось сохранить запись:\n\n{e}"
            )
