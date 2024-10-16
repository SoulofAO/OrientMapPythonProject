import xml.etree.ElementTree as ET

# Путь к файлу HML
file_path = "TestOMP.omap"

def get_namespace(element):
    m = element.tag.find('}')
    return element.tag[:m+1] if m != -1 else ''

# Функция для извлечения информации о символах (например, "Contour")
def extract_symbols(root, namespace):
    symbols = {}

    # Проходим по всем символам с учётом пространства имён
    for symbol in root.findall(f'.//{namespace}symbol'):
        symbol_id = symbol.get('id')
        symbol_name = symbol.get('name')

        # Если символ называется "Contour" или содержит "Contour", сохраняем его
        if symbol_name and ("Contour" in symbol_name):
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

# Основная функция для парсинга XML-файла
def parse_hml(file_path):
    # Парсим XML-файл
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Извлекаем пространство имён
    namespace = get_namespace(root)

    # Извлекаем символы (например, "Contour")
    symbols = extract_symbols(root, namespace)
    print(f"Найденные символы: {symbols}")

    # Ищем объекты, которые используют эти символы, и выводим их координаты
    objects = extract_object_coords(root, symbols.keys(), namespace)

    print(f"Объекты с координатами для символов: {symbols}")
    for obj in objects:
        print(f"Symbol ID: {obj['symbol_id']}, Coordinates: {obj['coordinates']}")

# Вызов функции
parse_hml(file_path)
