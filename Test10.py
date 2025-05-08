from shapely.geometry import LineString, Polygon

polygon = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])  # Квадрат
ray = LineString([(-5.0, 2.5), (10, 2.5)])  # Горизонтальный луч вправо

# Пересечения луча с внешним контуром полигона
intersection = ray.intersection(polygon.exterior)

# Подсчет количества пересечений
if intersection.is_empty:
    num_intersections = 0
elif intersection.geom_type == 'Point':
    num_intersections = 1
elif intersection.geom_type == 'MultiPoint':
    num_intersections = len(intersection.geoms)
    print(len(intersection.geoms))
else:
    raise Exception("Непредусмотренный тип пересечения: " + intersection.geom_type)

# Проверка по четности количества пересечений
if num_intersections % 2 == 1:
    print("Точка внутри полигона (Inside)")
else:
    print("Точка снаружи полигона (Outside)")
