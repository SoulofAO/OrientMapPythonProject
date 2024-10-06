from shapely.geometry import Point, Polygon
import numpy as np

# Класс LineMerger
class LineMerger:
    def __init__(self, border_polygon):
        self.border_polygon = Polygon(border_polygon)

    def distance(self, p1, p2):
        return np.linalg.norm(np.array(p1) - np.array(p2))

    def merge_near_lines(self, lines):
        availible_lines = lines.copy()
        merged_lines = []

        while len(availible_lines) > 0:
            line = availible_lines.pop(0)
            merged = True

            while merged:
                merged = False
                for test_line in availible_lines:
                    if (self.border_polygon.contains(Point(test_line[0])) and
                        self.border_polygon.contains(Point(test_line[-1]))):

                        dist_start = self.distance(line[-1], test_line[0])
                        dist_end = self.distance(line[-1], test_line[-1])

                        if dist_start < dist_end and dist_start < 1.0:
                            line += test_line[1:]
                            availible_lines.remove(test_line)
                            merged = True
                            break
                        elif dist_end < 1.0:
                            line += test_line[::-1][1:]
                            availible_lines.remove(test_line)
                            merged = True
                            break

                # Проверяем, если линия зациклена (первая точка совпадает с последней)
                if line[0] == line[-1]:
                    merged_lines.append(line)
                    merged = False
                    break

            # Если линия не зациклилась, но больше нет с чем объединять, она остается как есть
            if line[0] != line[-1]:
                merged_lines.append(line)

        return merged_lines

# Пример использования
if __name__ == "__main__":
    border_polygon = [(0, 0), (10, 0), (10, 10), (0, 10)]  # Пример границы полигона
    lines = [
        [[1, 1], [2, 2],[1,1]],
        [[4,4],[5,5]],
        [[6,6],[3,3]]# Первая линия
    ]

    merger = LineMerger(border_polygon)
    merged_lines = merger.merge_near_lines(lines)

    print("Результат объединенных цикличных линий:")
    for line in merged_lines:
        print(line)
