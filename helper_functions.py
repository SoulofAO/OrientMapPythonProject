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

    file_path = filedialog.askopenfilename(title="Выберите файл BNA",
                                               filetypes=[("BNA files", "*.bna"), ("All files", "*.*")])

    if file_path:
        print(f"Выбранный файл: {file_path}")
        return file_path, ReadFile(file_path)
    else:
        print("Файл не выбран.")
        return None, None;
