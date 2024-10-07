import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtGui import QColor

class TreeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Настройка окна
        self.setWindowTitle("Пример цветного дерева в PyQt5")
        self.setGeometry(300, 100, 600, 400)

        # Создаем центральный виджет и макет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Создаем дерево
        self.tree = QTreeWidget()
        self.tree.setColumnCount(1)  # Указываем количество колонок
        self.tree.setHeaderLabels(["Items"])  # Название колонки

        # Добавляем корневые элементы
        root1 = QTreeWidgetItem(self.tree)
        root1.setText(0, "Root 1")

        root2 = QTreeWidgetItem(self.tree)
        root2.setText(0, "Root 2")

        # Задаем цвет фона для root1
        root1.setBackground(0, QColor(255, 204, 204))  # Светло-красный фон
        # Задаем цвет текста для root1
        root1.setForeground(0, QColor(0, 0, 255))  # Синий текст

        # Добавляем дочерние элементы к root1
        child1 = QTreeWidgetItem(root1)
        child1.setText(0, "Child 1.1")
        child1.setBackground(0, QColor(204, 255, 204))  # Светло-зеленый фон

        child2 = QTreeWidgetItem(root1)
        child2.setText(0, "Child 1.2")
        child2.setForeground(0, QColor(255, 0, 0))  # Красный текст

        # Добавляем подуровень дочерних элементов
        subchild1 = QTreeWidgetItem(child1)
        subchild1.setText(0, "SubChild 1.1.1")
        subchild1.setBackground(0, QColor(204, 204, 255))  # Светло-синий фон

        # Добавляем дочерние элементы к root2
        child3 = QTreeWidgetItem(root2)
        child3.setText(0, "Child 2.1")
        child3.setForeground(0, QColor(0, 128, 0))  # Темно-зеленый текст

        # Добавляем дерево на макет
        layout.addWidget(self.tree)

        # Устанавливаем макет
        central_widget.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TreeWindow()
    window.show()
    sys.exit(app.exec_())
