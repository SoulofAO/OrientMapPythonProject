import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QSlider, QVBoxLayout, QCheckBox,
    QPushButton, QHBoxLayout, QFormLayout, QSpinBox, QFileDialog, QScrollArea
)
from PyQt5.QtCore import Qt


# Пример класса с параметрами для генератора
class GeneratorSettings:
    def __init__(self):
        self.param1 = 50
        self.param2 = 0.5
        self.param3 = 100
        self.param4 = True


# Основное окно приложения
class HeightmapGeneratorUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = GeneratorSettings()  # Экземпляр класса с параметрами
        self.initUI()

    def initUI(self):
        # Основной контейнер
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Левая часть с изображением и кнопками
        left_layout = QVBoxLayout()

        # Label для отображения изображения
        self.image_label = QLabel("Image Preview")
        self.image_label.setFixedSize(400, 400)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.image_label)

        # Кнопки загрузки, сброса и применения
        self.load_button = QPushButton("Load File")
        self.reset_button = QPushButton("Reset")
        self.apply_button = QPushButton("Apply")
        self.load_button.clicked.connect(self.on_load_file)
        self.reset_button.clicked.connect(self.on_reset)
        self.apply_button.clicked.connect(self.on_apply)
        left_layout.addWidget(self.load_button)
        left_layout.addWidget(self.reset_button)
        left_layout.addWidget(self.apply_button)

        # Добавляем левый блок в основной layout
        main_layout.addLayout(left_layout)

        # Правая часть - панель с параметрами
        right_layout = QVBoxLayout()

        # Прокручиваемая область для параметров
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)

        # Автоматическое создание элементов интерфейса для параметров
        self.create_param_controls(scroll_layout)

        # Добавляем прокручиваемую область на правую панель
        right_layout.addWidget(scroll_area)

        # Добавляем правый блок в основной layout
        main_layout.addLayout(right_layout)

        # Устанавливаем основной виджет
        self.setCentralWidget(central_widget)
        self.setWindowTitle("Heightmap Generator")
        self.resize(800, 600)

    def create_param_controls(self, layout):
        """Создаем UI элементы для всех параметров из settings."""
        for attr_name in dir(self.settings):
            if not attr_name.startswith('__') and not callable(getattr(self.settings, attr_name)):
                value = getattr(self.settings, attr_name)
                if isinstance(value, int):
                    self.create_spinbox(layout, attr_name, value)
                elif isinstance(value, float):
                    self.create_slider(layout, attr_name, value)
                elif isinstance(value, bool):
                    self.create_checkbox(layout, attr_name, value)

    def create_spinbox(self, layout, attr_name, value):
        """Создание SpinBox для целочисленных параметров."""
        spin_box = QSpinBox()
        spin_box.setValue(value)
        spin_box.setMinimum(0)
        spin_box.setMaximum(1000)
        spin_box.valueChanged.connect(lambda val: setattr(self.settings, attr_name, val))
        layout.addRow(attr_name, spin_box)

    def create_slider(self, layout, attr_name, value):
        """Создание слайдера для вещественных параметров."""
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(int(value * 100))
        slider.valueChanged.connect(lambda val: setattr(self.settings, attr_name, val / 100.0))
        layout.addRow(attr_name, slider)

    def create_checkbox(self, layout, attr_name, value):
        """Создание чекбокса для булевых параметров."""
        from PyQt5.QtWidgets import QCheckBox
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        checkbox.stateChanged.connect(lambda state: setattr(self.settings, attr_name, state == Qt.Checked))
        layout.addRow(attr_name, checkbox)

    # События для кнопок
    def on_load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.bmp)")
        if file_name:
            # Загрузить файл и применить его
            pass

    def on_reset(self):
        # Сбросить параметры
        pass

    def on_apply(self):
        # Применить параметры
        for attr_name in dir(self.settings):
            if not attr_name.startswith('__') and not callable(getattr(self.settings, attr_name)):
                widget = self.findChild(QWidget, attr_name)
                if isinstance(widget, QSpinBox):
                    setattr(self.settings, attr_name, widget.value())
                elif isinstance(widget, QSlider):
                    setattr(self.settings, attr_name, widget.value() / 100.0)
                elif isinstance(widget, QCheckBox):
                    setattr(self.settings, attr_name, widget.isChecked())

            # Дополнительно, здесь можно добавить код для пересчета карты или отображения результата.
        print("Параметры обновлены:", vars(self.settings))


# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HeightmapGeneratorUI()
    window.show()
    sys.exit(app.exec_())