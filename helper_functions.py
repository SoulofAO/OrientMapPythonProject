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
        code = symbol.get('code')
        symbol_name = symbol.get('name')
        if symbol_name and (name in symbol_name):
            symbols[symbol_id] = symbol_name

    return symbols

def extract_symbols_by_code(root, code_range, namespace):
    symbols = {}
    min_code, max_code = code_range

    for symbol in root.findall(f'.//{namespace}symbol'):
        symbol_id = symbol.get('id')
        try:
            symbol_code = symbol.get('code')
            symbol_name = symbol.get('name')

            if symbol_code is not None:
                code = float(symbol_code)
                if(min_code == max_code):
                    if min_code <= code <= max_code:
                        symbols[symbol_id] = symbol_name
                else:
                    if min_code <= code < max_code:
                        symbols[symbol_id] = symbol_name
        except:
            continue

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

def normalize(v):
    """Возвращает нормализованный (единичный) вектор v = (x, y)."""
    mag = math.hypot(v[0], v[1])          # length = √(x² + y²)
    if mag == 0:
        raise ValueError("Нулевой вектор нельзя нормализовать")
    return (v[0] / mag, v[1] / mag)

def angle_between_vectors(u1, u2):
    """Угол между двумя 2‑D векторами в радианах."""
    cos_angle = (u1[0] * u2[0] + u1[1] * u2[1])/(math.sqrt(u1[0]*u1[0] + u1[1]*u1[1]) * math.sqrt(u2[0]*u2[0] + u2[1]*u2[1]))

    return math.degrees(math.acos(cos_angle))
