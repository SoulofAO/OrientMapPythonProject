from HeightmapGenerator import UHeightMapGenerator
from UI import UHeightmapGeneratorUI
import sys
import os
from PyQt5.QtWidgets import QApplication
import json

heightmap_generator = UHeightMapGenerator()

file_path = "save_file"

if os.path.exists(file_path):
    with open(file_path, 'r') as file:
        loaded_params = json.load(file)
        heightmap_generator.from_dict(loaded_params)
else:
    print(f"Файл Save '{file_path}' не найден. Будет создан файл по умолчанию")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UHeightmapGeneratorUI(heightmap_generator)
    window.show()
    sys.exit(app.exec_())
