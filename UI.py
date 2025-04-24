import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QSlider, QVBoxLayout, QCheckBox,
    QPushButton, QHBoxLayout, QFormLayout, QSpinBox, QFileDialog, QScrollArea, QDoubleSpinBox, QComboBox, QTreeWidget, QTreeWidgetItem, QProgressBar, QShortcut, QLineEdit, QSplitter
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
import PIL.ImageQt as ImageQt
import helper_functions
import json
import os
from HeightmapGenerator import UHeightMapGenerator, UFixingLinesSettings, UAvailibleParceLineSettings
import line
from PyQt5.QtGui import QColor
import UIModulate
from playsound import playsound
from Delegates import UDelegate

class UHeightmapGenerationWarperThread(QThread):
    progress_signal = pyqtSignal(str, int)
    error_lines_signal = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.settings = None

    def call_update_percent_delegate(self, text, value):
        # Отправляем сигнал с текстом и значением
        self.progress_signal.emit(text, value)

    def set_heightmap_generator(self, heightmap_generator):
        self.settings = heightmap_generator

    def call_update_error_lines_delegate(self, int):
        self.error_lines_signal.emit(int)

    def run(self):
        if self.settings:
            self.settings.progress_delegate.add(self.call_update_percent_delegate)
            self.settings.error_lines_delegate.add(self.call_update_error_lines_delegate)
            self.settings.MainLaunchOperations()


class UHeightmapGeneratorUI(QMainWindow):
    def __init__(self, heightmap_generator):
        super().__init__()
        self.combobox_directions =None
        self.settings : UHeightMapGenerator = heightmap_generator
        self.param_widgets = [] #[[Name, Widget]]
        self.initUI()

    def closeEvent(self, event):
        self.ApplyAllVariableAndSave()
        event.accept()


    def initUI(self):
        # Основной контейнер
        main_splitter = QSplitter(Qt.Horizontal)

        # Левая часть с изображением и кнопками
        left_splitter = QSplitter(Qt.Vertical)

        # Label для отображения изображения
        high_widget = QWidget()
        high_layout = QHBoxLayout()
        self.draw_debug_lines_checkbox = QCheckBox()
        self.draw_debug_lines_checkbox.setText("Show Only Debug Lines")
        self.draw_debug_lines_checkbox.setChecked(True)
        high_layout.addWidget(self.draw_debug_lines_checkbox)

        self.error_lines_counter = QLabel("")
        self.error_lines_counter.setText("Error Lines Counter: 0")
        high_layout.addWidget(self.error_lines_counter)

        high_widget.setLayout(high_layout)

        left_splitter.addWidget(high_widget)

        self.image_label = QLabel("Image Preview")
        #self.image_label.setFixedSize(400, 400)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        left_splitter.addWidget(self.image_label)

        progress_widget = QWidget()
        progress_layout = QHBoxLayout()

        self.progress_text = QLabel("")
        progress_layout.addWidget(self.progress_text)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 300, 25)  # Размер и положение прогресс-бара
        self.progress_bar.setMaximum(100)  # Устанавливаем максимальное значение
        progress_layout.addWidget(self.progress_bar)
        progress_widget.setLayout(progress_layout)

        left_splitter.addWidget(progress_widget)

        self.tree_lines = QTreeWidget()
        self.tree_lines.setColumnCount(1)  # Указываем количество колонок
        self.tree_lines.setHeaderLabels(["Items"])  # Название колонки
        left_splitter.addWidget(self.tree_lines)

        self.load_button = QPushButton("Load File")
        self.reset_button = QPushButton("Reset Data")
        self.apply_button = QPushButton("Apply")
        self.load_button.clicked.connect(self.on_load_file)
        self.reset_button.clicked.connect(self.on_reset)
        self.apply_button.clicked.connect(self.on_apply)

        left_splitter.addWidget(self.load_button)
        self.loaded_status_text = QLabel("Loading Status")
        left_splitter.addWidget(self.loaded_status_text)
        self.UpdateLoadedStatusText()

        left_splitter.addWidget(self.reset_button)
        left_splitter.addWidget(self.apply_button)

        spltter_stretch_factors = [1,20,1,2,2,2,2,2]
        counter = 0
        for spltter_stretch_factor in spltter_stretch_factors:
            left_splitter.setStretchFactor(counter, spltter_stretch_factor)
            counter +=1

        main_splitter.addWidget(left_splitter)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setSizes([800, 800])

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
        right_splitter.addWidget(availible_parce_lines_text_label)
        availible_parce_lines_text_label.setAlignment(Qt.AlignCenter)

        self.availible_parce_lines_array = UIModulate.UArrayWidget(UAvailibleParceLineSettings, self.settings.availible_parce_contour_line_settings)
        right_splitter.addWidget(self.availible_parce_lines_array)

        right_splitter.addWidget(scroll_area)

        fixing_line_layout = QVBoxLayout()
        fixing_line_widget = QWidget()
        fixing_line_widget.setLayout(fixing_line_layout)
        right_splitter.addWidget(fixing_line_widget)

        fixing_line_text_label = QLabel("Fixing Line")
        fixing_line_layout.addWidget(fixing_line_text_label)
        fixing_line_text_label.setAlignment(Qt.AlignCenter)

        self.fix_line_settings_array = UIModulate.UArrayWidget(UFixingLinesSettings,
                                                               self.settings.fixing_lines_settings)
        fixing_line_layout.addWidget(self.fix_line_settings_array)
        main_splitter.addWidget(right_splitter)

        self.setCentralWidget(main_splitter)
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

    @pyqtSlot(str, int)
    def update_progress_bar(self, text, value):
        self.progress_text.setText(text)
        value = min(100,value)
        if(self.progress_bar):
            self.progress_bar.setValue(value)

    @pyqtSlot(int)
    def update_error_lines(self, value):
        self.error_lines_counter.setText("Error Lines Counter:" + value)

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
            self.error_lines_counter.setText("Error Lines Counter:" + str(self.settings.count_error_lines))
            self.settings.end_cook_delegate.remove(self.on_image_cooked)
            playsound('Complete.wav')


    def on_apply(self):
        self.ApplyAllVariableAndSave()
        if(self.settings.file_path and os.path.exists(self.settings.file_path)):
            self.settings.draw_debug_lines = self.draw_debug_lines_checkbox.isChecked()
            self.settings.end_cook_delegate.add(self.on_image_cooked)
            self.thread_warper.progress_signal.connect(self.update_progress_bar)
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



