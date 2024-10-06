from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

# Создаем полигон (например, треугольник)
polygon = Polygon([(0, 0), (2, 0), (1, 1)])

# Задаем точку, которую нужно проецировать
point = Point(100, 1)

# Находим ближайшую точку на границе полигона
nearest_point = nearest_points(point, polygon)[1]

# Вычисляем вектор проекции
projection_vector = (nearest_point.x - point.x, nearest_point.y - point.y)

