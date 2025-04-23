import os
from tkinter import Tk, filedialog

# Функция для подсчёта строк в одном файле
def count_lines_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
        return 0

# Функция для обхода папки и подсчёта строк
def count_code_lines_in_folder(folder_path, extensions=(".cpp", ".h", ".py")):
    total_lines = 0
    file_count = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(extensions):
                full_path = os.path.join(root, file)
                lines = count_lines_in_file(full_path)
                total_lines += lines
                file_count += 1
    return total_lines, file_count

# Диалог выбора папки
def choose_folder():
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Выберите папку с кодом")
    return folder_selected

if __name__ == "__main__":
    folder = choose_folder()
    if folder:
        total_lines, file_count = count_code_lines_in_folder(folder)
        print(f"\n📁 Папка: {folder}")
        print(f"📄 Обработано файлов: {file_count}")
        print(f"📊 Общее количество строк кода: {total_lines}")
    else:
        print("❌ Папка не выбрана.")
