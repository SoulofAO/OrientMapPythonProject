import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, LineString
from PIL import Image, ImageDraw
import helper_functions as helper_functions
import line as line_library
from shapely.ops import nearest_points
import networkx as nx
import os
import threading
import Delegates

class UHeightMapGenerator:
    def __init__(self):
        self.bna_file_path = "None"
        self.global_scale_multiplier = 0.2

        self.max_width = -1000000
        self.max_height = -1000000
        self.min_width = 1000000
        self.min_height = 1000000

        self.availible_parce_data = ["Contour","Index contour"]
        self.first_level_distance = 50 * self.global_scale_multiplier
        self.merge_point_value = 0*self.global_scale_multiplier
        self.max_merge_line_value = 1000*self.global_scale_multiplier

        self.border_polygon = None
        self.border_distance = 20;
        self.max_border_polygon = None
        self.max_distance_to_border_polygon = 100
        self.draw_with_max_border_polygon = True
        self.hight_find_direction = "both"
        self.draw_debug_lines = True;

        self.apply_unborder_draw = True
        self.apply_merge_line_value = True
        self.end_cook_delegate = Delegates.UDelegate()
        self.cook_image = None

        self.save_tag = ['bna_file_path', 'global_scale_multiplier', 'first_level_distance', 'merge_point_value', 'max_merge_line_value',
                        'border_distance', 'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                         'hight_find_direction', 'apply_unborder_draw', 'apply_merge_line_value']
        self.ui_show_tag = ['bna_file_path', 'global_scale_multiplier', 'first_level_distance', 'merge_point_value', 'max_merge_line_value',
                          'border_distance', 'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                           'hight_find_direction', 'apply_unborder_draw', 'apply_merge_line_value']
        self.lines = []
    def to_dict(self):
        """Сериализуем только параметры, указанные в _save_tag."""
        return {k: getattr(self, k) for k in self.save_tag}

    def from_dict(self, data):
        """Десериализация параметров из словаря в объект."""
        for k, v in data.items():
            if k in self.save_tag:
                setattr(self, k, v)

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

        self.border_polygon = Polygon([(self.min_width+self.border_distance, self.min_height+self.border_distance),
                                       (self.max_width-self.border_distance, self.min_height+self.border_distance),
                 (self.max_width-self.border_distance, self.max_height-self.border_distance),
                 (self.min_width+self.border_distance, self.max_height-self.border_distance)])
        self.max_border_polygon = Polygon([(self.min_width-self.max_distance_to_border_polygon, self.min_height-self.max_distance_to_border_polygon),
                                           (self.max_width+self.max_distance_to_border_polygon, self.min_height-self.max_distance_to_border_polygon),
                 (self.max_width+self.max_distance_to_border_polygon, self.max_height+self.max_distance_to_border_polygon),
                 (self.min_width-self.max_distance_to_border_polygon, self.max_height+self.max_distance_to_border_polygon)])



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

                    draw.line(flat_coords, fill=(line.color[0],line.color[1],line.color[2]), width=2)  # Рисуем линию с цветом из line.color

            x, y = self.border_polygon.exterior.xy
            border_coords = []
            for length in range(len(x)):
                border_coords.append((int(x[length] + offset_x), int(y[length] + offset_y)))
            draw.line(border_coords, fill="red", width=2)
            image.save("lines_image.png")
            self.cook_image = image
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
            image = Image.new("RGB", (width+1+self.max_distance_to_border_polygon*2, height+1+self.max_distance_to_border_polygon*2), "black")
            draw = ImageDraw.Draw(image)

            offset_x = -min_x
            offset_y = -min_y

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

            for line in lines:
                if len(line.line) >= 2:  # Проверяем, что есть как минимум две точки для рисования линии
                    # Преобразуем массив координат в плоский список с учетом смещения и округляем до int
                    flat_coords = [(int(point[0] + offset_x+self.max_distance_to_border_polygon), int(point[1] + offset_y+self.max_distance_to_border_polygon)) for point in line.line]

                    draw.line(flat_coords, fill=(line.color[0], line.color[1], line.color[2]),
                              width=2)  # Рисуем линию с цветом из line.color

            image.save("lines_image.png")
            self.cook_image = image
            return image

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

    def create_graph_from_polygon(self, polygon, direction='both'):
        """
        Создает граф из вершин полигона.
        Ребра соединяют соседние вершины с учетом направления движения.

        :param direction: Направление движения. Возможные значения:
                          'both' - двустороннее движение,
                          'forward' - однонаправленное по часовой стрелке,
                          'backward' - однонаправленное против часовой стрелки.
        """
        G = nx.DiGraph() if direction != 'both' else nx.Graph()  # Выбор типа графа: направленный или нет

        # Добавляем вершины полигона в граф
        for i in range(len(polygon.exterior.coords)):
            G.add_node(i, coord=polygon.exterior.coords[i])

        # Добавляем рёбра между соседними вершинами с учётом общего направления
        for i in range(len(polygon.exterior.coords) - 1):
            if direction == 'forward' or direction == 'both':
                G.add_edge(i, i + 1,
                           weight=LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]]).length)
            if direction == 'backward' or direction == 'both':
                G.add_edge(i + 1, i,
                           weight=LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]]).length)

        # Замыкаем полигон
        if direction == 'forward' or direction == 'both':
            G.add_edge(len(polygon.exterior.coords) - 1, 0,
                       weight=LineString([polygon.exterior.coords[-1], polygon.exterior.coords[0]]).length)
        if direction == 'backward' or direction == 'both':
            G.add_edge(0, len(polygon.exterior.coords) - 1,
                       weight=LineString([polygon.exterior.coords[-1], polygon.exterior.coords[0]]).length)

        return G

    def find_closest_vertex(self, polygon, point):
        """
        Находит ближайшую вершину полигона к точке
        """
        min_dist = float('inf')
        closest_vertex = None

        for i, coord in enumerate(polygon.exterior.coords):
            dist = Point(coord).distance(point)
            if dist < min_dist:
                min_dist = dist
                closest_vertex = i

        return closest_vertex

    def find_path_one_way(self, G, start_vertex, end_vertex):
        """
        Поиск пути в графе только в одну сторону, с использованием направленного графа.
        """
        try:
            path = nx.shortest_path(G, start_vertex, end_vertex)
        except nx.NetworkXNoPath:
            path = None  # Если пути нет
        return path

    def get_path_points(self, G, path):
        """
        Возвращает список координат точек для заданного пути
        """
        return [G.nodes[i]['coord'] for i in path]

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

    def MergeNearLines(self, lines):
        answer_lines = []
        availible_lines = lines.copy()

        while len(availible_lines) >= 1:
            line = availible_lines[0]

            # Если линия замкнута (первая точка равна последней) и она не внутри полигона
            if (line[0] == line[len(line) - 1]) and not self.border_polygon.contains(
                    Point(line[0])) and not self.border_polygon.contains(Point(line[len(line) - 1])):
                answer_lines.append(availible_lines[0])
                del availible_lines[0]
            else:
                optimal_line_const = 10000000
                optimal_line_to_merge_index = -1
                optimal_start_point_to_merge_index = -1
                optimal_end_point_to_merge_index = -1

                # Проверка минимального расстояния между первой и последней точками самой линии
                self_distance = (line[0][0] - line[len(line) - 1][0]) ** 2 + (line[0][1] - line[len(line) - 1][1]) ** 2

                if self_distance < optimal_line_const and self_distance < self.max_merge_line_value:
                    optimal_line_const = self_distance
                    optimal_line_to_merge_index = -2  # Особая отметка, что линия замыкает сама себя

                # Поиск оптимальной линии для слияния
                k = 0
                for test_line in availible_lines:
                    if test_line == line:  # Проверяем, если линия сама собой, пропускаем до конца цикла
                        k = k + 1
                        continue

                    if test_line[0] != test_line[len(test_line) - 1]:  # Проверка, что линия не замкнута

                        # Проверка возможных точек для слияния
                        test_distances = [
                            ((test_line[0][0] - line[0][0]) ** 2 + (test_line[0][1] - line[0][1]) ** 2, 0, 0),
                            ((test_line[len(test_line) - 1][0] - line[0][0]) ** 2 + (
                                        test_line[len(test_line) - 1][1] - line[0][1]) ** 2, 0, len(test_line) - 1),
                            ((test_line[len(test_line) - 1][0] - line[len(line) - 1][0]) ** 2 + (
                                        test_line[len(test_line) - 1][1] - line[len(line) - 1][1]) ** 2, len(line) - 1,
                             len(test_line) - 1),
                            ((test_line[0][0] - line[len(line) - 1][0]) ** 2 + (
                                        test_line[0][1] - line[len(line) - 1][1]) ** 2, len(line) - 1, 0)
                        ]

                        for test_distance, start_idx, end_idx in test_distances:
                            if test_distance < optimal_line_const and test_distance < self.max_merge_line_value:
                                optimal_line_const = test_distance
                                optimal_line_to_merge_index = k
                                optimal_start_point_to_merge_index = start_idx
                                optimal_end_point_to_merge_index = end_idx
                    k += 1

                # Если нашлась линия для объединения или линия замыкает сама себя
                if optimal_line_to_merge_index == -2:  # Линия замыкает сама себя
                    line.append(line[0])  # Добавляем первую точку в конец для замыкания
                    answer_lines.append(line)
                    del availible_lines[0]
                elif optimal_line_to_merge_index != -1:
                    # Соединение линий
                    line_to_merge = availible_lines[optimal_line_to_merge_index]

                    if optimal_start_point_to_merge_index == 0 and optimal_end_point_to_merge_index == 0:
                        line = line_to_merge[::-1] + line
                    elif optimal_start_point_to_merge_index == 0 and optimal_end_point_to_merge_index == len(line) - 1:
                        line = line + line_to_merge
                    elif optimal_start_point_to_merge_index == len(
                            line) - 1 and optimal_end_point_to_merge_index == len(line_to_merge) - 1:
                        line = line + line_to_merge[::-1]
                    elif optimal_start_point_to_merge_index == len(line) - 1 and optimal_end_point_to_merge_index == 0:
                        line = line + line_to_merge
                    availible_lines[0] = line

                    del availible_lines[optimal_line_to_merge_index]
                else:
                    answer_lines.append(availible_lines[0])
                    del availible_lines[0]

        if availible_lines:
            answer_lines.append(availible_lines[0])

        return answer_lines

    def FixLine(self, line):
            if (line[0] != line[len(line) - 1]):
                if not self.border_polygon.contains(Point(line[0])) or not self.border_polygon.contains(Point(line[len(line)-1])):
                    G = self.create_graph_from_polygon(self.max_border_polygon, self.hight_find_direction)

                    projection_point, closest_segment =self.direction_point_from_border_polygon(self.max_border_polygon, line[0])
                    x_coordinate_start = projection_point.x
                    y_coordinate_start = projection_point.y
                    line.insert(0, (x_coordinate_start, y_coordinate_start))

                    start_vertex = self.find_closest_vertex(self.max_border_polygon, Point((x_coordinate_start, y_coordinate_start)))

                    projection_point, closest_segment = self.direction_point_from_border_polygon(self.max_border_polygon, line[len(line) - 1])
                    x_coordinate_end = projection_point.x
                    y_coordinate_end = projection_point.y
                    line.append((x_coordinate_end, y_coordinate_end))

                    end_vertex = self.find_closest_vertex(self.max_border_polygon, Point((x_coordinate_end, y_coordinate_end )))

                    one_way_path = self.find_path_one_way(G, start_vertex, end_vertex)
                    if one_way_path:
                        path_points = self.get_path_points(G, one_way_path)
                        if(len(path_points))>2:
                            for path_point in path_points:
                                line.insert(0, (path_point[0], path_point[1]))
                            line.append(path_points[len(path_points) - 1])
                        else:
                            line.insert(0, line[0])
                    return True
                else:
                    print("Fatal Error - Border non closest line" + str(line))
            return False


    def GeneratedLineByCoords(self, lines_coords):
        lines = []
        if (self.apply_merge_line_value):
            lines_coords = self.MergeNearLines(lines_coords)
        for line in lines_coords:
            if(self.apply_unborder_draw):
                self.FixLine(line)
            new_line = line_library.ULine(None, [], None, line)
            new_line.MergeСlosePoints(self.merge_point_value)
            if(new_line.CheckLineNumberPoint()):
                new_line.CreatePoligon()
                lines.append(new_line)
        uncheck_lines = lines.copy()
        while len(uncheck_lines)>0:
            check_line = uncheck_lines[0]
            uncheck_lines.remove(check_line)
            min_parent_area = 1000000000
            min_parent = None
            for uncheck_line in uncheck_lines:
                if(check_line.shapely_polygon.contains(uncheck_line.shapely_polygon)):
                    if(uncheck_line.parent and check_line.parent):
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
                if(check_line.parent and check_line in check_line.parent.childs ):
                    check_line.parent.childs.remove(check_line)
                check_line.parent = min_parent
                check_line.parent.childs.append(check_line)
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
        self.cook_image = image
        return image

    def LaunchAsync(self):
        if(os.path.exists(self.bna_file_path)):
            data = helper_functions.ReadFile(self.bna_file_path)
            if(data):
                thread = threading.Thread(target=self.MainLaunchOperations)
                thread.start()
                thread.join()

    def MainLaunchOperations(self):
        if(os.path.exists(self.bna_file_path)):
            data = helper_functions.ReadFile(self.bna_file_path)
            if (self.draw_debug_lines):
                data_all = self.ParseAllFromData(data)
                data_lines = self.ParseLinesFromData(data)
                self.lines = self.GenerateLinesByLineData(data_lines)
                print(self.width, self.height)
                self.DebugDrawLines(self.lines)
                self.end_cook_delegate.invoke()
            else:
                data_all = self.ParseAllFromData(data)
                data_lines = self.ParseLinesFromData(data)
                self.lines = self.GenerateLinesByLineData(data_lines)
                print(self.width, self.height)
                self.DrawPlotHeightMap(self.lines)
                self.end_cook_delegate.invoke()

