import zipfile
import os
import json
import xml.etree.ElementTree as ET

# Путь к OCD файлу
ocd_file_path = "example.ocd"
extracted_dir = "extracted_ocd_files"

# 1. Распаковываем файл OCD (ZIP-архив)
with zipfile.ZipFile(ocd_file_path, 'r') as zip_ref:
    zip_ref.extractall(extracted_dir)  # Извлекаем файлы во временную директорию

# 2. Просматриваем содержимое директории
for root, dirs, files in os.walk(extracted_dir):
    for file in files:
        file_path = os.path.join(root, file)

        # Если файл имеет расширение .plist или .json, попробуем его разобрать
        if file.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
                print("JSON data:", data)
        elif file.endswith('.xml') or file.endswith('.plist'):
            tree = ET.parse(file_path)
            root = tree.getroot()
            print("XML root tag:", root.tag)
            # Выводим структуру XML
            for child in root:
                print(child.tag, child.attrib)

