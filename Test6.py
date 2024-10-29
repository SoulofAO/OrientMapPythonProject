import random
import time

class OctreeNode:
    def __init__(self, boundary, capacity):
        self.boundary = boundary  # (x_min, y_min, x_max, y_max)
        self.capacity = capacity  # Максимальное количество точек в узле
        self.points = []  # Точки в текущем узле
        self.divided = False  # Разделен ли узел
        self.children = []  # Дочерние узлы

    def subdivide(self):
        x_min, y_min, x_max, y_max = self.boundary
        mid_x = (x_min + x_max) / 2
        mid_y = (y_min + y_max) / 2

        # Создаем 4 дочерних узла
        self.children.append(OctreeNode((x_min, y_min, mid_x, mid_y), self.capacity))  # NW
        self.children.append(OctreeNode((mid_x, y_min, x_max, mid_y), self.capacity))  # NE
        self.children.append(OctreeNode((x_min, mid_y, mid_x, y_max), self.capacity))  # SW
        self.children.append(OctreeNode((mid_x, mid_y, x_max, y_max), self.capacity))  # SE

        self.divided = True

    def insert(self, point):
        if not self.contains(point):
            return False

        if len(self.points) < self.capacity:
            self.points.append(point)
            return True
        else:
            if not self.divided:
                self.subdivide()

            for child in self.children:
                if child.insert(point):
                    return True

        return False

    def contains(self, point):
        x, y = point
        x_min, y_min, x_max, y_max = self.boundary
        return x_min <= x <= x_max and y_min <= y <= y_max

    def query(self, range, found_points):
        if not self.intersects(range):
            return

        for point in self.points:
            if range_contains(range, point):
                found_points.append(point)

        if self.divided:
            for child in self.children:
                child.query(range, found_points)

    def intersects(self, range):
        x_min1, y_min1, x_max1, y_max1 = self.boundary
        x_min2, y_min2, x_max2, y_max2 = range
        return not (x_min1 > x_max2 or x_max1 < x_min2 or y_min1 > y_max2 or y_max1 < y_min2)

    def print_tree(self, level=0):
        indent = "  " * level
        print(f"{indent}Node at {self.boundary} with {len(self.points)} points")
        if self.divided:
            for i, child in enumerate(self.children):
                print(f"{indent} Child {i + 1}:")
                child.print_tree(level + 1)


def range_contains(range, point):
    x_min, y_min, x_max, y_max = range
    x, y = point
    return x_min <= x <= x_max and y_min <= y <= y_max


class Octree:
    def __init__(self, boundary, capacity):
        self.root = OctreeNode(boundary, capacity)

    def insert(self, point):
        self.root.insert(point)

    def query(self, range):
        found_points = []
        self.root.query(range, found_points)
        return found_points
    def print_tree(self):
        self.root.print_tree()


def generate_random_points(num_points, x_range, y_range):
    return [(random.uniform(*x_range), random.uniform(*y_range)) for _ in range(num_points)]


def standard_search(points, search_range):
    found_points = []
    for point in points:
        if range_contains(search_range, point):
            found_points.append(point)
    return found_points


if __name__ == "__main__":
    # Генерация случайных точек
    num_points = 10000  # Количество точек
    x_range = (0, 100)
    y_range = (0, 100)

    points = generate_random_points(num_points, x_range, y_range)

    # Определяем диапазон поиска
    search_range = (15, 15, 35, 35)  # (x_min, y_min, x_max, y_max)

    # Стандартный поиск
    start_time = time.time()
    found_points_standard = standard_search(points, search_range)
    standard_time = time.time() - start_time
    print(f"Стандартный поиск найдено точек: {len(found_points_standard)} за {standard_time:.6f} секунд")

    # Поиск с использованием Octree
    octree = Octree((0, 0, 100, 100), capacity=4)
    for point in points:
        octree.insert(point)

    start_time = time.time()
    found_points_octree = octree.query(search_range)
    octree_time = time.time() - start_time
    print(f"Поиск в Octree найдено точек: {len(found_points_octree)} за {octree_time:.6f} секунд")

    start_time = time.time()
    found_points_standard = standard_search(points, search_range)
    standard_time = time.time() - start_time
    print(f"Стандартный поиск найдено точек: {len(found_points_standard)} за {standard_time:.6f} секунд")
    
    start_time = time.time()
    found_points_octree = octree.query(search_range)
    octree_time = time.time() - start_time
    print(f"Поиск в Octree найдено точек: {len(found_points_octree)} за {octree_time:.6f} секунд")



