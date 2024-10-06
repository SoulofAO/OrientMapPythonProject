import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from PIL import Image, ImageDraw
import helper_functions as helper_functions
import line as line_library
from shapely.ops import nearest_points

class HeightMapGenerator:
    def __init__(self):
        self.global_scale_multiplier = 0.1
        self.image_width = 2000* self.global_scale_multiplier
        self.image_height = 2000 * self.global_scale_multiplier

        self.max_width = -1000000
        self.max_height = -1000000
        self.min_width = 1000000
        self.min_height = 1000000

        self.availible_parce_data = ["Contour","Index contour"]
        self.first_level_distance = 50 * self.global_scale_multiplier
        self.merge_value = 0*self.global_scale_multiplier
        self.border_polygon = None
        self.max_border_polygon = None
        self.max_distance_to_border_polygon = 100
        self.draw_with_max_border_polygon = True

    def ParseAllFromData(self, data):
        lines = []
        current_line = []
        for line in data.splitlines():
            stripped_line = line.strip()
            points = stripped_line.split(',')

            if not helper_functions.can_convert_to_float(points[0]):
                if current_line:
                    lines.append(current_line)
                    current_line = []
            else:

                if len(points) == 2:
                    x = float(points[0]) * self.global_scale_multiplier
                    y = float(points[1]) * self.global_scale_multiplier
                    current_line.append([x, y])

        if current_line:
            lines.append(current_line)

        return lines

    def ParseLinesFromData(self, data):
        lines = []
        current_line = []
        correct_data = True;
        for line in data.splitlines():
            stripped_line = line.strip()
            points = stripped_line.split(',')
            if not helper_functions.can_convert_to_float(points[0]):
                points[0] = points[0].strip('"').strip()
                if points[0] in self.availible_parce_data:
                    correct_data = True;
                    if current_line:
                        lines.append(current_line)
                    current_line = []
                else:
                    correct_data = False
            else:

                if len(points) == 2 and correct_data:
                    x = float(points[0]) * self.global_scale_multiplier
                    y = float(points[1]) * self.global_scale_multiplier
                    current_line.append([x, y])

        if current_line:
            lines.append(current_line)

        return lines


    def SetupSizeDataFromLines(self, lines_coords):
        max_width = -1000000
        max_height = -1000000
        min_width = 1000000
        min_height = 1000000
        for line in lines_coords:
            for coord in line:
                if (max_width < coord[0]):
                    max_width= coord[0]
                if (max_height < coord[1]):
                    max_height = coord[1]
                if (min_width > coord[0]):
                    min_width = coord[0]
                if (min_height > coord[1]):
                    min_height = coord[1]

        self.width = max_width - min_width
        self.height = max_height - min_height

        self.max_width = max_width
        self.max_height = max_height
        self.min_width = min_width
        self.min_height = min_height

        unfinished_lines = []
        for line in lines_coords:
            if(line[0] != line[len(line) - 1]):
                unfinished_lines.append(line)

        self.border_polygon = Polygon([(self.min_width+1, self.min_height+1), (self.max_width-1, self.min_height+1),
                 (self.max_width-1, self.max_height-1),
                 (self.min_width+1, self.max_height-1)])
        self.max_border_polygon = Polygon([(self.min_width+self.max_distance_to_border_polygon, self.min_height+self.max_distance_to_border_polygon),
                                           (self.max_width-self.max_distance_to_border_polygon, self.min_height+self.max_distance_to_border_polygon),
                 (self.max_width-self.max_distance_to_border_polygon, self.max_height-self.max_distance_to_border_polygon),
                 (self.min_width+self.max_distance_to_border_polygon, self.max_height-self.max_distance_to_border_polygon)])

    def DebugDrawLines(self,lines):
        if(not self.draw_with_max_border_polygon):
            min_x = min(min(point[0] for point in line.line) for line in lines)
            max_x = max(max(point[0] for point in line.line) for line in lines)
            min_y = min(min(point[1] for point in line.line) for line in lines)
            max_y = max(max(point[1] for point in line.line) for line in lines)

            # Увеличиваем размеры изображения с учетом отрицательных координат
            width = int(max_x - min_x + 1 )
            height = int(max_y - min_y + 1)

            # Создаем новое изображение с черным фоном
            image = Image.new("RGB", (width, height), "black")
            draw = ImageDraw.Draw(image)

            # Смещение для корректного отображения отрицательных координат
            offset_x = -min_x
            offset_y = -min_y

            for line in lines:
                if len(line.line) >= 2:  # Проверяем, что есть как минимум две точки для рисования линии
                    # Преобразуем массив координат в плоский список с учетом смещения и округляем до int
                    flat_coords = [(int(point[0] + offset_x), int(point[1] + offset_y)) for point in line.line]
                    draw.line(flat_coords, fill="white", width=2)  # Рисуем линию

            x, y = self.border_polygon.exterior.xy
            border_coords = []
            for length in range(len(x)):
                border_coords.append((int(x[length] + offset_x), int(y[length] + offset_y)))
            draw.line(border_coords, fill="red", width=2)
            image.save("lines_image.png")
            image.show()
        else:
            min_x = min(min(point[0] for point in line.line) for line in lines)
            max_x = max(max(point[0] for point in line.line) for line in lines)
            min_y = min(min(point[1] for point in line.line) for line in lines)
            max_y = max(max(point[1] for point in line.line) for line in lines)

            # Увеличиваем размеры изображения с учетом отрицательных координат
            width = int(max_x - min_x + 1)
            height = int(max_y - min_y + 1)

            # Создаем новое изображение с черным фоном
            image = Image.new("RGB", (width+1+self.max_distance_to_border_polygon, height+1+self.max_distance_to_border_polygon), "black")
            draw = ImageDraw.Draw(image)

            offset_x = -min_x
            offset_y = -min_y

            for line in lines:
                if len(line.line) >= 2:
                    flat_coords = [(int(point[0] + offset_x+self.max_distance_to_border_polygon), int(point[1] + offset_y+self.max_distance_to_border_polygon)) for point in line.line]
                    draw.line(flat_coords, fill="white", width=2)

            x, y = self.border_polygon.exterior.xy
            border_coords = []
            for length in range(len(x)):
                border_coords.append((int(x[length] + offset_x+self.max_distance_to_border_polygon), int(y[length] + offset_y+self.max_distance_to_border_polygon)))
            draw.line(border_coords, fill="red", width=2)

            x, y = self.max_border_polygon.exterior.xy
            max_border_coords = []
            for length in range(len(x)):
                max_border_coords.append((int(x[length] + offset_x + self.max_distance_to_border_polygon), int(y[length] + offset_y+self.max_distance_to_border_polygon)))
            draw.line(max_border_coords, fill="green", width=2)

            image.save("lines_image.png")
            image.show()


    from shapely.geometry import Polygon, Point
    import numpy as np

    def direction_point_from_border_polygon(self, border_polygon, point):
        coords = list(border_polygon.exterior.coords)
        point = Point(point)
        min_distance = float('inf')
        projection_point = None
        closest_segment = None

        for i in range(len(coords) - 1):
            line_segment = [Point(coords[i]), Point(coords[i + 1])]
            projection = self.project_point_onto_line_segment(point, line_segment)
            distance = point.distance(projection)

            if distance < min_distance:
                min_distance = distance
                projection_point = projection
                closest_segment = LineString(line_segment)

        return projection_point, closest_segment

    def project_point_onto_line_segment(self, point, line_segment):
        p1, p2 = line_segment
        line_vec = np.array([p2.x - p1.x, p2.y - p1.y])
        point_vec = np.array([point.x - p1.x, point.y - p1.y])

        line_len_squared = np.dot(line_vec, line_vec)
        if line_len_squared == 0:
            return p1

        t = np.dot(point_vec, line_vec) / line_len_squared
        t = max(0, min(1, t))

        projection_x = p1.x + t * line_vec[0]
        projection_y = p1.y + t * line_vec[1]

        return Point(projection_x, projection_y)

    def GenerateLinesByLineData(self,lines_data):
        lines_coords = []
        for line_data in lines_data:
            updated_coords = []
            for coord in line_data:
                x = coord[0]
                y = coord[1]
                updated_coords.append([x,y])
            lines_coords.append(updated_coords)
        self.SetupSizeDataFromLines(lines_coords)
        return self.GeneratedLineByCoords(lines_coords)

    def FixLine(self, line):
        if (line[0] != line[len(line) - 1]):
            projection_point, closest_segment =self.direction_point_from_border_polygon(self.border_polygon, line[0])
            x_coordinate_start = projection_point.x
            y_coordinate_start = projection_point.y
            line.insert(0,(x_coordinate_start,y_coordinate_start))

            projection_point, closest_segment = self.direction_point_from_border_polygon(self.border_polygon, line[len(line) - 1])
            x_coordinate_end = projection_point.x
            y_coordinate_end = projection_point.y
            line.append((x_coordinate_end, y_coordinate_end))

    def GeneratedLineByCoords(self, lines_coords):
        lines = []
        for line in lines_coords:
            self.FixLineCoords(line)
            new_line = line_library.ULine(None, [], None, line)
            new_line.MergeСlosePoints(self.merge_value)
            if(new_line.CheckLineNumberPoint()):
                new_line.CreatePoligon()
                lines.append(new_line)
        uncheck_lines = lines.copy()
        partly_check_lines = []
        remove_list = []
        while len(partly_check_lines)>0 or len(uncheck_lines)>0:
            if(len(partly_check_lines)<=0):
                partly_check_lines.append(uncheck_lines[0])
                uncheck_lines.remove(uncheck_lines[0])
            check_line = partly_check_lines[0]
            min_parent_area = 1000000000
            min_parent = None
            for uncheck_line in uncheck_lines:
                if(check_line.shapely_polygon.contains(uncheck_line.shapely_polygon)):
                    if(uncheck_line.parent):
                        if check_line.parent.shapely_polygon.area > uncheck_line.shapely_polygon.area:
                            uncheck_line.parent.childs.remove(check_line)
                            uncheck_line.parent = check_line
                            check_line.childs.append(uncheck_line)
                    else:
                        uncheck_line.parent = check_line
                        check_line.childs.append(uncheck_line)
                else:
                    if(min_parent_area>uncheck_line.shapely_polygon.area):
                        min_parent = uncheck_line
                        min_parent_area = uncheck_line.shapely_polygon.area
            if(min_parent):
                check_line.parent = min_parent
                check_line.parent.childs.append(check_line)

            for check_line_child in check_line.childs:
                if(not check_line_child in remove_list):
                    partly_check_lines.append(check_line_child)
                    uncheck_lines.remove(check_line_child)
            partly_check_lines.remove(check_line)
            remove_list.append(check_line)
        return lines

    def DrawPlotHeightMap(self, lines):
        max_depth = line_library.GetMaxDepthFromLines(lines)
        print("Depth equal " + str(max_depth))
        image = Image.new("RGB", (int(self.width + self.first_level_distance), int(self.height + self.first_level_distance)), "black")
        draw = ImageDraw.Draw(image)
        root_lines = line_library.GetRootLines(lines)

        k = 0
        for y in range(int(self.height + self.first_level_distance)):
            for x in range(int(self.width + self.first_level_distance)):
                helper_functions.print_progress_bar(k,int(self.height)*int(self.width))
                point = Point(int(x+self.min_width - self.first_level_distance/2 ), int(y+self.min_height - self.first_level_distance/2))
                intensity = 0
                owner_line = None
                min_poligin_length = 100000000000000
                for line in lines:
                    if line.shapely_polygon.contains(point):
                        intensity += 1
                        if(min_poligin_length>line.shapely_polygon.length):
                            min_poligin_length = line.shapely_polygon.length
                            owner_line = line
                if owner_line:
                    distance_to_owner_poligon = point.distance(owner_line.shapely_polygon.exterior)
                    min_distance_to_child_poligon = 100000000000000
                    child_line = None
                    for child in owner_line.childs:
                        if min_distance_to_child_poligon> point.distance(child.shapely_polygon.exterior):
                            min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                            child_line = child
                    distance_to_child_poligon = min_distance_to_child_poligon

                    normalize_distance_to_child_poligon = distance_to_child_poligon/(distance_to_child_poligon+ distance_to_owner_poligon )
                    normalize_distance_to_owner_poligon = distance_to_owner_poligon / (
                                distance_to_child_poligon + distance_to_owner_poligon)
                    intensity +=1-normalize_distance_to_child_poligon
                else:
                    min_distance_to_child_poligon = 100000000000000
                    child_line = None
                    for child in root_lines:
                        if min_distance_to_child_poligon> point.distance(child.shapely_polygon.exterior):
                            min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                            child_line = child
                    distance_to_child_poligon = min_distance_to_child_poligon

                    normalize_distance_to_child_poligon = distance_to_child_poligon/(distance_to_child_poligon+ self.first_level_distance)
                    intensity +=1-normalize_distance_to_child_poligon


                white_intensity = min(255, int(intensity * 255/max_depth))  # Увеличиваем интенсивность
                draw.point((int(x), int(y)), fill=(white_intensity, white_intensity, white_intensity))
                k = k + 1


        image.show()


    def Launch(self):
        data = helper_functions.ChooseFile()
        if(data):
            data_all = self.ParseAllFromData(data)
            data_lines = self.ParseLinesFromData(data)
            lines = self.GenerateLinesByLineData(data_lines)
            line_library.PrintLinesFromLines(lines)
            print(self.width, self.height)
            self.DebugDrawLines(lines)

heightmap_generator = HeightMapGenerator()
heightmap_generator.Launch()