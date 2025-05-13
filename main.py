from HeightmapGenerator import UHeightMapGenerator
from UI import UHeightmapGeneratorUI
import sys
import os
from PyQt5.QtWidgets import QApplication
import json
import argparse

heightmap_generator = UHeightMapGenerator()

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--default_run', type=lambda x: x.lower() in ['true', '1', 'yes'], default=False,
                    required=False)
parser.add_argument('-f', '--default_file_path', default="None", required=False)
parser.add_argument('-o', '--default_draw_with_heightmap_step', type=lambda x: x.lower() in ['true', '1', 'yes'], default=True, required=False)
parser.add_argument('-g', '--default_heightmap_step', default=500, required=False)
parser.add_argument('-j', '--default_max_heightmap_step', default=65535, required=False)

args = parser.parse_args()

default_run = args.default_run
default_file_path = args.default_file_path
default_draw_with_heightmap_step = args.default_draw_with_heightmap_step
default_heightmap_step = float(args.default_heightmap_step)
default_max_heightmap_step = float(args.default_max_heightmap_step)

if __name__ == "__main__":
    if(bool(default_run)):
        file_path = "default_save_file"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                loaded_params = json.load(file)
                heightmap_generator.from_dict(loaded_params)
        else:
            print("Result : Failed")
            exit()

        heightmap_generator.file_path = default_file_path
        heightmap_generator.draw_debug_lines = False
        heightmap_generator.draw_with_heightmap_step = default_draw_with_heightmap_step
        heightmap_generator.heightmap_step  = default_heightmap_step
        heightmap_generator.max_heightmap_step = default_max_heightmap_step

        try:
            heightmap_generator.MainLaunchOperations();
            print("Result : Sucsess")
        except Exception as e:
            print("Error:", e)
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
