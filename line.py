import helper_functions as helper_functions
from shapely.geometry import Polygon
import numpy as np
import random

class ULine:
    def __init__(self, parent, childs, shapely_polygon, line):
        self.parent = parent
        self.childs = childs
        self.shapely_polygon = shapely_polygon
        self.line = line
        self.color = []
        self.correct_line = True;
        self.power = 1.0
        self.GenerateColorByLines()


    def GenerateColorByLines(self):
        s = 0
        for point in self.line:
            s = s + point[0]+ point[1]
        s = abs(s)
        r = s % 256  # Красный компонент
        g = (s * 2 + 50) % 256  # Зеленый компонент (с небольшим смещением)
        b = (s * 3 + 100) % 256  # Синий компонент (с большим смещением)

        self.color = [int(r),int(g),int(b)]

    def GetRootLine(self):
        if (self.parent):
            return self.parent.GetRootLine()
        else:
            return self

    def CheckLineParentLoop(self, visited_lines=[]):
        if (self in visited_lines):
            return True
        else:
            if (self.GetRootLine()):
                visited_lines.append(self)
                return self.GetRootLine().CheckLineParentLoop(visited_lines)
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

    def MergeСlosePoints(self, threshold):
        merged_line = []
        previous_point = None

        for point in self.line:
            if previous_point is None:
                merged_line.append(point)  # Добавляем первую точку
            else:
                if helper_functions.distance(previous_point, point) < threshold:
                    continue
                else:
                    merged_line.append(point)

            previous_point = point  # Обновляем предыдущую точку

        self.line = merged_line

    def CreatePoligon(self):
        self.shapely_polygon = Polygon(self.line)

    def CheckLineNumberPoint(self):
        return len(self.line)>3

def GetMaxDepthFromLines(lines):
    max_depth = -1
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





