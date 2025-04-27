import sys
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class ImageViewer(QGraphicsView):
    def __init__(self, image_path):
        super().__init__()

        # Создаем сцену
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Загружаем картинку
        self.pixmap_item = QGraphicsPixmapItem(QPixmap(image_path))
        self.scene.addItem(self.pixmap_item)

        # Параметры управления
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        # Масштабирование
        self.scale_factor = 1.15  # скорость увеличения/уменьшения
        self.current_scale = 1.0  # текущий масштаб
        self.min_scale = 0.1      # минимальный масштаб
        self.max_scale = 2.0      # максимальный масштаб

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


def main():
    app = QApplication(sys.argv)
    viewer = ImageViewer("lines_image.png")  # Укажи путь к картинке
    viewer.setWindowTitle("Image Viewer")
    viewer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
