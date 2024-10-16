import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QSlider, QVBoxLayout, QCheckBox,
    QPushButton, QHBoxLayout, QFormLayout, QSpinBox, QFileDialog, QScrollArea, QDoubleSpinBox, QComboBox, QTreeWidget, QTreeWidgetItem, QProgressBar, QShortcut, QLineEdit
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import PIL.ImageQt as ImageQt
import helper_functions
import json
import os
from HeightmapGenerator import UHeightMapGenerator, UFixingLinesSettings, UAvailibleParceLineSettings
import line
from PyQt5.QtGui import QColor
import UIModulate
from playsound import playsound

class UHeightmapGenerationWarperThread(QThread):
    def __init__(self):
        super().__init__()
        self.settings = None

    def set_heightmap_generator(self, heightmap_generator):
        self.settings = heightmap_generator

    def run(self):
        if self.settings:
            self.settings.MainLaunchOperations()


class UHeightmapGeneratorUI(QMainWindow):
    def __init__(self, heightmap_generator):
        super().__init__()
        self.combobox_directions =None
        self.settings : UHeightMapGenerator = heightmap_generator
        self.param_widgets = [] #[[Name, Widget]]
        self.initUI()

    def initUI(self):
        # Основной контейнер

        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Левая часть с изображением и кнопками
        left_layout = QVBoxLayout()

        # Label для отображения изображения
        self.draw_debug_lines_checkbox = QCheckBox()
        self.draw_debug_lines_checkbox.setText("Show Only Debug Lines")
        self.draw_debug_lines_checkbox.setChecked(True)
        left_layout.addWidget(self.draw_debug_lines_checkbox)

        self.image_label = QLabel("Image Preview")
        #self.image_label.setFixedSize(400, 400)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.image_label)

        progress_layout = QHBoxLayout()

        self.progress_text = QLabel("")
        progress_layout.addWidget(self.progress_text)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 300, 25)  # Размер и положение прогресс-бара
        self.progress_bar.setMaximum(100)  # Устанавливаем максимальное значение
        progress_layout.addWidget(self.progress_bar)

        left_layout.addLayout(progress_layout)

        self.tree_lines = QTreeWidget()
        self.tree_lines.setColumnCount(1)  # Указываем количество колонок
        self.tree_lines.setHeaderLabels(["Items"])  # Название колонки
        left_layout.addWidget(self.tree_lines)



        self.load_button = QPushButton("Load File")
        self.reset_button = QPushButton("Reset Data")
        self.apply_button = QPushButton("Apply")
        self.load_button.clicked.connect(self.on_load_file)
        self.reset_button.clicked.connect(self.on_reset)
        self.apply_button.clicked.connect(self.on_apply)

        left_layout.addWidget(self.load_button)
        self.loaded_status_text = QLabel("Loading Status")
        left_layout.addWidget(self.loaded_status_text)
        self.UpdateLoadedStatusText()

        left_layout.addWidget(self.reset_button)
        left_layout.addWidget(self.apply_button)
        # Добавляем левый блок в основной layout
        main_layout.addLayout(left_layout)

        # Правая часть - панель с параметрами
        right_layout = QVBoxLayout()

        # Прокручиваемая область для параметров
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        self.scroll_layout = QFormLayout(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)

        # Автоматическое создание элементов интерфейса для параметров
        self.create_param_controls(self.scroll_layout)

        # Добавляем прокручиваемую область на правую панель
        availible_parce_lines_text_label = QLabel("Recive Line")
        right_layout.addWidget(availible_parce_lines_text_label)
        availible_parce_lines_text_label.setAlignment(Qt.AlignCenter)

        self.availible_parce_lines_array = UIModulate.UArrayWidget(UAvailibleParceLineSettings, self.settings.availible_parce_contour_line_settings)
        right_layout.addWidget(self.availible_parce_lines_array)

        right_layout.addWidget(scroll_area)



        fixing_line_text_lable = QLabel("Fixing Line")
        right_layout.addWidget(fixing_line_text_lable)
        fixing_line_text_lable.setAlignment(Qt.AlignCenter)
        self.fix_line_settings_array = UIModulate.UArrayWidget(UFixingLinesSettings, self.settings.fixing_lines_settings)

        right_layout.addWidget(self.fix_line_settings_array)

        main_layout.addLayout(right_layout)

        self.setCentralWidget(central_widget)
        self.setWindowTitle("Heightmap Generator")
        self.resize(800, 600)

        self.delete_shortcut = QShortcut(QKeySequence("Delete"), self)
        self.delete_shortcut.activated.connect(self.delete_key_event)

        self.apply_shortcut = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.apply_shortcut.activated.connect(self.apply_key_event)

        self.fix_line_settings_array.setFocus()

        self.thread_warper = UHeightmapGenerationWarperThread()

    def delete_key_event(self):
        self.availible_parce_lines_array.key_delete_setting()
        self.fix_line_settings_array.key_delete_setting()

    def apply_key_event(self):
        self.availible_parce_lines_array.apply_key_event()
        self.fix_line_settings_array.apply_key_event()


    def updateProgress(self, value):
        # Обновляем значение прогресс-бара
        self.progress.setValue(value)

    def UpdateLoadedStatusText(self):
        if(self.settings.file_path):
            if(os.path.exists(self.settings.file_path)):
                self.loaded_status_text.setText("Loaded")
                return
        self.loaded_status_text.setText("Not Loaded")

    def create_param_controls(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.param_widgets = []
        for attr_name in self.settings.ui_show_tag:
            value = getattr(self.settings, attr_name)
            if isinstance(value, bool):
                self.create_checkbox(layout, attr_name, value)
            elif (isinstance(value, str) and hasattr(self.settings, str(attr_name + "_options"))):
                options = getattr(self.settings, str(attr_name + "_options"))
                self.create_options(layout, attr_name, value, options)
            elif isinstance(value, int):
                self.create_spinbox(layout, attr_name, value)
            elif isinstance(value, float):
                self.create_double_spinbox(layout, attr_name, value)
            elif isinstance(value, str):  # Для строковых параметров
                lineedit = self.create_lineedit(layout, attr_name, value)




    def UpdateLines(self):
        self.tree_lines.clear()
        root_lines = line.GetRootLines(self.settings.lines)
        for root_line in root_lines:
            self.AddAllChildLines(root_line, None)

    def AddAllChildLines(self, parent_line, parent_tree):
        child = None
        if(parent_tree):
            child = QTreeWidgetItem(parent_tree)
        else:
            child = QTreeWidgetItem(self.tree_lines)
        child.setText(0, str(parent_line))
        child.setBackground(0, QColor(parent_line.color[0],parent_line.color[1],parent_line.color[2]))

        for uline in parent_line.childs:
            self.AddAllChildLines(uline, child)

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

    def create_options(self, layout, attr_name, value, options):
        """Создание ввода числа для вещественных параметров."""
        combobox_directions = QComboBox()
        combobox_directions.addItems(options)
        combobox_directions.setItemText(options.index(value))
        self.param_widgets.append([attr_name, combobox_directions])
        layout.addRow(attr_name, combobox_directions)

    def create_lineedit(self, layout, attr_name, value):
        """Создание текстового поля для строковых параметров."""
        line_edit = QLineEdit()
        line_edit.setText(value)  # Устанавливаем начальное значение
        self.param_widgets.append([attr_name, line_edit])
        layout.addRow(attr_name, line_edit)

    def FindParamWidgetByName(self, attr_name):
        for param_widget in self.param_widgets:
            if param_widget[0] == attr_name:
                return param_widget[1]
        return None

    # События для кнопок
    def on_load_file(self):
        path_file, data = helper_functions.ChooseFile()
        if (path_file):
            self.settings.file_path = path_file
            self.ApplyAllVariableAndSave()
        else:
            print("Warning: No selected File")

    def on_reset(self):
        # Сбросить параметры
        self.settings.from_dict(UHeightMapGenerator().to_dict())
        self.create_param_controls(self.scroll_layout)
        self.UpdateLoadedStatusText()


    def ApplyAllVariableAndSave(self):
        """Применить параметры из UI в объект settings."""
        for attr_name in self.settings.save_tag:
            widget = self.FindParamWidgetByName(attr_name)
            if(widget):
                if isinstance(widget, QSpinBox):
                    setattr(self.settings, attr_name, widget.value())
                elif isinstance(widget, QDoubleSpinBox):  # Заменяем QSlider на QDoubleSpinBox
                    setattr(self.settings, attr_name, widget.value())
                elif isinstance(widget, QCheckBox):
                    setattr(self.settings, attr_name, widget.isChecked())
                elif isinstance(widget, QLineEdit):  # Для строковых параметров
                    setattr(self.settings, attr_name, widget.text())
                elif isinstance(widget, QComboBox):
                    setattr(self.settings, attr_name, widget.currentText())
        self.settings.availible_parce_settings = self.availible_parce_lines_array.settings_list
        self.settings.fixing_lines_settings = self.fix_line_settings_array.settings_list
        self.UpdateLoadedStatusText()
        self.save_settings_to_file("save_file")
        print("Параметры обновлены:", vars(self.settings))

    def on_image_cooked(self):
        if (self.settings.cook_image):
            save_path = "output_image.png"  # или другой путь и имя файла
            self.settings.cook_image.save(save_path)
            loaded_pixmap = QPixmap(save_path)
            self.image_label.setPixmap(loaded_pixmap)
            self.UpdateLines()
            self.settings.end_cook_delegate.remove(self.on_image_cooked)
            playsound('Complete.wav')


    def on_apply(self):
        self.ApplyAllVariableAndSave()
        if(self.settings.file_path and os.path.exists(self.settings.file_path)):
            self.settings.draw_debug_lines = self.draw_debug_lines_checkbox.isChecked()
            self.settings.end_cook_delegate.add(self.on_image_cooked)
            self.thread_warper.set_heightmap_generator(self.settings)
            self.thread_warper.start()


    def save_settings_to_file(self, file_name):
        """Функция для сохранения параметров объекта в файл."""
        with open(file_name, 'w') as file:
            json.dump(self.settings.to_dict(), file, indent=4)

    def load_settings_from_file(self, file_name):
        """Функция для загрузки параметров из файла в объект."""
        if os.path.exists(file_name):
            with open(file_name, 'r') as file:
                loaded_params = json.load(file)
                self.settings.from_dict(loaded_params)
# Запуск приложения



