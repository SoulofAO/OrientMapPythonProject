import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QHBoxLayout,
    QMessageBox,
    QLineEdit,
    QLabel,
    QSpinBox,
    QScrollArea,
    QFormLayout,
    QCheckBox,
    QDoubleSpinBox
)


class Settings:
    counter = -1

    def __init__(self):
        Settings.counter = Settings.counter + 1
        self.name = f"{Settings.counter}"
        self.value = 0
        self.use_fix_border_lines = False
        self.ui_show_tag = ["value", "use_fix_border_lines"]

    def __str__(self):
        string = ""
        for attr_name in self.ui_show_tag:
            string = string + ", " + attr_name + " = " + str(getattr(self, attr_name))
        return f"{self.name}: {string}"


class UArrayWidget(QWidget):
    def __init__(self, settings_class):
        super().__init__()
        self.settings_class = settings_class
        self.param_widgets = []
        self.settings_list = []
        self.initUI()

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

    def generate_settings(self, layout):
        settings = self.settings_class()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for attr_name in settings.ui_show_tag:
            if not attr_name.startswith('__') and not callable(getattr(settings, attr_name)):
                value = getattr(settings, attr_name)
                if isinstance(value, bool):
                    self.create_checkbox(layout, attr_name, value)
                elif isinstance(value, int):
                    self.create_spinbox(layout, attr_name, value)
                elif isinstance(value, float):
                    self.create_double_spinbox(layout, attr_name, value)

    def find_settings_by_name(self, attr_name):
        for param_widget in self.param_widgets:
            if param_widget[0] == attr_name:
                return param_widget[1]
        return None

    def load_settings(self, current_row = -1):
        current_row = self.list_widget.currentRow()
        settings = self.settings_list[current_row]
        for attr_name in settings.ui_show_tag:
            if not attr_name.startswith('__') and not callable(getattr(settings, attr_name)):
                value = getattr(settings, attr_name)
                find_setting = self.find_settings_by_name(attr_name)
                print(find_setting, value)
                if (find_setting):
                    if isinstance(value, bool):
                        find_setting.setChecked(value)
                    elif isinstance(value, int):
                        find_setting.setValue(value)
                        print(value)
                    elif isinstance(value, float):
                        find_setting.setValue(value)

    def add_setting(self):
        new_setting = self.settings_class()
        self.settings_list.append(new_setting)
        self.list_widget.addItem(str(new_setting))
        self.edit_setting(new_setting)
        self.clear_inputs()

    def update_settings(self, settings = None):
        if settings is None:
            current_row = self.list_widget.currentRow()
            if current_row < 0:
                return
            settings = self.settings_list[current_row]
        index = self.settings_list.index(settings)
        list_item = self.list_widget.item(index)
        if list_item:
            list_item.setText(str(settings))

    def bind_edit_settings(self):
        self.edit_setting()

    def edit_setting(self, settings = None):
        if(settings==None):
            current_row = self.list_widget.currentRow()
            settings = self.settings_list[current_row]
        for attr_name in settings.ui_show_tag:
            widget = self.find_settings_by_name(attr_name)
            if(widget):
                if isinstance(widget, QSpinBox):
                    setattr(settings, attr_name, widget.value())
                elif isinstance(widget, QDoubleSpinBox):  # Заменяем QSlider на QDoubleSpinBox
                    setattr(settings, attr_name, widget.value())
                elif isinstance(widget, QCheckBox):
                    setattr(settings, attr_name, widget.isChecked())
        self.update_settings(settings)

    def delete_setting(self):
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Delete Error", "Select an item to delete.")
            return

        del self.settings_list[current_row]
        self.list_widget.takeItem(current_row)
        self.clear_inputs()  # Очистка полей ввода после удаления

    def clear_inputs(self):
        pass

    def create_spinbox(self, layout, attr_name, value):
        spin_box = QSpinBox()
        spin_box.setMinimum(0)
        spin_box.setMaximum(100000)
        spin_box.setValue(value)
        layout.addRow(attr_name, spin_box)
        self.param_widgets.append([attr_name, spin_box])

    def create_double_spinbox(self, layout, attr_name, value):
        """Создание ввода числа для вещественных параметров."""
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(2)  # Задаем точность до двух знаков после запятой
        spin_box.setMinimum(0.0)
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

