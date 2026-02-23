# DEV BRANCH - разделители будут добавлены здесь
# universal_parser.py
import os
from datetime import datetime
import os
from datetime import datetime
import sys
import os
import json
import webbrowser
import re
from datetime import datetime

import pandas as pd
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import QFont

from core.parser_engine import ParserEngine


class Field:
    def __init__(self, name, data_type, selector=None, separator=None):
        self.name = name
        self.data_type = data_type  # text, number, list
        self.selector = selector
        self.separator = separator  # 👈 новый параметр
        self.test_result = None


class FieldWidget(QGroupBox):
    def __init__(self, field, main_window, parent=None):
        super().__init__(parent)
        self.field = field
        self.main_window = main_window
        self.setTitle(field.name)

        layout = QVBoxLayout()

        # Статус
        self.status_label = QLabel("⚪ Не выбрано")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)

        # Тип данных
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(['Текст', 'Число', 'Список'])
        self.type_combo.setCurrentText(self._get_type_name(field.data_type))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Селектор
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Селектор:"))
        self.selector_edit = QLineEdit()
        if field.selector:
            self.selector_edit.setText(field.selector)
        self.selector_edit.setPlaceholderText("Например: h1, .ingredient, #calories")
        self.selector_edit.textChanged.connect(self.on_selector_changed)
        selector_layout.addWidget(self.selector_edit)
        layout.addLayout(selector_layout)

        # Разделитель (только для списков)
        self.separator_label = QLabel("Разделитель:")
        self.separator_combo = QComboBox()

        # Все возможные разделители
        separators = [
            'Запятая с пробелом (, )',
            'Вертикальная черта (|)',
            'Обратная косая черта (\\)',
            'Точка с запятой (;)',
            'Пробел ( )',
            'Точка (.)',
            'Перенос строки',
            'Нумерация (1., 2.)',
            'Буквы (а., б.)',
            'Буквы (a., b.)',
            'Свой разделитель'
        ]

        self.separator_combo.addItems(separators)
        self.separator_combo.currentTextChanged.connect(self.on_separator_changed)

        # Поле для своего разделителя (изначально скрыто)
        self.custom_separator = QLineEdit()
        self.custom_separator.setPlaceholderText("Введите свой разделитель...")
        self.custom_separator.hide()
        self.custom_separator.textChanged.connect(self.on_custom_separator_changed)

        # Добавляем в layout
        layout.addWidget(self.separator_label)
        layout.addWidget(self.separator_combo)
        layout.addWidget(self.custom_separator)

        # Скрываем всё это для не-списков
        if field.data_type != 'list':
            self.separator_label.hide()
            self.separator_combo.hide()
            self.custom_separator.hide()

        # Кнопка теста
        self.test_btn = QPushButton("🔍 Проверить поле")
        self.test_btn.clicked.connect(self.test_field)
        self.test_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        layout.addWidget(self.test_btn)

        # Результат теста
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(80)
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Результат проверки появится здесь...")
        layout.addWidget(self.result_text)

        self.setLayout(layout)

    def on_separator_changed(self, text):
        """Обработка выбора разделителя"""
        if text == 'Свой разделитель':
            self.custom_separator.show()
        else:
            self.custom_separator.hide()
            # Преобразуем текст в реальный разделитель
            separator_map = {
                'Запятая с пробелом (, )': ', ',
                'Вертикальная черта (|)': ' | ',
                'Обратная косая черта (\\)': ' \\ ',
                'Точка с запятой (;)': '; ',
                'Пробел ( )': ' ',
                'Точка (.)': '. ',
                'Перенос строки': '\n',
                'Нумерация (1., 2.)': 'numbered',
                'Буквы (а., б.)': 'cyrillic',
                'Буквы (a., b.)': 'latin'
            }
            self.field.separator = separator_map.get(text, ', ')

    def on_custom_separator_changed(self, text):
        """Свой разделитель"""
        self.field.separator = text

    def _get_type_name(self, data_type):
        types = {'text': 'Текст', 'number': 'Число', 'list': 'Список'}
        return types.get(data_type, 'Текст')

    def _get_type_code(self, type_name):
        codes = {'Текст': 'text', 'Число': 'number', 'Список': 'list'}
        return codes.get(type_name, 'text')

    def on_type_changed(self, type_name):
        self.field.data_type = self._get_type_code(type_name)
        self.status_label.setText("⚡ Тип изменён")
        self.status_label.setStyleSheet("color: #FF9800;")

    def on_selector_changed(self, text):
        self.field.selector = text
        self.status_label.setText("✏️ Селектор введён")
        self.status_label.setStyleSheet("color: #2196F3;")

    def test_field(self):
        if not self.field.selector:
            QMessageBox.warning(self, "Ошибка", "Сначала введите селектор!")
            return
        self.main_window.test_single_field(self)

    def update_test_result(self, result_text, is_success=True):
        self.result_text.setText(result_text)
        if is_success:
            self.result_text.setStyleSheet("color: #2e7d32; background-color: #e8f5e8;")
            self.status_label.setText("✅ Работает")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.result_text.setStyleSheet("color: #c62828; background-color: #ffebee;")
            self.status_label.setText("❌ Не работает")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")


class ConstructorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.fields = []
        self.current_soup = None
        self.parser = ParserEngine(use_selenium=False)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Universal Parser Studio")
        self.setGeometry(100, 100, 800, 900)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Верхняя панель с URL
        url_group = QGroupBox("🌐 Страница для парсинга")
        url_layout = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setText("https://eda.rambler.ru/recepty/salaty/cezar-114535")
        self.url_input.setPlaceholderText("Вставьте URL страницы...")
        url_layout.addWidget(self.url_input)

        self.load_btn = QPushButton("📥 Загрузить в парсер")
        self.load_btn.clicked.connect(self.load_url)
        self.load_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 15px;")
        url_layout.addWidget(self.load_btn)

        self.open_btn = QPushButton("🌐 Открыть в браузере")
        self.open_btn.clicked.connect(self.open_in_browser)
        self.open_btn.setStyleSheet("background-color: #9e9e9e; color: white; padding: 8px 15px;")
        url_layout.addWidget(self.open_btn)

        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

        # Инструкция
        instr = QLabel(
            "📌 Как работать:\n"
            "1. Вставьте URL и нажмите 'Загрузить в парсер'\n"
            "2. Откройте эту же страницу в браузере (кнопка выше)\n"
            "3. Нажмите F12, найдите нужные элементы и скопируйте их селекторы\n"
            "4. Вставьте селекторы в поля ниже и нажмите 'Проверить поле'\n"
            "5. Если всё работает - сохраняйте шаблон!"
        )
        instr.setStyleSheet("background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 5px;")
        instr.setWordWrap(True)
        main_layout.addWidget(instr)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.quick_start_btn = QPushButton("⚡ Быстрый старт")
        self.quick_start_btn.clicked.connect(self.quick_start)
        self.quick_start_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        buttons_layout.addWidget(self.quick_start_btn)

        self.add_parser_btn = QPushButton("➕ Добавить парсер")
        self.add_parser_btn.clicked.connect(self.add_parser)
        self.add_parser_btn.setStyleSheet("background-color: #FF6B6B; color: white; padding: 8px;")
        buttons_layout.addWidget(self.add_parser_btn)

        self.open_parser_btn = QPushButton("📂 Открыть парсер")
        self.open_parser_btn.clicked.connect(self.open_parser)
        self.open_parser_btn.setStyleSheet("background-color: #4ECDC4; color: white; padding: 8px;")
        buttons_layout.addWidget(self.open_parser_btn)

        self.add_btn = QPushButton("➕ Добавить поле")
        self.add_btn.clicked.connect(self.add_field_dialog)
        self.add_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 8px;")
        buttons_layout.addWidget(self.add_btn)

        self.test_all_btn = QPushButton("🧪 Проверить все поля")
        self.test_all_btn.clicked.connect(self.test_all_fields)
        self.test_all_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        buttons_layout.addWidget(self.test_all_btn)

        self.export_btn = QPushButton("📊 Экспорт в Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        self.export_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        buttons_layout.addWidget(self.export_btn)

        self.batch_btn = QPushButton("📦 Пакет из Excel")
        self.batch_btn.clicked.connect(self.batch_from_excel)
        self.batch_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px;")
        buttons_layout.addWidget(self.batch_btn)

        self.save_btn = QPushButton("💾 Сохранить шаблон")
        self.save_btn.clicked.connect(self.save_template)
        self.save_btn.setStyleSheet("background-color: #27ae60; color: white; padding: 8px;")
        buttons_layout.addWidget(self.save_btn)

        self.load_template_btn = QPushButton("📂 Загрузить шаблон")
        self.load_template_btn.clicked.connect(self.load_template)
        self.load_template_btn.setStyleSheet("background-color: #9C27B0; color: white; padding: 8px;")
        buttons_layout.addWidget(self.load_template_btn)

        main_layout.addLayout(buttons_layout)

        # Область с полями
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.fields_container = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.addStretch()
        scroll.setWidget(self.fields_container)
        main_layout.addWidget(scroll)

        # Статус парсера
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

        # Поля по умолчанию
        self.add_field("Название", "text")
        self.add_field("Ингредиенты", "list")
        self.add_field("Калории", "number")
        self.add_field("Шаги", "list")

    def open_in_browser(self):
        url = self.url_input.text()
        if url:
            webbrowser.open(url)

    def quick_start(self):
        """Быстрый старт с готовыми полями"""
        reply = QMessageBox.question(self, "Быстрый старт",
                                     "Создать новый парсер с полями по умолчанию?\n"
                                     "(Название, Ингредиенты, Калории, Шаги)",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Очищаем поля
            for field in self.fields[:]:
                self.remove_field(field)

            # Добавляем поля по умолчанию
            self.add_field("Название", "text")
            self.add_field("Ингредиенты", "list")
            self.add_field("Калории", "number")
            self.add_field("Шаги", "list")

            self.status_bar.showMessage("✅ Быстрый старт: созданы поля по умолчанию")
            
    def add_parser(self):
        """Создать новый чистый парсер"""
        # Спрашиваем, что делать со старым
        buttons = QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        reply = QMessageBox.question(self, "Новый парсер",
                                     "Сохранить текущий шаблон перед созданием нового?",
                                     buttons)

        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            self.save_template()

        # Очищаем все поля
        for field in self.fields[:]:
            self.remove_field(field)

        # НЕ добавляем поля по умолчанию - только одно приветственное сообщение
        self.status_bar.showMessage("✨ Новый пустой парсер создан. Добавьте поля через кнопку '➕ Добавить поле'")

        # Показываем подсказку
        QMessageBox.information(self, "Новый парсер",
                                "Создан пустой парсер.\n\n"
                                "Теперь вы можете:\n"
                                "1. Нажать '➕ Добавить поле' для создания нужных полей\n"
                                "2. Ввести селекторы вручную\n"
                                "3. Настроить разделители для списков\n"
                                "4. Сохранить шаблон")

    def open_parser(self):
        """Открыть список сохранённых парсеров"""
        # Спрашиваем папку с шаблонами
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        # Получаем список JSON файлов
        templates = [f for f in os.listdir(templates_dir) if f.endswith('.json')]

        if not templates:
            QMessageBox.information(self, "Нет шаблонов",
                                    "У вас пока нет сохранённых шаблонов.\n"
                                    "Создайте новый и сохраните его!")
            return

        # Создаём диалог выбора
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите шаблон")
        layout = QVBoxLayout()

        list_widget = QListWidget()
        list_widget.addItems(templates)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)

        if dialog.exec() == QDialog.Accepted:
            if list_widget.currentItem():
                template_name = list_widget.currentItem().text()
                template_path = os.path.join(templates_dir, template_name)
                self.load_template(template_path)  # используем существующий метод load_template

    def add_field(self, name, data_type):
        field = Field(name, data_type)
        widget = FieldWidget(field, self)
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, widget)
        self.fields.append(field)
        return widget

    def add_field_dialog(self):
        name, ok = QInputDialog.getText(self, "Новое поле", "Введите название поля:")
        if ok and name:
            type_dialog = QDialog(self)
            type_dialog.setWindowTitle("Тип поля")
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Выберите тип для '{name}':"))

            type_combo = QComboBox()
            type_combo.addItems(['Текст', 'Число', 'Список'])
            layout.addWidget(type_combo)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(type_dialog.accept)
            buttons.rejected.connect(type_dialog.reject)
            layout.addWidget(buttons)

            type_dialog.setLayout(layout)

            if type_dialog.exec() == QDialog.Accepted:
                type_name = type_combo.currentText()
                type_map = {'Текст': 'text', 'Число': 'number', 'Список': 'list'}
                self.add_field(name, type_map[type_name])

    def load_url(self):
        url = self.url_input.text()
        if url:
            self.status_bar.showMessage(f"Загружаю {url}...")
            self.current_soup = self.parser.load_from_url(url)
            if self.current_soup:
                self.status_bar.showMessage(f"✅ Страница загружена: {url}")
                QMessageBox.information(self, "Успех", "Страница загружена в парсер!\nМожно тестировать поля.")
            else:
                self.status_bar.showMessage("❌ Ошибка загрузки")
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить страницу")

    def test_single_field(self, widget):
        if not self.current_soup:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите страницу!")
            return

        selector = widget.field.selector
        field_type = widget.field.data_type

        elements = self.current_soup.select(selector)

        if not elements:
            widget.update_test_result("❌ Элемент не найден", False)
            return

        if field_type == 'list':
            values = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
            if values:
                preview = "\n".join([f"  {i + 1}. {v[:50]}" for i, v in enumerate(values[:3])])
                if len(values) > 3:
                    preview += f"\n  ... и ещё {len(values) - 3}"

                # Показываем как будет в Excel с выбранным разделителем
                separator = widget.field.separator or ' | '

                if separator == 'numbered':
                    # Нумерация 1., 2., 3.
                    excel_preview = ' '.join([f"{i + 1}. {v}" for i, v in enumerate(values[:3])])
                elif separator == 'cyrillic':
                    # Буквы а., б., в.
                    cyrillic = ['а.', 'б.', 'в.', 'г.', 'д.', 'е.']
                    excel_preview = ' '.join([f"{cyrillic[i]} {v}" for i, v in enumerate(values[:3])])
                elif separator == 'latin':
                    # Буквы a., b., c.
                    latin = ['a.', 'b.', 'c.', 'd.', 'e.', 'f.']
                    excel_preview = ' '.join([f"{latin[i]} {v}" for i, v in enumerate(values[:3])])
                else:
                    excel_preview = separator.join(values[:3])

                if len(values) > 3:
                    excel_preview += f"{separator}..."

                widget.update_test_result(
                    f"✅ Найдено {len(values)} элементов:\n{preview}\n\n📊 В Excel: {excel_preview}",
                    True
                )
            else:
                widget.update_test_result("❌ Элементы найдены, но текст пуст", False)

        elif field_type == 'number':
            text = elements[0].get_text(strip=True)
            nums = re.findall(r'\d+', text)
            if nums:
                widget.update_test_result(f"✅ Число: {nums[0]} (из текста: {text})", True)
            else:
                widget.update_test_result(f"⚠️ Текст: {text[:50]} (не число)", False)

        else:  # text
            text = elements[0].get_text(strip=True)
            widget.update_test_result(f"✅ Текст: {text[:100]}", True)

    def test_all_fields(self):
        if not self.current_soup:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите страницу!")
            return

        results = []
        success_count = 0
        total_with_selector = 0

        for field in self.fields:
            if field.selector:
                total_with_selector += 1
                elements = self.current_soup.select(field.selector)
                if elements:
                    if field.data_type == 'list':
                        count = len([e for e in elements if e.get_text(strip=True)])
                        results.append(f"✅ {field.name}: {count} эл.")
                        success_count += 1
                    else:
                        text = elements[0].get_text(strip=True)[:50]
                        results.append(f"✅ {field.name}: {text}")
                        success_count += 1
                else:
                    results.append(f"❌ {field.name}: не найдено")

        msg = "📊 Результаты проверки:\n\n" + "\n".join(results)
        msg += f"\n\n✅ Работает: {success_count} из {total_with_selector}"

        QMessageBox.information(self, "Результаты теста", msg)

    def export_to_excel(self):
        """Экспорт всех полей в Excel"""
        if not self.current_soup:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите страницу!")
            return

        from core.mapping_engine import MappingEngine

        # Собираем данные
        data = {}
        for field in self.fields:
            if field.selector:
                elements = self.current_soup.select(field.selector)
                if elements:
                    if field.data_type == 'list':
                        values = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
                        data[field.name] = ' | '.join(values)
                    elif field.data_type == 'number':
                        text = elements[0].get_text(strip=True)
                        nums = re.findall(r'\d+', text)
                        data[field.name] = nums[0] if nums else text
                    else:
                        data[field.name] = elements[0].get_text(strip=True)
                else:
                    data[field.name] = ''

        # Сохраняем в Excel
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить как Excel", "", "Excel Files (*.xlsx)")
        if filename:
            mapping = MappingEngine()
            mapping.create_excel(filename, "Рецепты", list(data.keys()))
            mapping.append_row(filename, "Рецепты", data)
            QMessageBox.information(self, "Успех", f"Данные сохранены в {filename}")

    def batch_from_excel(self):
        """Парсинг списка URL из Excel"""
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите Excel с URL", "", "Excel Files (*.xlsx)")
        if not filename:
            return

        # Читаем Excel
        df = pd.read_excel(filename)

        # Ищем колонку с URL
        columns = df.columns.tolist()
        col, ok = QInputDialog.getItem(self, "Выберите колонку", "В какой колонке ссылки?", columns, 0, False)
        if not ok:
            return

        urls = df[col].tolist()

        # Спрашиваем куда сохранить результат
        result_file, _ = QFileDialog.getSaveFileName(self, "Сохранить результат", "", "Excel Files (*.xlsx)")
        if not result_file:
            return

        # Создаём парсер и маппинг
        from core.mapping_engine import MappingEngine
        parser = ParserEngine(use_selenium=False)
        mapping = MappingEngine()

        # Создаём результирующий Excel с колонками из полей
        columns = [f.name for f in self.fields if f.selector]
        mapping.create_excel(result_file, "Рецепты", columns)

        # Обрабатываем каждый URL
        success = 0
        for i, url in enumerate(urls):
            self.status_bar.showMessage(f"Обрабатываю {i + 1}/{len(urls)}: {url[:50]}...")
            QApplication.processEvents()

            soup = parser.load_from_url(url)
            if soup:
                data = {}
                for field in self.fields:
                    if field.selector:
                        elements = soup.select(field.selector)
                        if elements:
                            if field.data_type == 'list':
                                values = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
                                data[field.name] = ' | '.join(values)
                            elif field.data_type == 'number':
                                text = elements[0].get_text(strip=True)
                                nums = re.findall(r'\d+', text)
                                data[field.name] = nums[0] if nums else text
                            else:
                                data[field.name] = elements[0].get_text(strip=True)
                        else:
                            data[field.name] = ''

                mapping.append_row(result_file, "Рецепты", data)
                success += 1

        self.status_bar.showMessage(f"Готово! Обработано {success} из {len(urls)}")
        QMessageBox.information(self, "Успех",
                                f"Обработано {success} из {len(urls)} рецептов\nРезультат в {result_file}")

    def save_template(self):
        template = {
            'url': self.url_input.text(),
            'fields': {}
        }

        for field in self.fields:
            if field.selector:
                template['fields'][field.name] = {
                    'type': field.data_type,
                    'selector': field.selector
                }

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить шаблон", "", "JSON Files (*.json)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Успех", f"✅ Шаблон сохранён!\nПоля: {len(template['fields'])}")

        def save_template(self):
            """Сохранить шаблон в JSON"""
            # Создаём папку templates если её нет
            templates_dir = "templates"
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)

            # Предлагаем имя файла
            default_name = "template_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            default_path = os.path.join(templates_dir, default_name)

            filename, _ = QFileDialog.getSaveFileName(self, "Сохранить шаблон",
                                                      default_path, "JSON Files (*.json)")
            if filename:
                template = {
                    'url': self.url_input.text(),
                    'fields': {}
                }

                for field in self.fields:
                    if field.selector:
                        template['fields'][field.name] = {
                            'type': field.data_type,
                            'selector': field.selector,
                            'separator': field.separator if field.data_type == 'list' else None
                        }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)

                QMessageBox.information(self, "Успех", f"✅ Шаблон сохранён!\nПоля: {len(template['fields'])}")

    def load_template(self):
        """Загрузить шаблон из JSON файла"""
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить шаблон", "", "JSON Files (*.json)")
        if not filename:
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                template = json.load(f)

            # Очищаем текущие поля
            for field in self.fields[:]:  # Копируем список, чтобы безопасно удалять
                self.remove_field(field)

            # Устанавливаем URL
            if 'url' in template:
                self.url_input.setText(template['url'])

            # Загружаем поля
            if 'fields' in template:
                for field_name, field_config in template['fields'].items():
                    data_type = field_config.get('type', 'text')
                    selector = field_config.get('selector', '')
                    self.add_field_with_selector(field_name, data_type, selector)

            QMessageBox.information(self, "Успех", f"✅ Шаблон загружен!\nПоля: {len(template.get('fields', {}))}")

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить шаблон:\n{str(e)}")

    def remove_field(self, field):
        """Удалить поле"""
        # Находим виджет для этого поля
        for i in range(self.fields_layout.count()):
            item = self.fields_layout.itemAt(i)
            if item and item.widget() and hasattr(item.widget(), 'field') and item.widget().field == field:
                widget = item.widget()
                self.fields_layout.removeWidget(widget)
                widget.deleteLater()
                self.fields.remove(field)
                break

    def add_field_with_selector(self, name, data_type, selector):
        """Добавить поле с готовым селектором"""
        field = Field(name, data_type, selector)
        widget = FieldWidget(field, self)
        widget.selector_edit.setText(selector)
        self.fields_layout.insertWidget(self.fields_layout.count() - 1, widget)
        self.fields.append(field)
        return widget


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ConstructorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()