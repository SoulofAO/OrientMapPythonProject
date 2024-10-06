import helper_functions as helper_functions
from shapely.geometry import Polygon
import numpy as np

class ULine:
    def __init__(self, parent, childs, shapely_polygon, line):
        self.parent = parent
        self.childs = childs
        self.shapely_polygon = shapely_polygon
        self.line = line

    def GetRootLine(this):
        if (this.parent):
            return this.parent.GetRootLine()
        else:
            return this

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
    for line in lines:
        root_line = line.GetRootLine()
        if not root_line in answer:
            answer.append(root_line)
    return answer

def PrintLinesFromLine(uline, level=0):
    indent = "    " * level  # Создаем отступ в зависимости от уровня
    print(f"{indent}Line: {uline.line}, Polygon: {uline.shapely_polygon}")

    for child in uline.childs:
        PrintLinesFromLine(child, level + 1)

def PrintLinesFromLines(ulines, level=0):
    root_lines = GetRootLines(ulines)
    for line in root_lines:
        PrintLinesFromLine(line)

