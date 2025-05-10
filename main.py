from HeightmapGenerator import UHeightMapGenerator
from UI import UHeightmapGeneratorUI
import sys
import os
from PyQt5.QtWidgets import QApplication
import json
import argparse

heightmap_generator = UHeightMapGenerator()

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--default_run', type=lambda x: x.lower() in ['true', '1', 'yes'], required=True)
parser.add_argument('-f', '--default_file_path', required=True)

args = parser.parse_args()
print(args.default_run, args.default_file_path)

if __name__ == "__main__":
    if(bool(args.default_run)):
        heightmap_generator.file_path = args.default_file_path
        heightmap_generator.draw_debug_lines = False

        file_path = "default_save_file"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                loaded_params = json.load(file)
                heightmap_generator.from_dict(loaded_params)
        else:
            print("Result : Failed")
            exit()

        try:
            heightmap_generator.MainLaunchOperations();
            print("Result : Sucsess")
        except:
            print("Result : Failed")

    else:
        file_path = "save_file"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                loaded_params = json.load(file)
                heightmap_generator.from_dict(loaded_params)
        else:
            print(f"Файл Save '{file_path}' не найден. Будет создан файл по умолчанию")

        app = QApplication(sys.argv)
        window = UHeightmapGeneratorUI(heightmap_generator)
        window.show()
        sys.exit(app.exec_())
