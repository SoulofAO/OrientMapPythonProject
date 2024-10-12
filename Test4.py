from shapely.geometry import Polygon

def evaluate_polygon_overlap(polygon_outer, polygon_inner):
    """
    Оценивает степень вложенности полигона polygon_inner в polygon_outer от 0 до 1.
    1 - polygon_inner полностью вложен в polygon_outer,
    0 - нет пересечений.

    :param polygon_outer: внешний полигон (Polygon)
    :param polygon_inner: внутренний полигон (Polygon)
    :return: float - степень вложенности от 0 до 1
    """
    inner_area = polygon_inner.area
    intersection_area = polygon_outer.intersection(polygon_inner).area

    if inner_area == 0:
        return 0
    return intersection_area / inner_area


# Тест 1: Полное вложение
outer_polygon_1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])  # Внешний полигон
inner_polygon_1 = Polygon([(2, 2), (8, 2), (8, 8), (2, 8)])      # Внутренний полигон
result_1 = evaluate_polygon_overlap(outer_polygon_1, inner_polygon_1)
result_1 = evaluate_polygon_overlap(inner_polygon_1,outer_polygon_1)
print(f"Тест 1 (полное вложение): {result_1} (ожидаем 1)")

# Тест 2: Частичное вложение
outer_polygon_2 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
inner_polygon_2 = Polygon([(5, 5), (15, 5), (15, 15), (5, 15)])  # Пересекается частично
result_2 = evaluate_polygon_overlap(outer_polygon_2, inner_polygon_2)
print(f"Тест 2 (частичное вложение): {result_2} (ожидаем значение между 0 и 1)")

# Тест 3: Нет пересечения
outer_polygon_3 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
inner_polygon_3 = Polygon([(20, 20), (30, 20), (30, 30), (20, 30)])  # Полностью вне
result_3 = evaluate_polygon_overlap(outer_polygon_3, inner_polygon_3)
print(f"Тест 3 (нет вложения): {result_3} (ожидаем 0)")

# Тест 4: Совпадение полигонов
outer_polygon_4 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])  # Полный матч
inner_polygon_4 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])  # Полигон такой же
result_4 = evaluate_polygon_overlap(outer_polygon_4, inner_polygon_4)
print(f"Тест 4 (совпадение полигонов): {result_4} (ожидаем 1)")

# Тест 5: Внутренний полигон вне внешнего
outer_polygon_5 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
inner_polygon_5 = Polygon([(-5, -5), (-1, -5), (-1, -1), (-5, -1)])  # Полностью вне
result_5 = evaluate_polygon_overlap(outer_polygon_5, inner_polygon_5)
print(f"Тест 5 (внешний полигон вне): {result_5} (ожидаем 0)")
