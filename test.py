import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from shapely.geometry import Polygon, Point
from PIL import Image, ImageDraw
import re

global_scale_multiplier = 0.25
width, height = 2000* global_scale_multiplier, 2000 * global_scale_multiplier
availible_parce_data = ["Contour","Index contour"]

class ULine:
    def __init__(self, parent, childs, shapely_polygon, line):
        self.parent = parent
        self.childs = childs
        self.shapely_polygon = shapely_polygon
        self.line = line

    def GetRootLine(this):
        if (this.parent):
            return this.parent.GetRootLine()
        else:
            return this

    def GetMaxDepth(self, depth = 0):
        if(len(self.childs)>0):
            max_depth = -1
            for child in self.childs:
                depth = child.GetMaxDepth(depth + 1)
                if(depth>max_depth):
                    max_depth = depth
            return max_depth
        else:
            return depth


import tkinter as tk
from tkinter import filedialog
import csv


def ChooseFile():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Выберите файл BNA",
                                           filetypes=[("BNA files", "*.bna"), ("All files", "*.*")])

    if file_path:
        print(f"Выбранный файл: {file_path}")
        ReadFile(file_path)
    else:
        print("Файл не выбран.")

    if file_path:
        print(f"Выбранный файл: {file_path}")
        return ReadFile(file_path)
    else:
        print("Файл не выбран.")


def ReadFile(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        content = file.read()  # Читаем содержимое файла
        print(content)
        return content
    return None


def can_convert_to_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def ParseLinesFromData(data):
    lines = []
    current_line = []
    correct_data = True;
    for line in data.splitlines():
        stripped_line = line.strip()
        points = stripped_line.split(',')

        if not can_convert_to_float(points[0]):
            if points[0] in availible_parce_data:
                correct_data = True;
                if current_line:
                    lines.append(current_line)
                    current_line = []
            else:
                correct_data = False
        else:

            if len(points) == 2 and correct_data:
                x = float(points[0]) * global_scale_multiplier
                y = float(points[1]) * global_scale_multiplier
                current_line.append([x, y])

    if current_line:
        lines.append(current_line)

    return lines
def ParseLinesFromData(data):
    lines = []
    current_line = []
    correct_data = True;
    for line in data.splitlines():
        stripped_line = line.strip()
        points = stripped_line.split(',')

        if not can_convert_to_float(points[0]):
            if points[0] in availible_parce_data:
                correct_data = True;
                if current_line:
                    lines.append(current_line)
                    current_line = []
            else:
                correct_data = False
        else:

            if len(points) == 2 and correct_data:
                x = float(points[0]) * global_scale_multiplier
                y = float(points[1]) * global_scale_multiplier
                current_line.append([x, y])

    if current_line:
        lines.append(current_line)

    return lines

def SetupWidthAndHeightFromDataLines(lines):
    max_width = -1
    max_height = -1

    for line in lines:
        for coord in line:
            if(max_width>coord[0]):
                max_width = coord[0]
            if(max_height>coord[1]):
                max_height = coord[1]
    width = max_width
    height = max_width

def GenerateLines(lines):
    update_lines = []
    for line in lines:
        updated_coords = []
        for coord in line:
            x = coord[0]+width*1/2
            y = coord[1]+height*1/2
            updated_coords.append([x,y])
        update_lines.append(updated_coords)

    polygons = [ULine(None,[],Polygon(line), line) for line in update_lines]

    for focus_shape in polygons:
        for other_shape in polygons:
            if focus_shape != other_shape and focus_shape.shapely_polygon.contains(other_shape.shapely_polygon):
                focus_shape.childs.append(other_shape)
                other_shape.parent = focus_shape
    return polygons

def GetMaxDepthFromLines(lines):
    max_depth = -1
    for line in lines:
        depth = line.GetMaxDepth()
        if(max_depth<depth):
            max_depth = depth
    return max_depth

def DrawPlotHeightMap(lines):
    max_depth = GetMaxDepthFromLines(lines)
    image = Image.new("RGB", (int(width), int(height)), "black")
    draw = ImageDraw.Draw(image)
    root_lines = GetRootLines(lines)
    # Применяем интенсивность к изображению
    for y in range(int(height)):
        for x in range(int(width)):
            point = Point(x, y)
            intensity = 0
            owner_line = None
            min_poligin_length = 100000000000000
            for line in lines:
                if line.shapely_polygon.contains(point):
                    intensity += 1
                    if(min_poligin_length>line.shapely_polygon.length):
                        min_poligin_length = line.shapely_polygon.length
                        owner_line = line
            if owner_line:
                distance_to_owner_poligon = point.distance(owner_line.shapely_polygon.exterior)
                min_distance_to_child_poligon = 100000000000000
                child_line = None
                for child in owner_line.childs:
                    if min_distance_to_child_poligon> point.distance(child.shapely_polygon.exterior):
                        min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                        child_line = child
                distance_to_child_poligon = min_distance_to_child_poligon

                normalize_distance_to_child_poligon = distance_to_child_poligon/(distance_to_child_poligon+ distance_to_owner_poligon )
                normalize_distance_to_owner_poligon = distance_to_owner_poligon / (
                            distance_to_child_poligon + distance_to_owner_poligon)
                intensity +=1-normalize_distance_to_child_poligon
            else:
                min_distance_to_child_poligon = 100000000000000
                child_line = None
                for child in root_lines:
                    if min_distance_to_child_poligon> point.distance(child.shapely_polygon.exterior):
                        min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                        child_line = child
                distance_to_child_poligon = min_distance_to_child_poligon

                normalize_distance_to_child_poligon = distance_to_child_poligon/(distance_to_child_poligon+ 200)
                intensity +=1-normalize_distance_to_child_poligon


            white_intensity = min(255, int(intensity * 255/max_depth))  # Увеличиваем интенсивность
            draw.point((int(x), int(y)), fill=(white_intensity, white_intensity, white_intensity))



    image.show()


def DrawPlotHeightMapV0(lines):
    # Устанавливаем размеры изображения
    width, height = 2000, 2000  # Измените размеры по необходимости
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    colors = ['black', 'blue', 'red']
    k = 0

    while len(lines) > 0:
        new_lines = []

        for line in lines:
            # Создаем полигон из линий
            polygon = Polygon(line.line)
            if polygon.is_valid:
                # Преобразуем координаты для изображения
                coords = [(x + width // 2, height // 2 - y) for x, y in line.line]

                # Рисуем полигон
                draw.polygon(coords, fill=colors[k], outline=colors[k])

            if len(line.childs):
                new_lines.extend(line.childs)

        lines = new_lines
        k += 1
        if k >= len(colors):  # Защита от выхода за пределы списка цветов
            break

    image.show()  # Отображаем изображение

def GetRootLines(lines):
    answer = []
    for line in lines:
        root_line = line.GetRootLine()
        if not root_line in answer:
            answer.append(root_line)
    return answer




# Пример входных данных (замените на ваши реальные данные)
data = """
0,-800
-800,0
0,800
800,0
new_line
0,-400
-400,0
0,400
400,0
new_line
0,-200
-200,0
0,200
200,0
new_line
"""


data = ChooseFile()
if(data):
    data_lines = ParseLinesFromData(data)
    SetupWidthAndHeightFromDataLines(data_lines)
    lines = GenerateLines(data_lines)
    print(lines)
    root_lines = GetRootLines(lines)
    DrawPlotHeightMap(lines)