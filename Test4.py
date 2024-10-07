import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull


def convex_hull_from_segments(segments):
    """
    Функция для нахождения минимальной выпуклой оболочки, включающей все заданные отрезки.

    :param segments: Список отрезков в формате [[[x1, y1], [x2, y2]], ...]
    :return: Ничего не возвращает, но строит и визуализирует выпуклую оболочку.
    """
    # Собираем все конечные точки отрезков
    points = []
    for segment in segments:
        points.append(segment[0])  # Добавляем первую точку отрезка
        points.append(segment[1])  # Добавляем вторую точку отрезка

    # Преобразуем в массив numpy
    points = np.array(points)

    # Находим выпуклую оболочку
    hull = ConvexHull(points)

    # Визуализация
    plt.plot(points[:, 0], points[:, 1], 'o', label='Points')  # Все точки
    for simplex in hull.simplices:
        plt.plot(points[simplex, 0], points[simplex, 1], 'k-', label='Convex Hull')  # Линии выпуклой оболочки

    plt.legend()
    plt.show()


# Пример использования функции
segments = [
    [[0, 0], [1, 1]],
    [[1, 2], [2, 3]],
    [[-1, -1], [0, 1]],
    [[3, 4], [5, 6]],
    [[-2, 2], [3, 1]],
]

convex_hull_from_segments(segments)
