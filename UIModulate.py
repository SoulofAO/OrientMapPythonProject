import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout,
    QLineEdit, QPushButton,
    QListWidget, QMessageBox, QScrollArea, QFormLayout, QSpinBox, QCheckBox, QHBoxLayout, QDoubleSpinBox, QLabel, QListWidgetItem, QComboBox, QShortcut, QSplitter
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QListWidget, QScrollArea, QFormLayout, QVBoxLayout,
    QHBoxLayout, QPushButton, QSplitter, QSizePolicy, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

class UArrayWidget(QWidget):
    def __init__(self, settings_class, settings_list, font_size=12.0):
        super().__init__()
        self.settings_class = settings_class
        self.param_widgets = []
        self.settings_list = settings_list
        self.unique_values = False
        self.font_size = font_size

        self._build_ui()

        for setting in settings_list:
            self.create_new_setting(setting)

    def _build_ui(self):
        """Композиция виджетов со сплиттерами."""
        root_splitter = QSplitter(Qt.Vertical, self)    # главный H‑splitter

        # ─── Левая панель ───────────────────────────────────────────
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.MinimumExpanding,
                                       QSizePolicy.Expanding)
        root_splitter.addWidget(self.list_widget)

        # ─── Правая (вертикальная) панель ───────────────────────────
        right_splitter = QSplitter(Qt.Vertical)
        root_splitter.addWidget(right_splitter)

        # ----‑‑‑‑‑ Верх: прокручиваемая форма параметров -------------‑
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        self.scroll_layout = QFormLayout(scroll_content)
        self.generate_settings(self.scroll_layout)        # заполнение полей

        scroll_area.setWidget(scroll_content)
        right_splitter.addWidget(scroll_area)

        # ----‑‑‑‑‑ Низ: кнопочная панель ----------------------------‑
        button_box = QWidget()
        button_layout = QHBoxLayout(button_box)
        button_layout.setContentsMargins(0, 0, 0, 0)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_setting)
        button_layout.addWidget(add_btn)

        del_btn = QPushButton("Delete")
        del_btn.clicked.connect(self.delete_setting)
        button_layout.addWidget(del_btn)

        right_splitter.addWidget(button_box)

        # ─── Финальная сборка ───────────────────────────────────────
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(root_splitter)
        self.setLayout(main_layout)

        # подключаем выбор в списке к загрузке параметров
        self.list_widget.currentRowChanged.connect(self.load_settings)

        # стартовые размеры секций (можно менять на вкус)
        root_splitter.setSizes([150, 400])
        right_splitter.setSizes([300, 60])


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
                    lineedit = self.create_lineedit(layout, attr_name, value)

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
        index = self.list_widget.count()
        name_label = QLabel(f"{str(index)}: {str(new_setting)}")  # Пример отображения одного из значений

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

                name_label_string = f"{str(index)}: {str(settings)}"  # Пример отображения одного из значений

                new_name_label = QLabel(f"{name_label_string}")  # Пример обновления строки
                new_name_label.setWordWrap(True)
                new_name_label.setStyleSheet(f"font-size: {self.font_size}px;")

                # Добавляем обновленный QLabel в layout виджета
                item_widget.layout().addWidget(new_name_label)

                # Обновляем размер элемента
                list_item.setSizeHint(item_widget.sizeHint())

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

    def key_delete_setting(self):
        if(self.list_widget.hasFocus()):
            self.delete_setting()

    def create_spinbox(self, layout, attr_name, value):
        spin_box = QSpinBox()
        spin_box.setMinimum(-100000)
        spin_box.setMaximum(100000)
        spin_box.setValue(value)
        spin_box.valueChanged.connect(self.on_widget_changed)
        layout.addRow(attr_name, spin_box)
        self.param_widgets.append([attr_name, spin_box])

    def create_double_spinbox(self, layout, attr_name, value):
        """Создание ввода числа для вещественных параметров."""
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(2)
        spin_box.setMinimum(-100000.0)
        spin_box.setMaximum(100000.0)
        spin_box.setSingleStep(0.01)
        spin_box.setValue(value)
        spin_box.valueChanged.connect(self.on_widget_changed)
        layout.addRow(attr_name, spin_box)
        self.param_widgets.append([attr_name, spin_box])

    def create_checkbox(self, layout, attr_name, value):
        """Создание чекбокса для булевых параметров."""
        checkbox = QCheckBox()
        checkbox.setChecked(value)
        checkbox.stateChanged.connect(self.on_widget_changed)
        layout.addRow(attr_name, checkbox)
        self.param_widgets.append([attr_name, checkbox])

    def create_lineedit(self, layout, attr_name, value):
        """Создание текстового поля для строковых параметров."""
        line_edit = QLineEdit()
        line_edit.setText(value)
        line_edit.textChanged.connect(self.on_widget_changed)
        layout.addRow(attr_name, line_edit)
        self.param_widgets.append([attr_name, line_edit])

    def create_options(self, layout, attr_name, value, options):
        """Создание выпадающего списка для выбора параметров."""
        combobox_directions = QComboBox()
        combobox_directions.addItems(options)
        if value in options:
            combobox_directions.setCurrentIndex(options.index(value))
        combobox_directions.currentIndexChanged.connect(self.on_widget_changed)
        layout.addRow(attr_name, combobox_directions)
        self.param_widgets.append([attr_name, combobox_directions])

    def on_widget_changed(self, *args):
        self.edit_setting()


class UImageViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Внутренние элементы
        self.view = _UInternalGraphicsView()
        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.setContentsMargins(0, 0, 0, 0)  # без отступов

    def setPixmap(self, pixmap: QPixmap):
        self.view.setPixmap(pixmap)

    def clear(self):
        self.view.clear()


class _UInternalGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Сцена и элементы
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None

        # Параметры управления
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Масштабирование
        self.scale_factor = 1.15
        self.current_scale = 1.0
        self.min_scale = 0.2
        self.max_scale = 5.0

    def setPixmap(self, pixmap: QPixmap):
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            self.pixmap_item = None

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        self.resetTransform()
        self.current_scale = 1.0

    def clear(self):
        if self.pixmap_item:
            self.scene.removeItem(self.pixmap_item)
            self.pixmap_item = None
        self.resetTransform()
        self.current_scale = 1.0

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0

        if zoom_in:
            if self.current_scale * self.scale_factor <= self.max_scale:
                self.scale(self.scale_factor, self.scale_factor)
                self.current_scale *= self.scale_factor
        else:
            if self.current_scale / self.scale_factor >= self.min_scale:
                self.scale(1 / self.scale_factor, 1 / self.scale_factor)
                self.current_scale /= self.scale_factor

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)
        super().mouseReleaseEvent(event)



