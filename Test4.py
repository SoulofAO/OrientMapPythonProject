from shapely.geometry import Polygon
import math

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
t = [(159.17041765207983, 24.339786909778155), (22.60954416067807, 204.25175457876782), [-1.6460000000000001, 107.23800000000001], [71.858, -24.41], (159.17041765207983, 24.339786909778155)]
t1 = [(58.77313063141416, -135.92337906925488), (216.07071435466855, -77.57045280918136), (64.57740516987266, 193.75887848653062), (-97.60009178398376, 234.30677250746174), (-23.466455839321938, 215.7717545787678), [-47.72200000000001, 118.758], [-139.328, -44.706], [-112.998, -46.352000000000004], [37.85, -37.026], (44.02060092318067, -136.83543684966287), (58.77313063141416, -135.92337906925488)]     # Внутренний полигон

t_new = []
t1_new = []
for x in range(len(t)):
    t_new.append([int(t[x][0]), int(t[x][1])])

for x in range(len(t1)):
    t1_new.append([int(t1[x][0]), int(t1[x][1])])


outer_polygon_1 = Polygon(t_new)  # Внешний полигон
inner_polygon_1 = Polygon(t1_new)

result_1 = evaluate_polygon_overlap(outer_polygon_1, inner_polygon_1)
result_1 = evaluate_polygon_overlap(inner_polygon_1,outer_polygon_1)
print(f"Тест 1 (полное вложение): {result_1} (ожидаем 1)")

# Тест 2: Частичное вложение
outer_polygon_2 = Polygon([(0, 0), [5, 0], [5, 5], (10, 5), (0,5),(0,0)])
inner_polygon_2 = Polygon([(0, 0), (5, 5), [0, 5],[0,0]])  # Пересекается частично
result_2 = evaluate_polygon_overlap(outer_polygon_2, inner_polygon_2)
result_2 = evaluate_polygon_overlap(inner_polygon_2, outer_polygon_2)
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
