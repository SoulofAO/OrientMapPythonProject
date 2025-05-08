from shapely.geometry import LineString, Point

# Пример: линия входит в круг, но не выходит (вторая точка внутри круга)
line = LineString([(0, 0), (5.5, 5.5)])
circle = Point(5, 5).buffer(3)

intersection = line.intersection(circle)
print("Тип пересечения:", intersection.geom_type)

# Посмотрим, что внутри
if intersection.geom_type == "LineString":
    print("Координаты отрезка внутри круга:", list(intersection.coords))
