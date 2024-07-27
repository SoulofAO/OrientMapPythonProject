import matplotlib.pyplot as plt
from shapely.geometry import Polygon

# Пример координат для полигона
line = [(0, 0), (1, 1), (1, 0), (0, 2)]
polygon = Polygon(line)

# Создание графика
fig, ax = plt.subplots()

# Добавление полигона на график с заданием цвета
x, y = polygon.exterior.xy
ax.fill(x, y, color='blue', edgecolor='black', linewidth=1)  # Задаем цвет заливки и цвета границы

# Установка границ графика
ax.set_xlim(-1, 2)
ax.set_ylim(-1, 2)

# Отображение графика
plt.show()