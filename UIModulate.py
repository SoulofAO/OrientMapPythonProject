import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLineEdit, QPushButton,
    QListWidget, QMessageBox, QScrollArea, QFormLayout, QSpinBox, QCheckBox, QHBoxLayout, QDoubleSpinBox, QLabel, QListWidgetItem, QComboBox, QShortcut
)
from PyQt5.QtGui import QKeySequence


class UArrayWidget(QWidget):
    def __init__(self, settings_class, settings_list, font_size = 12.0):
        super().__init__()
        self.settings_class = settings_class
        self.param_widgets = []
        self.settings_list = settings_list
        self.unique_values = False
        self.font_size = font_size
        self.initUI()

        for setting in settings_list:
            self.create_new_setting(setting)

    def initUI(self):
        layout = QVBoxLayout()

        # Список для отображения элементов Settings
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        self.scroll_layout = QFormLayout(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)

        layout.addWidget(scroll_area)
        # Поля для редактирования
        self.generate_settings(self.scroll_layout)

        # Кнопки для управления
        button_layout = QHBoxLayout()

        add_button = QPushButton("Add")
        add_button.clicked.connect(self.add_setting)
        button_layout.addWidget(add_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.bind_edit_settings)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete_setting)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.list_widget.currentRowChanged.connect(self.load_settings)


    def update_options(self):
        settings = self.settings_class()
        for attr_name in settings.ui_show_tag:
            if not attr_name.startswith('__') and not callable(getattr(settings, attr_name)):
                value = getattr(settings, attr_name)
                find_setting = self.find_settings_by_name(attr_name)
                if find_setting:
                    if (isinstance(value, str) and hasattr(settings, str(attr_name + "_options"))):
                        options = getattr(settings, str(attr_name + "_options"))
                        find_setting.addItems(options)

    def generate_settings(self, layout):
        settings = self.settings_class()

        # Очистка текущих виджетов
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        # Генерация виджетов на основе параметров
        for attr_name in settings.ui_show_tag:
            if not attr_name.startswith('__') and not callable(getattr(settings, attr_name)):
                value = getattr(settings, attr_name)
                if isinstance(value, bool):
                    self.create_checkbox(layout, attr_name, value)
                elif (isinstance(value, str) and hasattr(settings, str(attr_name+"_options"))):
                    options = getattr(settings, str(attr_name+"_options"))
                    if(hasattr(settings, str("update_"+attr_name+"_options_delegate"))):
                        update_delegate = getattr(settings, str("update_"+attr_name+"_options_delegate"))
                        update_delegate.add(self.update_options)
                    self.create_options(layout,attr_name,value, options)
                elif isinstance(value, int):
                    self.create_spinbox(layout, attr_name, value)
                elif isinstance(value, float):
                    self.create_double_spinbox(layout, attr_name, value)
                elif isinstance(value, str):  # Для строковых параметров
                    self.create_lineedit(layout, attr_name, value)


    def find_settings_by_name(self, attr_name):
        for param_widget in self.param_widgets:
            if param_widget[0] == attr_name:
                return param_widget[1]
        return None

    def load_settings(self, current_row=-1):
        current_row = self.list_widget.currentRow()
        if(current_row>=0 and len(self.settings_list)>current_row):
            settings = self.settings_list[current_row]
            for attr_name in settings.ui_show_tag:
                if not attr_name.startswith('__') and not callable(getattr(settings, attr_name)):
                    value = getattr(settings, attr_name)
                    find_setting = self.find_settings_by_name(attr_name)
                    if find_setting:
                        if isinstance(value, bool):
                            find_setting.setChecked(value)
                        elif (isinstance(value, str) and hasattr(settings, str(attr_name + "_options"))):
                            options = getattr(settings, str(attr_name + "_options"))
                            find_setting.clear()
                            find_setting.addItems(options)
                            if(value in options):
                                find_setting.setCurrentIndex(options.index(value))
                            else:
                                find_setting.setCurrentIndex(options.index("ErrorType"))
                        elif isinstance(value, int):
                            find_setting.setValue(value)
                        elif isinstance(value, float):
                            find_setting.setValue(value)
                        elif isinstance(value, str):  # Для строковых параметров
                            find_setting.setText(value)

    def check_parametrs_focus(self):
        for child in self.param_widgets:
            if child[1].hasFocus():
                return True
        return False

    def create_new_setting(self, new_setting):
        # Создаем кастомный виджет для отображения в ListWidget
        item_widget = QWidget()
        item_layout = QVBoxLayout()

        name_label = QLabel(f"{new_setting}")  # Пример отображения одного из значений

        name_label.setWordWrap(True)

        name_label.setStyleSheet(f"font-size: {self.font_size}px;")

        item_layout.addWidget(name_label)
        item_widget.setLayout(item_layout)

        list_item = QListWidgetItem(self.list_widget)
        list_item.setSizeHint(item_widget.sizeHint())
        self.list_widget.setItemWidget(list_item, item_widget)

    def add_setting(self):
        # Создаем новый объект настройки
        new_setting = self.settings_class()
        self.create_new_setting(new_setting)

        self.settings_list.append(new_setting)
        self.edit_setting(new_setting)
        self.clear_inputs()

    def update_settings(self, settings=None):
        # Если settings не переданы, используем текущий выбранный элемент
        if settings is None:
            current_row = self.list_widget.currentRow()
            if current_row < 0:
                return
            settings = self.settings_list[current_row]

        index = self.settings_list.index(settings)
        list_item = self.list_widget.item(index)

        if list_item:
            # Получаем текущий виджет, связанный с элементом
            item_widget = self.list_widget.itemWidget(list_item)

            if item_widget:
                # Очищаем текущий layout виджета
                for i in reversed(range(item_widget.layout().count())):
                    widget_to_remove = item_widget.layout().itemAt(i).widget()
                    if widget_to_remove:
                        widget_to_remove.deleteLater()

                # Обновляем виджет новыми значениями
                new_name_label = QLabel(f"{settings}")  # Пример обновления строки
                new_name_label.setWordWrap(True)
                new_name_label.setStyleSheet(f"font-size: {self.font_size}px;")

                # Добавляем обновленный QLabel в layout виджета
                item_widget.layout().addWidget(new_name_label)

                # Обновляем размер элемента
                list_item.setSizeHint(item_widget.sizeHint())

    def bind_edit_settings(self):
        self.edit_setting()

    def edit_setting(self, settings=None):
        if settings is None:
            current_row = self.list_widget.currentRow()
            settings = self.settings_list[current_row]
        for attr_name in settings.ui_show_tag:
            widget = self.find_settings_by_name(attr_name)
            if widget:
                if isinstance(widget, QSpinBox):
                    setattr(settings, attr_name, widget.value())
                elif isinstance(widget, QDoubleSpinBox):
                    setattr(settings, attr_name, widget.value())
                elif isinstance(widget, QCheckBox):
                    setattr(settings, attr_name, widget.isChecked())
                elif isinstance(widget, QLineEdit):  # Для строковых параметров
                    setattr(settings, attr_name, widget.text())
                elif isinstance(widget, QComboBox):
                    setattr(settings, attr_name, widget.currentText())


        self.update_settings(settings)

    def delete_setting(self):
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Delete Error", "Select an item to delete.")
            return

        del self.settings_list[current_row]
        self.list_widget.takeItem(current_row)
        self.clear_inputs()  # Очистка полей ввода после удаления

    def key_delete_setting(self):
        if(self.list_widget.hasFocus()):
            self.delete_setting()


    def clear_inputs(self):
        pass

    def apply_key_event(self):
        if(self.check_parametrs_focus()):
            current_row = self.list_widget.currentRow()
            if current_row >= 0:
                self.edit_setting()
            else:
                self.add_setting()


    def create_spinbox(self, layout, attr_name, value):
        spin_box = QSpinBox()
        spin_box.setMinimum(-100000)
        spin_box.setMaximum(100000)
        spin_box.setValue(value)
        layout.addRow(attr_name, spin_box)
        self.param_widgets.append([attr_name, spin_box])

    def create_double_spinbox(self, layout, attr_name, value):
        """Создание ввода числа для вещественных параметров."""
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(2)  # Задаем точность до двух знаков после запятой
        spin_box.setMinimum(-100000.0)
        spin_box.setMaximum(100000.0)  # Изменяй максимальное значение по необходимости
        spin_box.setSingleStep(0.01)  # Шаг изменения значения
        spin_box.setValue(value)
        self.param_widgets.append([attr_name, spin_box])
        layout.addRow(attr_name, spin_box)

    def create_checkbox(self, layout, attr_name, value):
        """Создание чекбокса для булевых параметров."""
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        self.param_widgets.append([attr_name, checkbox])
        layout.addRow(attr_name, checkbox)

    def create_lineedit(self, layout, attr_name, value):
        """Создание текстового поля для строковых параметров."""
        line_edit = QLineEdit()
        line_edit.setText(value)  # Устанавливаем начальное значение
        self.param_widgets.append([attr_name, line_edit])
        layout.addRow(attr_name, line_edit)

    def create_options(self, layout, attr_name, value, options):
        """Создание ввода числа для вещественных параметров."""
        combobox_directions = QComboBox()
        combobox_directions.addItems(options)
        if value in options:
            combobox_directions.setCurrentIndex(options.index(value))
        self.param_widgets.append([attr_name, combobox_directions])
        layout.addRow(attr_name, combobox_directions)




