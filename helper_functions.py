from matplotlib.collections import PatchCollection
from shapely.geometry import Polygon, Point
from PIL import Image, ImageDraw
import re
import tkinter as tk
from tkinter import filedialog
import csv
import math

import time
import sys
import xml.etree.ElementTree as ET


def print_progress_bar(iteration, total, length=50):
    percent = (iteration / total) * 100
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)

    sys.stdout.write(f'\r|{bar}| {percent:.2f}% ({iteration}/{total})')
    sys.stdout.flush()

def ReadFile(file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        content = file.read()  # Читаем содержимое файла
        return content
    return None


def can_convert_to_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def ChooseFile():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Выберите файл OMAP, OCD, BNA",
                                               filetypes=[("OMAP files", "*.omap"), ("BNA files", "*.bna"), ("OCD files", "*.ocd"), ("All files", "*.*")])

    if file_path:
        print(f"Выбранный файл: {file_path}")
        return file_path, ReadFile(file_path)
    else:
        print("Файл не выбран.")
        return None, None;

def get_namespace(element):
    m = element.tag.find('}')
    return element.tag[:m + 1] if m != -1 else ''

# Функция для извлечения информации о символах (например, "Contour")
def extract_symbols(root, name, namespace):
    symbols = {}

    for symbol in root.findall(f'.//{namespace}symbol'):
        symbol_id = symbol.get('id')
        symbol_name = symbol.get('name')
        if symbol_name and (name in symbol_name):
            symbols[symbol_id] = symbol_name
    return symbols

    # Функция для поиска объектов по идентификатору символа и извлечения координат
def extract_object_coords(root, symbol_ids, namespace):
    objects = []

        # Проходим по всем объектам и проверяем символы
    for obj in root.findall(f'.//{namespace}object'):
        symbol_id = obj.get('symbol')
            # Если символ объекта есть в списке интересующих нас символов
        if symbol_id in symbol_ids:
            coords = obj.find(f'{namespace}coords').text.strip()
            objects.append({
                'symbol_id': symbol_id,
                'coordinates': coords
            })

    return objects

def fix_coordinates(coordinates):
    # Проверяем, что массив не пуст
    if not coordinates:
        return []

    last_element = coordinates[-1]

    if not (isinstance(last_element, list) and len(last_element) == 2):
        coordinates = coordinates[:-1]

    last_element = coordinates[-1]
    if not (isinstance(last_element, list) and len(last_element) == 2):
        coordinates[len(coordinates) - 1].pop(len(coordinates[len(coordinates) - 1])-1)

    return coordinates


def angle_between_vectors(v1, v2):
    # Векторное произведение для нахождения угла между двумя векторами
    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    magnitude_v1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    magnitude_v2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    if magnitude_v1 == 0 or magnitude_v2 == 0:
        return 0  # Защита от деления на ноль (можно изменить по необходимости)

    cos_angle = dot_product / (magnitude_v1 * magnitude_v2)
    # Ограничиваем значение косинуса для предотвращения ошибок из-за погрешностей
    cos_angle = max(-1.0, min(1.0, cos_angle))

    return math.acos(cos_angle)  # Возвращаем угол в радианах