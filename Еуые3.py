import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
import time


# Класс, представляющий поток для выполнения долгих операций
class HeightmapThread(QThread):
    progress = pyqtSignal(int)  # Сигнал для передачи прогресса

    def run(self):
        """Метод, который будет выполняться в отдельном потоке"""
        for i in range(1, 11):  # Имитация долгого процесса
            time.sleep(1)  # Долгий расчет
            self.progress.emit(i * 10)  # Отправка прогресса (0-100)


# Основное окно приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Heightmap Calculator")

        self.layout = QVBoxLayout()

        self.label = QLabel("Нажмите кнопку для расчета Heightmap")
        self.layout.addWidget(self.label)

        self.button = QPushButton("Начать расчет")
        self.button.clicked.connect(self.start_calculation)
        self.layout.addWidget(self.button)

        self.setCentralWidget(QWidget(self))
        self.centralWidget().setLayout(self.layout)

        # Создаем экземпляр потока
        self.thread = HeightmapThread()
        self.thread.progress.connect(self.update_progress)

    def start_calculation(self):
        self.label.setText("Расчет Heightmap запущен...")
        self.button.setEnabled(False)  # Отключаем кнопку, чтобы предотвратить повторный клик
        self.thread.start()  # Запускаем поток

    def update_progress(self, value):
        self.label.setText(f"Прогресс: {value}%")
        if value == 100:
            self.label.setText("Расчет завершен!")
            self.button.setEnabled(True)  # Включаем кнопку обратно


# Запуск приложения
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
