import random
import time
import math
from line import ULine
from typing import Optional, Sequence, Dict, List,Tuple

class UTestLine:
    def __init__(self, points):
        self.points = points

class OctreeNode:
    def __init__(self, boundary, capacity):
        self.boundary = boundary  # (x_min, y_min, x_max, y_max)
        self.capacity = capacity
        self.lines = []  # Список линий, где каждая линия - это список точек
        self.divided = False
        self.children = []

    def subdivide(self):
        x_min, y_min, x_max, y_max = self.boundary
        mid_x = (x_min + x_max) / 2
        mid_y = (y_min + y_max) / 2

        # Создание 4 дочерних узлов
        self.children.append(OctreeNode((x_min, y_min, mid_x, mid_y), self.capacity))  # NW
        self.children.append(OctreeNode((mid_x, y_min, x_max, mid_y), self.capacity))  # NE
        self.children.append(OctreeNode((x_min, mid_y, mid_x, y_max), self.capacity))  # SW
        self.children.append(OctreeNode((mid_x, mid_y, x_max, y_max), self.capacity))  # SE
        self.divided = True

    def insert(self, line):
        if not any(self.contains(point, self.boundary) for point in line.points):
            return False

        if len(self.lines) < self.capacity:
            self.lines.append(line)
            return True
        else:
            if not self.divided:
                self.subdivide()

            for child in self.children:
                if child.insert(line):
                    return True

        return False

    def contains(self, point, range):
        x, y = point
        x_min, y_min, x_max, y_max = range
        return x_min <= x <= x_max and y_min <= y <= y_max

    def query(self, range, found_lines):
        if not self.intersects(range):
            return

        for line in self.lines:
            if any(self.contains(point, range) for point in line.points):
                found_lines.append(line)

        if self.divided:
            for child in self.children:
                child.query(range, found_lines)

    def intersects(self, range):
        x_min1, y_min1, x_max1, y_max1 = self.boundary
        x_min2, y_min2, x_max2, y_max2 = range
        return not (x_min1 > x_max2 or x_max1 < x_min2 or y_min1 > y_max2 or y_max1 < y_min2)

    def nearest_neighbor_search(self, target, best_line=None, best_dist=float('inf')):
        for line in self.lines:
            for i in range(len(line.points) - 1):
                segment_dist = distance_to_segment(target, line.points[i], line.points[i + 1])
                if segment_dist < best_dist:
                    best_dist = segment_dist
                    best_line = line

        if self.divided:
            self.children.sort(key=lambda child: distance_to_boundary(target, child.boundary))
            for child in self.children:
                if distance_to_boundary(target, child.boundary) < best_dist:
                    best_line, best_dist = child.nearest_neighbor_search(target, best_line, best_dist)

        return best_line, best_dist


def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def distance_to_segment(point, seg_start, seg_end):
    px, py = point
    x1, y1 = seg_start
    x2, y2 = seg_end
    dx, dy = x2 - x1, y2 - y1
    if dx == dy == 0:  # seg_start == seg_end
        return distance(point, seg_start)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    nearest = (x1 + t * dx, y1 + t * dy)
    return distance(point, nearest)

def distance_to_boundary(point, boundary):
    x, y = point
    x_min, y_min, x_max, y_max = boundary
    dx = max(x_min - x, 0, x - x_max)
    dy = max(y_min - y, 0, y - y_max)
    return math.sqrt(dx * dx + dy * dy)


class Octree:
    def __init__(self, boundary, capacity):
        self.root = OctreeNode(boundary, capacity)

    def insert(self, line):
        self.root.insert(line)

    def query(self, range):
        found_lines = []
        self.root.query(range, found_lines)
        return found_lines

    def print_tree(self):
        self.root.print_tree()

    def nearest_neighbor(self, target):
        return self.root.nearest_neighbor_search(target)

    def nearest_neighbor_in_range(self, target, radius) -> Tuple[Optional[ULine], float]:
        nearest_line, dist = self.root.nearest_neighbor_search(target)
        if dist < radius:
            return nearest_line, dist
        else:
            return None, -1.0


def test_query_within_range():
    octree = Octree(boundary=(0, 0, 100, 100), capacity=4)
    line = UTestLine([(10, 10), (20, 20)])
    octree.insert(line)
    found_lines = octree.query((5, 5, 25, 25))
    print("test_query_within_range"," Sucsess" if len(found_lines)>0 else " Fail")
    print(found_lines)

def test_query_outside_range():
    octree = Octree(boundary=(0, 0, 100, 100), capacity=4)
    line = UTestLine([(10, 10), (20, 20)])
    octree.insert(line)
    found_lines = octree.query((50, 50, 60, 60))
    print("test_query_out_range", " Sucsess" if len(found_lines) > 0 else " Fail")
    print(found_lines)

def test_nearest_neighbor_search():
    octree = Octree(boundary=(0, 0, 100, 100), capacity=4)
    line1 = [(10, 10), (20, 20)]
    line2 = [(70, 70), (80, 80)]
    octree.insert(UTestLine(line1))
    octree.insert(UTestLine(line2))
    nearest_line, dist = octree.nearest_neighbor((15, 15))
    print("test_nearest_neighbor_search", " Sucsess" if nearest_line else " Fail")
    print(nearest_line, dist)

def test_distance_to_boundary():
    boundary = (10, 10, 20, 20)
    dist = distance_to_boundary((25, 15), boundary)
    print("Test distance to boundary:", "Pass" if round(dist, 2) == 5 else "Fail")

def test_distance_to_segment():
    seg_start, seg_end = (10, 10), (20, 20)
    dist1 = distance_to_segment((15, 15), seg_start, seg_end)
    dist2 = distance_to_segment((5, 5), seg_start, seg_end)
    print("Test distance to segment on line:", "Pass" if round(dist1, 2) == 0 else "Fail")
    print("Test distance to segment outside line:", "Pass" if round(dist2, 2) == round(math.sqrt(50), 2) else "Fail")

# Run tests
if __name__ == "__main__":
    test_query_within_range()
    test_query_outside_range()
    test_nearest_neighbor_search()
    test_distance_to_boundary()
    test_distance_to_segment()


