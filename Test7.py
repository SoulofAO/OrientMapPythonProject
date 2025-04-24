import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QSplitter, QListWidget,
    QTextEdit, QVBoxLayout
)


class SplitterDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Splitter‑разделитель")

        # Левый и правый виджеты
        nav = QListWidget()
        nav.addItems([f"Элемент {i}" for i in range(1, 11)])

        editor = QTextEdit("Редактируемый текст")

        # --- создаём сплиттер ---
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(nav)
        splitter.addWidget(editor)

        # Задаём начальные пропорции (по пикселям)
        splitter.setSizes([150, 450])

        # Корневой layout
        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    splitter_demo = SplitterDemo()
    splitter_demo.resize(400,400)
    splitter_demo.show()
    sys.exit(app.exec_())

