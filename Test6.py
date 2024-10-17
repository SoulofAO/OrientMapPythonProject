from shapely.geometry import Point, LineString
from shapely.ops import nearest_points

def find_closest_segment(point, segments):
    """Find the closest segment to the point."""
    closest_segment = None
    closest_point = None
    min_distance = float('inf')

    # Создаем объект точки
    shapely_point = Point(point)

    for segment in segments:
        line = LineString(segment)
        # Находим ближайшую точку на отрезке
        nearest_point = nearest_points(shapely_point, line)[1]  # Ближайшая точка на отрезке
        distance = shapely_point.distance(line)  # Расстояние до отрезка

        if distance < min_distance:
            min_distance = distance
            closest_segment = line
            closest_point = nearest_point

    return closest_segment, closest_point

def normal_vector(segment):
    """Calculate the outward normal vector of the segment."""
    # Получаем координаты отрезка
    start, end = segment.coords[0], segment.coords[1]
    # Вычисляем вектор отрезка
    segment_vector = (end[0] - start[0], end[1] - start[1])
    # Вычисляем нормаль (перпендикулярный вектор)
    normal = (-segment_vector[1], segment_vector[0])  # Вектор нормали
    # Нормализуем вектор
    length = (normal[0]**2 + normal[1]**2) ** 0.5
    return (normal[0] / length, normal[1] / length)  # Возвращаем нормализованный вектор

# Пример использования
point = (1, 2)  # Точка, для которой нужно найти нормаль
segments = [
    [(0, 0), (3, 0)],
    [(1, 0), (1, 4)],
    [(0, 0), (0, 3)],
]

closest_segment, closest_point = find_closest_segment(point, segments)
normal = normal_vector(closest_segment)

print(f"Closest segment: {closest_segment}")
print(f"Projection point: {closest_point}")
print(f"Normal vector: {normal}")
