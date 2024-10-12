import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QShortcut
from PyQt5.QtGui import QKeySequence

class ChildWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Создаем простой интерфейс для ChildWidget
        self.label = QLabel("Нажмите Ctrl+D для действия", self)
        self.label.setStyleSheet("font-size: 16px;")
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # Добавляем событие на горячую клавишу Ctrl+D
        self.shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut.activated.connect(self.on_hotkey_pressed)

        self.setLayout(layout)

    def on_hotkey_pressed(self):
        # Действие при нажатии горячей клавиши
        self.label.setText("Горячая клавиша Ctrl+D нажата!")

class ParentWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Основной интерфейс ParentWidget
        layout = QVBoxLayout()

        # Создаем кнопку в ParentWidget
        self.button = QPushButton("Я родитель", self)
        layout.addWidget(self.button)

        # Добавляем дочерний виджет (ChildWidget)
        self.child_widget = ChildWidget(self)
        layout.addWidget(self.child_widget)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Создаем экземпляр родительского виджета
    parent_widget = ParentWidget()
    parent_widget.show()

    sys.exit(app.exec_())
