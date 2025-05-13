import helper_functions as helper_functions
from shapely.geometry import Polygon, LineString
import numpy as np
import random
from typing import Optional, Sequence, List, Tuple

class ULine:
    def __init__(self, seed, parent, childs, shapely_polygon, line_string, points, rotation, power ):
        self.parent: Optional[ULine] = parent
        self.childs: list[ULine]  = childs
        self.shapely_polygon: Optional[Polygon] = shapely_polygon
        self.line_string : Optional[LineString] = line_string
        self.points = points.copy()
        self.color = []
        self.correct_line = True;
        self.power = float(power)
        self.rotation = float(rotation)
        self.slope_direction = "None" #None, Inside, Outside
        self.GenerateColorByLines(seed)

    def GenerateColorByLines(self, seed):
        s = seed
        for point in self.points:
            s = s + point[0]+ point[1]
        s = abs(s)
        r = s % 256  # Красный компонент
        g = (s * 2 + 50) % 256  # Зеленый компонент (с небольшим смещением)
        b = (s * 3 + 100) % 256  # Синий компонент (с большим смещением)

        self.color = [int(r),int(g),int(b)]

    def IsLineClose(self):
        return self.points[0] == self.points[-1]

    def GetRange(self):
        min_point = [1000000000000.0,1000000000000.0]
        max_point = [-1000000000000.0,-1000000000000.0]
        for point in self.points:
            max_point[0] = max(point[0], max_point[0])
            max_point[1] = max(point[1], max_point[1])

            min_point[0] = min(point[0], min_point[0])
            min_point[1] = min(point[1], min_point[1])
        return min_point, max_point


    def GetRootLine(self):
        if (self.parent):
            return self.parent.GetRootLine()
        else:
            return self

    def CheckLineParentLoop(self, visited_lines):
        if (self in visited_lines):
            return True
        else:
            if (self.parent):
                visited_lines.append(self)
                return self.parent.CheckLineParentLoop(visited_lines)
            else:
                return False

    def ContainLineInRootChain(this, check_line):
        if (check_line ==this):
            return True
        elif (this.parent):
            return this.parent.ContainLineInRootChain(check_line)
        else:
            return False

    def GetMaxDepth(self, depth = 1):
        if(len(self.childs)>0):
            max_depth = -1
            for child in self.childs:
                depth = child.GetMaxDepth(depth + 1)
                if(depth>max_depth):
                    max_depth = depth
            return max_depth
        else:
            return depth

    def GetMinAndMaxSlopeDirectionDepthByLine(self, depth=0):
        if len(self.childs) > 0:
            max_depth = -1
            min_depth = 1000000
            for child in self.childs:
                if self.slope_direction == "Outside":
                    new_depth = depth + 1
                elif self.slope_direction == "Inside":
                    new_depth = depth - 1
                else:
                    new_depth = depth + 1

                l_min_depth, l_max_depth = child.GetMinAndMaxSlopeDirectionDepthByLine(new_depth)
                if l_min_depth < min_depth:
                    min_depth = l_min_depth
                if l_max_depth > max_depth:
                    max_depth = l_max_depth
                if(new_depth>l_max_depth):
                    max_depth = new_depth
                if(new_depth<l_min_depth):
                    min_depth = new_depth
            return min_depth, max_depth
        else:
            if self.slope_direction == "Outside":
                new_depth = depth + 1
            elif self.slope_direction == "Inside":
                new_depth = depth - 1
            else:
                new_depth = depth + 1
            return new_depth, new_depth

    def GetSlopeDirectionDepthFromLineToUp(self):
        if self.slope_direction == "Outside":
            new_depth = 1
        elif self.slope_direction == "Inside":
            new_depth = -1
        else:
            new_depth = 1
        if(self.parent):
            new_depth = new_depth + self.parent.GetSlopeDirectionDepthFromLineToUp()
            return new_depth
        else:
            return new_depth


    def MergeСlosePoints(self, threshold):
        merged_line = []
        previous_point = None

        for point in self.points:
            if previous_point is None:
                merged_line.append(point)  # Добавляем первую точку
            else:
                if helper_functions.distance(previous_point, point) < threshold:
                    continue
                else:
                    merged_line.append(point)

            previous_point = point  # Обновляем предыдущую точку

        self.points = merged_line

    def CreatePoligon(self):
        if(self.CheckLineNumberPoint()):
            self.shapely_polygon = Polygon(self.points)
        else:
            self.correct_line = False

    def CreateLine(self):
        self.line_string = LineString(self.points)

    def CheckLineNumberPoint(self):
        return len(self.points)>3

    def evaluate_polygon_overlap(self, line):
        """
        Оценивает степень вложенности полигона polygon_inner в polygon_outer от 0 до 1.
        1 - polygon_inner полностью вложен в polygon_outer,
        0 - нет пересечений.

        :param polygon_outer: внешний полигон (Polygon)
        :param polygon_inner: внутренний полигон (Polygon)
        :return: float - степень вложенности от 0 до 1
        """
        t_new = []
        t1_new = []

        for x in range(len(self.points)):
            t_new.append([int(self.points[x][0]), int(self.points[x][1])])

        for x in range(len(line.points)):
            t1_new.append([int(line.points[x][0]), int(line.points[x][1])])

        outer_polygon = Polygon(t_new)  # Внешний полигон
        inner_polygon = Polygon(t1_new)

        outer_polygon = outer_polygon.buffer(0)
        inner_polygon = inner_polygon.buffer(0)

        inner_area = inner_polygon.area
        intersection_area = outer_polygon.intersection(inner_polygon).area

        if inner_area == 0:
            return 0
        return intersection_area / inner_area


def GetMinAndMaxSlopeDirectionDepthByLines(lines):
    max_depth = -1
    min_depth = 1000000000
    if(lines==None):
        return -1
    if(len(lines)==0):
        return -1
    for line in lines:
        l_min_depth, l_max_depth = line.GetMinAndMaxSlopeDirectionDepthByLine()
        if(max_depth < l_max_depth):
            max_depth = l_max_depth
        if(min_depth > l_min_depth):
            min_depth = l_min_depth
    return min(0, min_depth), max(0, max_depth)


def GetMaxDepthFromLines(lines):
    max_depth = -1
    if(lines==None):
        return -1.0
    if(len(lines)==0):
        return -1.0
    for line in lines:
        depth = line.GetMaxDepth()
        if(max_depth<depth):
            max_depth = depth
    return max_depth

def GetRootLines(lines):
    answer = []
    try:
        for line in lines:
            root_line = line.GetRootLine()
            if not root_line in answer:
                answer.append(root_line)
    except RecursionError as e:
        print("FATAL ERROR: MAX RECURSION")
        print(e)
    return answer



def rdp(points: List[Tuple[float, float]], epsilon: float) -> List[Tuple[float, float]]:
    """Ramer-Douglas-Peucker simplification algorithm"""
    if len(points) < 3:
        return points

    start, end = points[0], points[-1]
    max_dist = 0
    index = 0
    for i in range(1, len(points) - 1):
        dist = perpendicular_distance(points[i], start, end)
        if dist > max_dist:
            index = i
            max_dist = dist

    if max_dist > epsilon:
        left = rdp(points[:index + 1], epsilon)
        right = rdp(points[index:], epsilon)
        return left[:-1] + right
    else:
        return [start, end]

def perpendicular_distance(point, line_start, line_end):
    if line_start == line_end:
        return np.linalg.norm(np.array(point) - np.array(line_start))
    else:
        line = np.array(line_end) - np.array(line_start)
        t = np.dot(np.array(point) - np.array(line_start), line) / np.dot(line, line)
        t = max(0, min(1, t))
        proj = np.array(line_start) + t * line
        return np.linalg.norm(np.array(point) - proj)

def simplify_line_by_percent(line: Optional[ULine], percent: float):
    if(percent < 0):
        percent = 5.0
    if(percent>100):
        percent = 100
    best_result = simplify_line_by_percent_points(line.points, percent)
    line.points = best_result
    line.CreatePoligon()

def simplify_line_by_percent_points(points: List[Tuple[float, float]], percent: float) -> List[Tuple[float, float]]:
    """
    Упрощает линию, оставляя ~percent% точек (0–100).
    """
    if not (0 < percent <= 100):
        raise ValueError("Процент должен быть в диапазоне (0, 100].")

    target_count = max(2, int(len(points) * percent / 100))

    # Бинарный поиск подходящего epsilon
    low, high = 0.0, max_line_extent(points)
    best_result = points

    for _ in range(20):
        mid = (low + high) / 2
        simplified = rdp(points, mid)
        if len(simplified) > target_count:
            low = mid
        else:
            high = mid
            best_result = simplified
        if len(simplified) == target_count:
            break

    return best_result

def max_line_extent(points: List[Tuple[float, float]]) -> float:
    """Максимальная длина линии, используемая для грубой оценки максимального epsilon"""
    extent = 0.0
    for i in range(1, len(points)):
        extent = max(extent, np.linalg.norm(np.array(points[i]) - np.array(points[i - 1])))
    return extent




