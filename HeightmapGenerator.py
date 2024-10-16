import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, LineString
from PIL import Image, ImageDraw
import helper_functions as helper_functions
import line as line_library
from shapely.ops import nearest_points
import networkx as nx
import os
import Delegates
import math
from scipy.spatial import ConvexHull
from playsound import playsound
import xml.etree.ElementTree as ET

def set_options_to_availible_parce_line_settings(new_options):
    for default_option in UAvailibleParceLineSettings.default_options:
        if (not default_option in new_options):
            new_options.append(default_option)
    UAvailibleParceLineSettings.options = new_options
    UAvailibleParceLineSettings.update_name_options_delegate.invoke()

class UAvailibleParceLineSettings:
    options = ["Contour", "Index contour", "ErrorType"]
    default_options = ["Contour", "Index contour", "ErrorType"]
    update_name_options_delegate = Delegates.UDelegate()

    def __eq__(self, other):
        if(other):
            return self.name == other.name
        else:
            return False

    def update_options_by_global_options(self):
        self.name_options = UAvailibleParceLineSettings.options
        self.update_name_options_delegate.invoke()

    def __init__(self, name = "string", index = 1):
        self.name = name
        self.name_options = UAvailibleParceLineSettings.options
        self.index = index

        self.ui_show_tag = ["name", "index"]
        self.save_tag = ["name", "index"]

    def __str__(self):
        string = ""
        for attr_name in self.ui_show_tag:
            string = string + ", " + attr_name + " = " + str(getattr(self, attr_name))
        return f"{self.name}: {string}"

    def to_dict(self):
        """Сериализуем только параметры, указанные в save_tag."""
        return {k: getattr(self, k) for k in self.save_tag}

    def from_dict(self, data):
        """Десериализация параметров из словаря в объект."""
        for k, v in data.items():
            if k in self.save_tag:
                setattr(self, k, v)


class UFixingLinesSettings:
    counter = -1

    def __init__(self):
        UFixingLinesSettings.counter = UFixingLinesSettings.counter + 1
        self.name = f"{UFixingLinesSettings.counter}"

        self.merge_point_value = 0;
        self.max_merge_line_value = 200;

        self.border_distance = 0;
        self.hight_find_direction = "both"
        self.hight_find_direction_options = ['both', 'forward', 'backward']

        self.apply_fix_unborder_lines = True
        self.apply_merge_line_value = True
        self.regenerate_borders = True

        self.save_tag = ["merge_point_value", "max_merge_line_value","border_distance","hight_find_direction",
                            "apply_fix_unborder_lines", "apply_merge_line_value", "regenerate_borders"]
        self.ui_show_tag = ["merge_point_value", "max_merge_line_value","border_distance","hight_find_direction",
                            "apply_fix_unborder_lines", "apply_merge_line_value", "regenerate_borders"]


    def __str__(self):
        string = ""
        for attr_name in self.ui_show_tag:
            string = string + ", " + attr_name + " = " + str(getattr(self, attr_name))
        return f"{self.name}: {string}"

    def to_dict(self):
        """Сериализуем только параметры, указанные в save_tag."""
        return {k: getattr(self, k) for k in self.save_tag}

    def from_dict(self, data):
        """Десериализация параметров из словаря в объект."""
        for k, v in data.items():
            if k in self.save_tag:
                setattr(self, k, v)

class UHeightMapGenerator:
    def __init__(self):
        # 1. Параметры ввода/вывода
        self.__file_path = "None"  # Путь к файлу BNA

        # 2. Параметры размера и границ
        self.global_scale_multiplier = 0.2  # Глобальный масштаб
        self.width = 0  # Ширина карты
        self.height = 0  # Высота карты
        self.max_width = -1000000  # Максимальная ширина
        self.max_height = -1000000  # Максимальная высота
        self.min_width = 1000000  # Минимальная ширина
        self.min_height = 1000000  # Минимальная высота

        self.max_distance_to_border_polygon = 100  # Максимальное расстояние до границы полигона

        # 3. Параметры визуализации и отладки
        self.draw_with_max_border_polygon = True  # Рисовать с максимальной границей полигона
        self.draw_debug_lines = True  # Режим отладки: отображение отладочных линий
        self.cook_image = None  # Изображение для отладки или вывода

        # 4. Параметры обработки линий
        self.availible_parce_contour_line_settings = [UAvailibleParceLineSettings("Contour",1),UAvailibleParceLineSettings("Index contour",1)]  # Доступные данные для парсинга
        self.availible_parce_slope_line_setting = "Slope line, contour"

        self.first_level_distance = 50  # Расстояние первого уровня (между линиями контура)
        self.remove_all_error_lines = False  # Удаление всех ошибочных линий
        self.min_owner_overlap = 0.95

        self.fixing_lines_settings = [UFixingLinesSettings()]  # Настройки для исправления линий
        self.lines = []  # Линии, которые будут обрабатываться

        # 5. Прочие настройки и делегаты
        self.border_polygon = None  # Полигон границы
        self.max_border_polygon = None  # Максимальный полигон границы
        self.end_cook_delegate = Delegates.UDelegate()  # Делегат для завершея
        self.progress_delegate = Delegates.UDelegate()

        self.save_tag = ['file_path', 'global_scale_multiplier', 'first_level_distance',
                         'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                         'remove_all_error_lines','min_owner_overlap', 'availible_parce_slope_line_setting']
        self.ui_show_tag = ['global_scale_multiplier', 'first_level_distance',
                            'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                            'remove_all_error_lines','min_owner_overlap', 'availible_parce_slope_line_setting']



    def to_dict(self):
        """Сериализуем только параметры, указанные в save_tag, включая список fixing_lines_settings и availible_parce_settings."""
        data = {k: getattr(self, k) for k in self.save_tag}
        # Сериализация списка fixing_lines_settings
        data['fixing_lines_settings'] = [settings.to_dict() for settings in self.fixing_lines_settings]
        data['availible_parce_settings'] = [settings.to_dict() for settings in self.availible_parce_settings]
        return data

    def from_dict(self, data):
        """Десериализация параметров из словаря в объект."""
        for k, v in data.items():
            if k in self.save_tag:
                setattr(self, k, v)
            elif k == "fixing_lines_settings":
                # Десериализация списка fixing_lines_settings
                self.fixing_lines_settings.clear()
                for item in v:
                    new_fixing_lines_setting = UFixingLinesSettings()
                    new_fixing_lines_setting.from_dict(item)
                    self.fixing_lines_settings.append(new_fixing_lines_setting)
            elif k == 'availible_parce_settings':
                # Десериализация списка availible_parce_settings
                self.availible_parce_contour_line_settings.clear()
                for item in v:
                    new_availible_parce_line_setting = UAvailibleParceLineSettings()
                    new_availible_parce_line_setting.from_dict(item)
                    self.availible_parce_contour_line_settings.append(new_availible_parce_line_setting)
                    print(new_availible_parce_line_setting)

    @property
    def file_path(self):
        # Геттер для переменной value
        return self.__file_path

    @file_path.setter
    def file_path(self, file_path):
        # Сеттер, который будет вызван при присвоении значения
        self.__file_path = file_path
        self.UpdateAvailibleParceLineOptions(helper_functions.ReadFile(self.__file_path))

    def find_availible_parce_setting_by_name(self, name):
        for availible_parce_setting in self.availible_parce_settings:
            if(availible_parce_setting.name == name):
                return availible_parce_setting
        return None

    def UpdateAvailibleParceLineOptions(self, data):
        options = []
        for line in data.splitlines():
            stripped_line = line.strip()
            points = stripped_line.split(',')
            if not helper_functions.can_convert_to_float(points[0]):
                points[0] = points[0].strip('"').strip()
                if(not points[0] in options):
                    options.append(points[0])
        set_options_to_availible_parce_line_settings(options)
        for option in self.availible_parce_contour_line_settings:
            if(option):
                option.update_options_by_global_options()


    # Основная функция для парсинга XML-файла
    def parse_omap_hml(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        namespace = helper_functions.get_namespace(root)

        lines = []
        slope_lines = []

        symbols_lines = {}
        for available_parce_contour_line in self.availible_parce_contour_line_settings:
            symbols_lines.update(helper_functions.extract_symbols(root, available_parce_contour_line.name, namespace))

        for obj in root.findall(f'.//{namespace}object'):
            symbol_id = obj.get('symbol')
            if symbol_id in symbols_lines:
                coords = obj.find(f'{namespace}coords').text.strip()
                coords = coords.split(";")  # Сначала разделяем по ";"
                coords = [coord.split(" ") for coord in coords]
                coords = helper_functions.fix_coordinates(coords)
                coords_list = [[float(coord[0])/ 100 * self.global_scale_multiplier, float(coord[1])/ 100 * self.global_scale_multiplier] for coord in coords]
                lines.append([coords_list])

        symbols_slope_lines = {}
        symbols_slope_lines.update(helper_functions.extract_symbols(root, self.availible_parce_slope_line_setting, namespace))

        for obj in root.findall(f'.//{namespace}object'):
            symbol_id = obj.get('symbol')
            if symbol_id in symbols_slope_lines:
                rotation = obj.get('rotation')
                coords = obj.find(f'{namespace}coords').text.strip()
                coords = coords.split(";")  # Сначала разделяем по ";"
                coords = helper_functions.fix_coordinates(coords)
                coords_list = [[float(coord[0])/ 100 * self.global_scale_multiplier, float(coord[1])/ 100 * self.global_scale_multiplier] for coord in coords]
                slope_lines.append([coords_list, rotation])

        return lines, slope_lines

    def ImportNewFile(self):
        file_extension = self.file_path.split('.')[-1]
        if file_extension == "omap":
            data_lines, data_slope_lines = self.parse_omap_hml()
            return data_lines, data_slope_lines
        elif file_extension == "bna":
            data = helper_functions.ReadFile(self.bna_file_path)
            data_lines = self.ParseAllFromData(data)
            return data_lines, None
        elif file_extension == "ocd":
            return None, None
        else:
            print("Неизвестный тип файла")
            return None, None

    def ParseLinesFromData(self, data):
        lines = []
        current_line = []
        correct_data = True;
        for line in data.splitlines():
            stripped_line = line.strip()
            points = stripped_line.split(',')
            if not helper_functions.can_convert_to_float(points[0]):
                points[0] = points[0].strip('"').strip()
                if self.find_availible_parce_setting_by_name(points[0]) !=None:
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

        lines = self.ParseLinesFromData(lines)

        return lines

    def SetupBorderPoligonsDataFromLines(self, border_distance):
        """
            Generated Border By Lines inside.
        """
        points = []
        for line in self.lines:
            for segment in line.start_points:
                points.append(segment)

        points = np.array(points)

        unique_points = np.unique(points, axis=0)

        if len(unique_points) < 3:
            # Если точек меньше 3 или они лежат на одной прямой, используем LineString и создаем буфер
            line = LineString(unique_points)
            self.border_polygon = line.buffer(-1*border_distance, join_style=2,
                                              cap_style=2)  # cap_style=2 для плоских концов
            self.max_border_polygon = line.buffer(self.max_distance_to_border_polygon, join_style=2, cap_style=2)

        else:
            # Находим минимальные и максимальные координаты по x и y
            self.min_width = np.min(points[:, 0])
            self.max_width = np.max(points[:, 0])
            self.min_height = np.min(points[:, 1])
            self.max_height = np.max(points[:, 1])

            # Создаем выпуклую оболочку на основе всех точек отрезков
            hull = ConvexHull(points)
            hull_points = points[hull.vertices]  # Вершины выпуклой оболочки
            original_polygon = Polygon(hull_points)  # Исходный полигон

            # 1. Создание уменьшенного полигона (border_polygon)
            self.border_polygon = original_polygon.buffer(-1*border_distance, join_style=2)

            # 2. Создание расширенного полигона (max_border_polygon)
            self.max_border_polygon = original_polygon.buffer(self.max_distance_to_border_polygon, join_style=2)

    def find_bounding_square(self, polygon):
        """
        Находит размеры квадрата, в который можно вписать заданный полигон.

        :param polygon: Объект типа Polygon из библиотеки Shapely
        :return: Координаты квадратного ограничивающего прямоугольника (min_x, min_y, max_x, max_y)
        """
        if polygon.is_empty:
            print("Полигон пуст.")
            return None

        min_x, min_y, max_x, max_y = polygon.bounds

        width = max_x - min_x
        height = max_y - min_y

        square_side = max(width, height)

        if height < square_side:
            diff = square_side - height
            min_y -= diff / 2
            max_y += diff / 2
        elif width < square_side:
            diff = square_side - width
            min_x -= diff / 2
            max_x += diff / 2

        return min_x, min_y, max_x, max_y

    def SetupSizeDataFromLines(self, lines_coords):
        coords = [coord for line in lines_coords for coord in line]

        self.min_width = min(coord[0] for coord in coords)
        self.max_width = max(coord[0] for coord in coords)
        self.min_height = min(coord[1] for coord in coords)
        self.max_height = max(coord[1] for coord in coords)

        self.width = self.max_width - self.min_width
        self.height = self.max_height - self.min_height

    def DebugDrawLines(self,lines):
        if(not self.draw_with_max_border_polygon):
            min_x = self.min_width
            max_x = self.max_width
            min_y = self.min_height
            max_y = self.max_height

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
            min_x, min_y, max_x, max_y  = self.find_bounding_square(self.max_border_polygon)
            width = int(max_x - min_x + 1)
            height = int(max_y - min_y + 1)
            image = Image.new("RGB", (width+1, height+1), "black")
            draw = ImageDraw.Draw(image)

            offset_x = -min_x
            offset_y = -min_y

            x, y = self.border_polygon.exterior.xy
            border_coords = []

            for length in range(len(x)):
                border_coords.append((int(x[length] + offset_x), int(y[length] + offset_y)))
            draw.line(border_coords, fill="red", width=2)

            x, y = self.max_border_polygon.exterior.xy
            max_border_coords = []
            for length in range(len(x)):
                max_border_coords.append((int(x[length] + offset_x), int(y[length] + offset_y)))
            draw.line(max_border_coords, fill="green", width=2)

            for line in self.lines:
                if(line.correct_line):
                    if len(line.points) >= 2:
                        flat_coords = [(int(point[0] + offset_x), int(point[1] + offset_y)) for point in line.points]
                        draw.line(flat_coords, fill=(line.color[0], line.color[1], line.color[2]),
                                  width=2)
                else:
                    if len(line.points) >= 2:
                        flat_coords = [(int(point[0] + offset_x), int(point[1] + offset_y)) for point in line.points]
                        for i in range(len(flat_coords)-1):
                            self.draw_two_color_line(draw, flat_coords[i], flat_coords[i+1], 'red', 'white', width=2, step=10)

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

    def draw_two_color_line(self, draw, start, end, color1, color2, width=5, step=10):
        """
        Рисует чередующуюся по цветам линию.
        :param draw: Объект ImageDraw для рисования.
        :param start: Начальная точка линии (x, y).
        :param end: Конечная точка линии (x, y).
        :param color1: Первый цвет (например, 'red').
        :param color2: Второй цвет (например, 'white').
        :param width: Толщина линии.
        :param step: Длина каждого сегмента в пикселях.
        """
        x0, y0 = start
        x1, y1 = end
        dx = x1 - x0
        dy = y1 - y0
        length = ((dx ** 2) + (dy ** 2)) ** 0.5  # Длина линии
        steps = max(1, int(length / step))  # Количество шагов (сегментов), минимум 1 шаг

        # Рисуем сегменты, чередуя цвета
        for i in range(steps):
            # Вычисляем начальные и конечные координаты для каждого сегмента
            xi = x0 + (dx / steps) * i
            yi = y0 + (dy / steps) * i
            xi_next = x0 + (dx / steps) * (i + 1)
            yi_next = y0 + (dy / steps) * (i + 1)

            # Чередуем цвета
            color = color1 if i % 2 == 0 else color2
            draw.line([(xi, yi), (xi_next, yi_next)], fill=color, width=width)

        # Последний сегмент для корректного завершения линии
        if length > 0:  # Убедимся, что линия не нулевая по длине
            draw.line([(xi_next, yi_next), (x1, y1)], fill=color, width=width)

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

    def GenerateLinesByLineData(self,lines_data, slope_lines_data):
        lines_coords = []
        for line_data in lines_data:
            updated_coords = []
            for coord in line_data[0]:
                x = coord[0]
                y = coord[1]
                updated_coords.append([x,y])
            lines_coords.append(updated_coords)

        slope_lines_coords = []
        for slope_line_data in slope_lines_data:
            updated_coords = []
            for coord in slope_line_data[0]:
                x = coord[0]
                y = coord[1]
                updated_coords.append([x,y])
            slope_lines_coords.append(updated_coords)

        self.SetupSizeDataFromLines(lines_coords)
        return self.GeneratedLineByCoords(lines_coords, slope_lines_coords)

    def FixMergeNearLines(self, setting:UFixingLinesSettings):
        if(setting.apply_merge_line_value):
            answer_lines = []
            availible_lines = self.lines.copy()

            while len(availible_lines) >= 1:
                line = availible_lines[0]

                # Если линия замкнута (первая точка равна последней) и она не внутри полигона
                if (line.points[0] == line.points[-1]) and (not self.border_polygon.contains(
                        Point(line.points[0])) or not self.border_polygon.contains(Point(line.points[-1]))):
                    answer_lines.append(availible_lines[0])
                    del availible_lines[0]
                else:
                    optimal_line_const = 10000000
                    optimal_line_to_merge_index = -1
                    optimal_start_point_to_merge_index = -1
                    optimal_end_point_to_merge_index = -1

                    # Проверка минимального расстояния между первой и последней точками самой линии
                    self_distance = (line.points[0][0] - line.points[-1][0]) ** 2 + (line.points[0][1] - line.points[-1][1]) ** 2

                    if self_distance < optimal_line_const and self_distance < setting.max_merge_line_value:
                        optimal_line_const = self_distance
                        optimal_line_to_merge_index = -2  # Особая отметка, что линия замыкает сама себя

                    # Поиск оптимальной линии для слияния
                    k = 0
                    for test_line in availible_lines:
                        if test_line == line:  # Проверяем, если линия сама собой, пропускаем до конца цикла
                            k = k + 1
                            continue

                        if test_line.points[0] != test_line.points[-1]:
                            # Проверка первой пары точек: первая точка обеих линий
                            try:
                                if(self.border_polygon.contains(Point(line.points[0])) and self.border_polygon.contains(Point(test_line.points[0]))):
                                    test_distance_1 = (test_line.points[0][0] - line.points[0][0]) ** 2 + (test_line.points[0][1] - line.points[0][1]) ** 2
                                    if test_distance_1 < optimal_line_const and test_distance_1 <setting.max_merge_line_value:
                                        optimal_line_const = test_distance_1
                                        optimal_line_to_merge_index = k
                                        optimal_start_point_to_merge_index = 0
                                        optimal_end_point_to_merge_index = 0
                            except:
                                print("Wrong Geometry")

                            # Проверка второй пары точек: первая точка первой линии и последняя точка второй линии
                            try:
                                if (self.border_polygon.contains(Point(line.points[0])) and self.border_polygon.contains(
                                        Point(test_line.points[-1]))):
                                    test_distance_2 = (test_line.points[-1][0] - line.points[0][0]) ** 2 + (test_line.points[-1][1] - line.points[0][1]) ** 2
                                    if test_distance_2 < optimal_line_const and test_distance_2 < setting.max_merge_line_value:
                                        optimal_line_const = test_distance_2
                                        optimal_line_to_merge_index = k
                                        optimal_start_point_to_merge_index = 0
                                        optimal_end_point_to_merge_index = len(test_line.points) - 1
                            except:
                                print("Wrong Geometry")

                            # Проверка третьей пары точек: последние точки обеих линий
                            try:
                                if (self.border_polygon.contains(Point(line.points[-1])) and self.border_polygon.contains(
                                        Point(test_line.points[-1]))):
                                    test_distance_3 = (test_line.points[-1][0] - line.points[-1][0]) ** 2 + (test_line.points[-1][1] - line.points[-1][1]) ** 2
                                    if test_distance_3 < optimal_line_const and test_distance_3 < setting.max_merge_line_value:
                                        optimal_line_const = test_distance_3
                                        optimal_line_to_merge_index = k
                                        optimal_start_point_to_merge_index = len(line.points) - 1
                                        optimal_end_point_to_merge_index = len(test_line.points) - 1
                            except:
                                print("Wrong Geometry")
                            try:
                                if (self.border_polygon.contains(Point(line.points[-1])) and self.border_polygon.contains(
                                        Point(test_line.points[0]))):
                                        # Проверка четвертой пары точек: последняя точка первой линии и первая точка второй линии
                                    test_distance_4 = (test_line.points[0][0] - line.points[-1][0]) ** 2 + (test_line.points[0][1] - line.points[-1][1]) ** 2
                                    if test_distance_4 < optimal_line_const and test_distance_4 < setting.max_merge_line_value:
                                        optimal_line_const = test_distance_4
                                        optimal_line_to_merge_index = k
                                        optimal_start_point_to_merge_index = len(line.points) - 1
                                        optimal_end_point_to_merge_index = 0
                            except:
                                print("Wrong Geometry")
                        k += 1

                    # Если нашлась линия для объединения или линия замыкает сама себя
                    if optimal_line_to_merge_index == -2:  # Линия замыкает сама себя
                        line.points.append(line.points[0])  # Добавляем первую точку в конец для замыкания
                        line.start_points.append(line.points[0])
                        answer_lines.append(line)
                        del availible_lines[0]
                    elif optimal_line_to_merge_index != -1:
                        # Соединение линий
                        line_to_merge = availible_lines[optimal_line_to_merge_index]

                        if optimal_start_point_to_merge_index == 0 and optimal_end_point_to_merge_index == 0:
                            line.points =  line_to_merge.points[::-1] + line.points
                            line.start_points = line_to_merge.start_points[::-1] + line.start_points
                        elif optimal_start_point_to_merge_index == 0 and optimal_end_point_to_merge_index == (len(line_to_merge.points) - 1):
                            line.points = line_to_merge.points + line.points
                            line.start_points = line.start_points + line_to_merge.start_points[::-1]
                        elif optimal_start_point_to_merge_index == (len(
                                line.points) - 1) and optimal_end_point_to_merge_index == (len(line_to_merge.points) - 1):
                            line.points = line.points + line_to_merge.points[::-1]
                            line.start_points = line.start_points + line_to_merge.start_points[::-1]
                        elif optimal_start_point_to_merge_index == (len(line.points) - 1) and optimal_end_point_to_merge_index == 0:
                            line.points = line.points + line_to_merge.points
                            line.start_points = line.start_points + line_to_merge.start_points

                        del availible_lines[optimal_line_to_merge_index]
                    else:
                        answer_lines.append(availible_lines[0])
                        del availible_lines[0]

            if availible_lines:
                answer_lines.append(availible_lines[0])
            self.lines = answer_lines

            return answer_lines
        else:
            return []

    def FixUnboarderLines(self, setting:UFixingLinesSettings):
        if(setting.apply_fix_unborder_lines):
            for line in self.lines:
                if (line.points[0] != line.points[-1]):
                    if not self.border_polygon.contains(Point(line.points[0])) or not self.border_polygon.contains(Point(line.points[-1])):
                        G = self.create_graph_from_polygon(self.max_border_polygon, setting.hight_find_direction)

                        projection_point, closest_segment =self.direction_point_from_border_polygon(self.max_border_polygon, line.points[0])
                        x_coordinate_start = projection_point.x
                        y_coordinate_start = projection_point.y
                        line.points.insert(0, (x_coordinate_start, y_coordinate_start))

                        start_vertex = self.find_closest_vertex(self.max_border_polygon, Point((x_coordinate_start, y_coordinate_start)))

                        projection_point, closest_segment = self.direction_point_from_border_polygon(self.max_border_polygon, line.points[-1])
                        x_coordinate_end = projection_point.x
                        y_coordinate_end = projection_point.y
                        line.points.append((x_coordinate_end, y_coordinate_end))

                        end_vertex = self.find_closest_vertex(self.max_border_polygon, Point((x_coordinate_end, y_coordinate_end )))

                        one_way_path = self.find_path_one_way(G, start_vertex, end_vertex)
                        if one_way_path:
                            path_points = self.get_path_points(G, one_way_path)
                            if(len(path_points))>2:
                                for path_point in path_points:
                                    line.points.insert(0, (path_point[0], path_point[1]))
                                line.points.append(path_points[len(path_points) - 1])
                            else:
                                line.points.insert(0, line.points[-1])
                    else:
                        print("Warning- Border non closest line" + str(line))

    def CheckErrorLines(self):
        for line in self.lines:
            if(line.points[0] == line.points[-1]) and line.CheckLineNumberPoint():
                line.correct_line =True
            else:
                line.correct_line = False

    def GeneratedNestingOfLines(self):
        """ Сама идея очень проста - мы перебираем все элементы последовательно, удаляя пройденный элемент.
         Поскольку проейденые элементы больше не прокручиваются, кода настолько много - выбирается как себе parent, так и предположительные Child.
         Проверки работают на случай косяка предыдуших этапов.
        """
        uncheck_lines = self.lines.copy()
        while len(uncheck_lines) > 0:
            check_line = uncheck_lines[0]
            uncheck_lines.remove(check_line)
            min_parent_area = 1000000000
            min_parent = None
            for uncheck_line in uncheck_lines:
                    if (check_line.evaluate_polygon_overlap(uncheck_line)>self.min_owner_overlap):
                        if check_line.shapely_polygon.area > uncheck_line.shapely_polygon.area:
                            last_parent = uncheck_line.parent
                            uncheck_line.parent = check_line
                            if (uncheck_line.CheckLineParentLoop([])):
                                uncheck_line.parent = last_parent
                            else:
                                if (last_parent and check_line in last_parent.childs):
                                    last_parent.childs.remove(check_line)
                                check_line.childs.append(uncheck_line)
                        else:
                            uncheck_line.parent = check_line
                            check_line.childs.append(uncheck_line)
                    else:
                        if (uncheck_line.shapely_polygon and uncheck_line.evaluate_polygon_overlap(check_line)>self.min_owner_overlap and min_parent_area > uncheck_line.shapely_polygon.area):
                            min_parent = uncheck_line
                            min_parent_area = uncheck_line.shapely_polygon.area
            if (min_parent):
                last_parent = check_line.parent
                check_line.parent = min_parent
                if (check_line.CheckLineParentLoop([])):
                    check_line.parent = last_parent
                else:
                    if (last_parent and check_line in last_parent.childs):
                        last_parent.childs.remove(check_line)
                    check_line.parent.childs.append(check_line)


    def GetAllErrorLines(self):
        error_lines = []
        for line in self.lines:
            if(line.correct_line == False):
                error_lines.append(line)
        return error_lines

    def RemoveAllErrorLines(self):
        error_lines = self.GetAllErrorLines()
        for error_line in error_lines:
            self.lines.remove(error_line)

    def GeneratedSlopeDirectionEvent(self, slope_lines_coords):
        pass

    def GeneratedLineByCoords(self, lines_coords, slope_lines_coords):
        self.lines = []

        for line in lines_coords:
            new_line = line_library.ULine(None, [], None, line)
            new_line.correct_line = True
            self.lines.append(new_line)

        self.SetupBorderPoligonsDataFromLines(-2)

        self.progress_delegate.invoke("fixing_lines_settings", -1)
        for setting in self.fixing_lines_settings:
            self.FixMergeNearLines(setting)
            if(setting.regenerate_borders):
                self.SetupBorderPoligonsDataFromLines(setting.border_distance)
            self.FixUnboarderLines(setting)

        self.progress_delegate.invoke("generated_neasting_of_lines", -1)
        for line in self.lines:
            line.CreatePoligon()
        self.GeneratedNestingOfLines()

        self.CheckErrorLines()

        if(self.remove_all_error_lines):
            self.RemoveAllErrorLines()


    def DrawPlotHeightMap(self):
        max_depth = line_library.GetMaxDepthFromLines(self.lines)
        print("Depth equal " + str(max_depth))
        image = Image.new("RGB", (int(self.width + self.first_level_distance), int(self.height + self.first_level_distance)), "black")
        draw = ImageDraw.Draw(image)
        root_lines = line_library.GetRootLines(self.lines)

        k = 0
        for y in range(int(self.height + self.first_level_distance)):
            for x in range(int(self.width + self.first_level_distance)):
                helper_functions.print_progress_bar(k,int(self.height)*int(self.width))
                point = Point(int(x+self.min_width - self.first_level_distance/2), int(y+self.min_height - self.first_level_distance/2))
                intensity = 0
                owner_line = None
                min_poligin_length = 100000000000000
                for line in self.lines:
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

    def MainLaunchOperations(self):
        if(os.path.exists(self.file_path)):
            contour_lines, slope_lines = self.ImportNewFile()
            self.GenerateLinesByLineData(contour_lines, slope_lines)
            if (self.draw_debug_lines):
                self.DebugDrawLines(self.lines)
                self.end_cook_delegate.invoke()
            else:
                self.DrawPlotHeightMap()
                self.end_cook_delegate.invoke()

