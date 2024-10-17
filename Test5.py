import math
from shapely.geometry import Point, Polygon, LineString
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
    length = (normal[0] ** 2 + normal[1] ** 2) ** 0.5
    return (normal[0] / length, normal[1] / length)  # Возвращаем нормализованный вектор


class ULine:
    def __init__(self, parent, childs, shapely_polygon, points):
        self.parent = parent
        self.childs = childs
        self.shapely_polygon = shapely_polygon  # Полигон shapely
        self.points = points.copy()  # [x1, y1], [x2, y2], ..., точки полигона

    def get_segments(self):
        """Возвращает список отрезков границы полигона."""
        coords = list(self.shapely_polygon.exterior.coords)
        return [(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]

    def is_looking_at_polygon(self, rotation, origin):
        """
        Проверяем, смотрит ли луч, исходящий из точки origin и заданный углом rotation, на границу полигона.
        :param rotation: угол в радианах (-pi до pi), задающий направление луча
        :param origin: начальная точка луча (например, (0, 0))
        :return: True если луч направлен на границу полигона, False если нет
        """
        # Получаем отрезки границы полигона
        segments = self.get_segments()

        # Находим ближайшую точку на границе полигона от заданной точки
        closest_segment, closest_point = find_closest_segment(origin, segments)
        normal = normal_vector(closest_segment)

        # Находим точку на конце нормали
        point = (closest_point.x + normal[0], closest_point.y + normal[1])

        # Преобразуем угол в координаты точки на конце луча
        ray_distance = 1000  # длина луча
        end_x = point[0] + ray_distance * math.cos(rotation)
        end_y = point[1] + ray_distance * math.sin(rotation)

        # Создаем линию (луч) от ближайшей точки в направлении угла
        ray = LineString([(point[0], point[1]), (end_x, end_y)])

        # Проверяем, пересекает ли этот луч границы полигона
        if ray.intersects(self.shapely_polygon.exterior):
            return True  # Если пересекает границу, возвращаем True

        return False  # Если не пересекает границу


# Пример использования:
polygon_points = [(0, 0), (4, 0), (4, 4), (0, 4)]  # Простой квадратный полигон
polygon = Polygon(polygon_points)

line = ULine(None, None, polygon, polygon_points)

# Угол 45 градусов (в радианах)
rotation_inside = math.pi / 4  # 45 degrees
rotation_outside = -math.pi   # -45 degrees

# Проверка направления
is_looking_inside = line.is_looking_at_polygon(rotation_inside, origin=(2, 2))  # Внутри
is_looking_outside = line.is_looking_at_polygon(rotation_outside, origin=(-1, -1))  # Снаружи

print(f'The point is looking at the polygon (inside rotation): {is_looking_inside}')  # Ожидается True
print(f'The point is looking at the polygon (outside rotation): {is_looking_outside}')  # Ожидается False

