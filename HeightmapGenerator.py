import line
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
from Octree import Octree, OctreeNode
from enum import Enum
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from shapely.ops import nearest_points
from typing import Optional, Sequence, Dict, List

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


type_option = ["Contour", "Slope line", "Water"]

class UAvailibleParceLineSettings:
    def __init__(self, name = "string", type = "Contour", index = 1):
        self.name = name
        self.type = type
        self.type_option = type_option
        self.index = index

        self.ui_show_tag = ["name", "index", "type"]
        self.save_tag = ["name", "index", "type"]

    def __eq__(self, other):
        if(other):
            return self.name == other.name
        else:
            return False

    def __str__(self):
        string = ""
        for attr_name in self.ui_show_tag:
            string = string + attr_name + " = " + str(getattr(self, attr_name)) + ", "
        return f"{string}"

    def to_dict(self):
        """Сериализуем только параметры, указанные в save_tag."""
        return {k: getattr(self, k) for k in self.save_tag}

    def from_dict(self, data):
        """Десериализация параметров из словаря в объект."""
        for k, v in data.items():
            if k in self.save_tag:
                setattr(self, k, v)

def interpolate_two_points(p0, p1, value0, value1, query_pt: Point):
    """
    Линейно интерполирует значение в точке query_pt,
    находящейся на плоскости, по двум контрольным точкам.

    p0, p1 – кортежи (x, y) контрольных точек
    value0, value1 – значения в этих точках
    query_pt – shapely.geometry.Point, позиция запроса
    """
    # преобразуем в numpy‑векторы
    a = np.asarray(p0, dtype=float)
    b = np.asarray(p1, dtype=float)
    q = np.asarray([query_pt.x, query_pt.y], dtype=float)

    # если точки совпали – вернём среднее значение
    if np.allclose(a, b):
        return 0.5 * (value0 + value1)

    # проецируем q на отрезок ab и находим параметр t∈[0,1]
    ab = b - a
    t = np.clip(np.dot(q - a, ab) / np.dot(ab, ab), 0.0, 1.0)

    # интерполируем значение
    return value0 + t * (value1 - value0)

def is_point_outside(polygon, point: Point) -> bool:
    ray = cast_ray_from(point, Point(point.x + 1, point.y))  # Луч вправо
    intersections = polygon.exterior.intersection(ray)
    if intersections.is_empty:
        return False
    if intersections.geom_type == "MultiPoint":
        return len(intersections.geoms) % 2 == 1
    return 1 % 2 == 1  # Single intersection

class UFixingLinesSettings:
    counter = -1

    def __init__(self):
        UFixingLinesSettings.counter = UFixingLinesSettings.counter + 1
        self.name = f"{UFixingLinesSettings.counter}"

        self.merge_point_value = 0;
        self.max_merge_line_value = 200;
        self.max_angle = 90
        self.enable_merge_with_self = True

        self.border_distance = 0;
        self.hight_find_direction = "both"
        self.hight_find_direction_options = ['both', 'forward', 'backward']
        self.fix_unborder_if_both_point_unborder = True

        self.apply_fix_unborder_lines = True
        self.apply_merge_line_value = True
        self.regenerate_borders = True

        self.save_tag = ["merge_point_value", "max_merge_line_value","border_distance","hight_find_direction",
                            "apply_fix_unborder_lines", "apply_merge_line_value", "regenerate_borders", "max_angle",
                         "fix_unborder_if_both_point_unborder", "enable_merge_with_self"]
        self.ui_show_tag = ["merge_point_value", "max_merge_line_value","border_distance","hight_find_direction",
                            "apply_fix_unborder_lines", "apply_merge_line_value", "regenerate_borders", "max_angle",
                            "fix_unborder_if_both_point_unborder", "enable_merge_with_self"]


    def __str__(self):
        string = ""
        for attr_name in self.ui_show_tag:
            string = string + attr_name + " = " + str(getattr(self, attr_name)) + ","
        return string

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
        self.count_error_lines = 0
        self.seed = 1

        self.max_distance_to_border_polygon = 100  # Максимальное расстояние до границы полигона

        # 3. Параметры визуализации и отладки
        self.draw_with_max_border_polygon = True  # Рисовать с максимальной границей полигона
        self.draw_with_slope_line_color = True # Рисовать с цветом возрастания или убывания.
        self.draw_debug_lines = True  # Режим отладки: отображение отладочных линий
        self.cook_image = None  # Изображение для отладки или вывода

        # 4. Параметры обработки линий
        self.availible_parce_contour_line_settings = [UAvailibleParceLineSettings("Contour","Contour", 1),
                                                      UAvailibleParceLineSettings("Index contour","Contour", 1),
                                                      UAvailibleParceLineSettings("Slope line, contour",  "Slope line", 1),
                                                      UAvailibleParceLineSettings("Index contour", "Slope line", 1),
                                                      UAvailibleParceLineSettings("Slope line, index contour", "Slope line", 1),
                                                      UAvailibleParceLineSettings("Uncrossable body of water (full colour), with bank line", "Water", 1),
                                                      UAvailibleParceLineSettings("Uncrossable body of water (dominant), with bank line", "Water", 1),
                                                      UAvailibleParceLineSettings("Uncrossable body of water (dominant)", "Water", 1),
                                                      UAvailibleParceLineSettings("Shallow body of water, with solid outline", "Water", 1),
                                                      UAvailibleParceLineSettings("Shallow body of water", "Water", 1),
                                                      UAvailibleParceLineSettings("Shallow body of water, solid outline", "Water", 1),
                                                      UAvailibleParceLineSettings("Shallow body of water, dashed outline", "Water", 1),
                                                      UAvailibleParceLineSettings("Small shallow body of water (full colour)", "Water", 1),
                                                      UAvailibleParceLineSettings("Crossable watercourse", "Water", 1),
                                                      UAvailibleParceLineSettings("Small crossable watercourse", "Water", 1),
                                                      UAvailibleParceLineSettings("Minor/seasonal water channel", "Water", 1),
                                                      UAvailibleParceLineSettings("Uncrossable marsh, with outline", "Water", 1),
                                                      UAvailibleParceLineSettings("Uncrossable marsh", "Water", 1),
                                                      UAvailibleParceLineSettings("Marsh", "Water", 1),
                                                      UAvailibleParceLineSettings("Narrow marsh", "Water", 1),
                                                      UAvailibleParceLineSettings("Waterhole", "Water", 1),
                                                      UAvailibleParceLineSettings("Marsh, minimum size", "Water", 1),
                                                      UAvailibleParceLineSettings("Indistinct marsh", "Water", 1),
                                                      UAvailibleParceLineSettings("Indistinct marsh, minimum size", "Water", 1),
                                                      UAvailibleParceLineSettings("Well, fountain or water tank", "Water", 1),
                                                      UAvailibleParceLineSettings("Spring", "Water", 1),
                                                      UAvailibleParceLineSettings("Prominent water feature", "Water", 1)
                                                      ]
        self.first_level_distance = 50  # Расстояние первого уровня (между линиями контура)
        self.remove_all_error_lines = False  # Удаление всех ошибочных линий
        self.min_owner_overlap = 0.95
        self.max_distance_to_slope_line = 20
        self.use_octree_to_fix_line = False
        self.use_octree_to_recive_slope_line = True
        self.blend_slope_line = True
        self.guess_slope_direction_by_rivers = True
        self.guess_slope_direction_by_rivers_range = 50
        self.guess_slope_direction_by_contour_line_angle = True

        self.fixing_lines_settings = [UFixingLinesSettings()]  # Настройки для исправления линий
        self.lines: Dict[str, List[line.ULine]] = {}  # Линии, которые будут обрабатываться
        for type in type_option:
            self.lines[type] = []
        self.octree_for_lines: Optional[Octree] = None

        # 5. Прочие настройки и делегаты
        self.border_polygon = None
        self.max_border_polygon = None
        self.end_cook_delegate = Delegates.UDelegate()
        self.progress_delegate = Delegates.UDelegate()
        self.error_lines_delegate = Delegates.UDelegate()
        self.fix_line_index = 0;


        self.save_tag = ['file_path', 'global_scale_multiplier', 'first_level_distance',
                         'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                         'remove_all_error_lines','min_owner_overlap', 'availible_parce_slope_line_setting',
                         'draw_with_slope_line_color', 'max_distance_to_slope_line', 'use_octree_to_fix_line',
                         'use_octree_to_recive_slope_line',  'blend_slope_line', 'seed',
                         'guess_slope_direction_by_rivers', 'guess_slope_direction_by_rivers_range',
                         'guess_slope_direction_by_contour_line_angle']
        self.ui_show_tag = ['global_scale_multiplier', 'first_level_distance',
                            'max_distance_to_border_polygon', 'draw_with_max_border_polygon',
                            'remove_all_error_lines','min_owner_overlap', 'availible_parce_slope_line_setting',
                            'draw_with_slope_line_color', 'max_distance_to_slope_line', 'use_octree_to_fix_line',
                            'use_octree_to_recive_slope_line',  'blend_slope_line', 'seed',
                            'guess_slope_direction_by_rivers', 'guess_slope_direction_by_rivers_range',
                            'guess_slope_direction_by_contour_line_angle']



    def to_dict(self):
        """Сериализуем только параметры, указанные в save_tag, включая список fixing_lines_settings и availible_parce_settings."""
        data = {k: getattr(self, k) for k in self.save_tag}
        # Сериализация списка fixing_lines_settings
        data['fixing_lines_settings'] = [settings.to_dict() for settings in self.fixing_lines_settings]
        data['availible_parce_contour_line_settings'] = [settings.to_dict() for settings in self.availible_parce_contour_line_settings]
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
        self.UpdateAvailibleParceLineOptions()

    def find_availible_parce_setting_by_name(self, name):
        for availible_parce_setting in self.availible_parce_settings:
            if(availible_parce_setting.name == name):
                return availible_parce_setting
        return None

    def UpdateAvailibleParceLineOptions(self):
        file_extension = self.file_path.split('.')[-1]
        options = []
        if file_extension == "omap":

            tree = ET.parse(self.file_path)
            root = tree.getroot()

            namespace = helper_functions.get_namespace(root)

            symbols_lines = {}

            for available_parce_contour_line in self.availible_parce_contour_line_settings:
                symbols_lines.update(
                    helper_functions.extract_symbols(root, available_parce_contour_line.name, namespace))

        elif file_extension == "bna":
            data = helper_functions.ReadFile(self.__file_path)
            for line in data.splitlines():
                stripped_line = line.strip()
                points = stripped_line.split(',')
                if not helper_functions.can_convert_to_float(points[0]):
                    points[0] = points[0].strip('"').strip()
                    if (not points[0] in options):
                        options.append(points[0])
            set_options_to_availible_parce_line_settings(options)
            for option in self.availible_parce_contour_line_settings:
                if (option):
                    option.update_options_by_global_options()
        elif file_extension == "ocd":
            pass
        else:
            print("Неизвестный тип файла")
            pass


    # Основная функция для парсинга XML-файла
    def parse_omap_hml(self):
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        namespace = helper_functions.get_namespace(root)

        lines_by_type = {}
        symbols_by_type = {}
        for type in type_option:
            lines_by_type[type] = []
            symbols_by_type[type] = []

        for available_parce_line in self.availible_parce_contour_line_settings:
            ID = helper_functions.extract_symbols(root, available_parce_line.name, namespace)
            symbols_by_type[available_parce_line.type].append(ID)

        objects = root.findall(f'.//{namespace}objects')
        for object in objects:
            for obj in object.findall(f'.//{namespace}object'):
                symbol_id = obj.get('symbol')
                sucsess_simbol = False
                sucsess_type = "None"
                for type in type_option:
                    for simbol in symbols_by_type[type]:
                        if symbol_id in simbol:
                            sucsess_simbol = True
                            sucsess_type = type
                            break
                if sucsess_simbol:
                    coords_element = obj.find(f'{namespace}coords')
                    if coords_element is None:
                        continue
                    coords = coords_element.text.strip()
                    coords = [coord.split(" ") for coord in coords.split(";")]
                    coords = helper_functions.fix_coordinates(coords)
                    coords_list = [[float(coord[0]) / 100 * self.global_scale_multiplier,
                                    float(coord[1]) / 100 * self.global_scale_multiplier] for coord in coords]
                    rotation = 0.0
                    if(obj.get('rotation') != None):
                        rotation = obj.get('rotation')
                    lines_by_type[sucsess_type].append({"coords_list" : coords_list, 'rotation': rotation})

        return lines_by_type

    def ImportNewFile(self):
        file_extension = self.file_path.split('.')[-1]
        if file_extension == "omap":
            lines_by_type  = self.parse_omap_hml()
            return lines_by_type
        elif file_extension == "bna":
            data = helper_functions.ReadFile(self.file_path)
            data_lines = self.ParseAllFromData(data)
            return data_lines
        elif file_extension == "ocd":
            return None
        else:
            print("Неизвестный тип файла")
            return None

    def ParseAllFromData(self, data):
        lines = []
        current_line = []
        sucsess = False
        for line in data.splitlines():
            stripped_line = line.strip()
            points = stripped_line.split(',')
            if not helper_functions.can_convert_to_float(points[0]):
                if current_line:
                    lines.append([current_line])
                    current_line = []
                if not self.find_availible_parce_setting_by_name(points[0]):
                    sucsess = True
            else:

                if len(points) == 2 and sucsess:
                    x = float(points[0]) * self.global_scale_multiplier
                    y = float(points[1]) * self.global_scale_multiplier
                    current_line.append([x, y])

        if current_line:
            lines.append([current_line])

        return lines

    def SetupBorderPoligonsDataFromLines(self, border_distance):
        """
            Generated Border By Lines inside.
        """
        points = []
        try:
            for line in self.lines["Contour"]:
                for segment in line.start_points:
                    points.append(segment)
        except:
            print("")



        points = np.array(points)

        unique_points = np.unique(points, axis=0)

        if len(unique_points) < 3:
            # Если точек меньше 3 или они лежат на одной прямой, используем LineString и создаем буфер
            line = LineString(unique_points)
            self.border_polygon = line.buffer(-1 * border_distance * self.global_scale_multiplier, join_style=2,
                                              cap_style=2)  # cap_style=2 для плоских концов
            self.max_border_polygon = line.buffer(self.max_distance_to_border_polygon * self.global_scale_multiplier, join_style=2, cap_style=2)

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

    def SetupSizeDataFromLines(self, lines_by_type):
        coords = []
        for type in lines_by_type:
            for line in lines_by_type[type]:
                for coord in line["coords_list"]:
                    coords.append(coord)

        self.min_width = min(coord[0] for coord in coords)
        self.max_width = max(coord[0] for coord in coords)
        self.min_height = min(coord[1] for coord in coords)
        self.max_height = max(coord[1] for coord in coords)

        self.width = self.max_width - self.min_width
        self.height = self.max_height - self.min_height

    def draw_polygon(self, draw, polygon, offset_x, offset_y, color, width=2):
        x, y = polygon.exterior.xy
        coords = [(int(x[i] + offset_x), int(y[i] + offset_y)) for i in range(len(x))]
        draw.line(coords, fill=color, width=width)

    def draw_lines(self, draw, lines, offset_x, offset_y):
        for line in lines["Contour"]:
            if len(line.points) >= 2:
                flat_coords = [(int(point[0] + offset_x), int(point[1] + offset_y)) for point in line.points]
                if(self.draw_with_slope_line_color):
                    if line.slope_direction == "None":
                        color = (255, 255, 255)
                    elif line.slope_direction == "Inside":
                        color = (0, 255, 0)
                    elif line.slope_direction == "Outside":
                        color = (255, 0, 0)
                    else:
                        color = (0, 0, 255)
                    draw.line(flat_coords, fill=color, width=2)
                else:
                    color = (line.color[0], line.color[1], line.color[2])
                    draw.line(flat_coords, fill=(line.color[0], line.color[1], line.color[2]), width=2)
        for line in lines["Water"]:
            if len(line.points) >= 2:
                flat_coords = [(int(point[0] + offset_x), int(point[1] + offset_y)) for point in line.points]
                draw.line(flat_coords, fill=(0, 46, 255), width=2)

    def DebugDrawLines(self, lines):
        if(self.draw_with_max_border_polygon):
            min_x, min_y, max_x, max_y = self.find_bounding_square(self.max_border_polygon)
            width = int(max_x - min_x + 1)
            height = int(max_y - min_y + 1)
        else:
            min_x = self.min_width
            max_x = self.max_width
            min_y = self.min_height
            max_y = self.max_height

            width = int(max_x - min_x + 1)
            height = int(max_y - min_y + 1)

        image = Image.new("RGB", (width, height), "black")
        draw = ImageDraw.Draw(image)

        offset_x = -min_x
        offset_y = -min_y

        self.draw_lines(draw, self.lines , offset_x, offset_y)

        if self.draw_with_max_border_polygon:
            self.draw_polygon(draw, self.border_polygon, offset_x, offset_y, "red")

            self.draw_polygon(draw, self.max_border_polygon, offset_x, offset_y, "green")

        image.save("lines_image.png")
        self.cook_image = image

        return image

    def direction_from_point_to_polygon(self, polygon, point):
        coords = list(polygon.exterior.coords)
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

    def GenerateLinesByLineData(self,lines_by_type):
        self.SetupSizeDataFromLines(lines_by_type)
        return self.GeneratedLineByCoords(lines_by_type)

    def FixMergeNearLines(self, setting:UFixingLinesSettings):

        if(setting.apply_merge_line_value):
            answer_lines = []
            availible_lines = self.lines["Contour"].copy()

            count = 0
            while len(availible_lines) >= 1:
                count = count + 1
                self.progress_delegate.invoke(
                    "fixing_lines_settings FixMergeNearLines : index = " + str(self.fix_line_index), int(count/len(self.lines)*100))

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

                    if(setting.enable_merge_with_self):
                        self_distance = Point(line.points[0]).distance(Point(line.points[-1]))
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

                            point_pairs = [
                                (0, 1, 0, 1),  # line.points[0] и test_line.points[0]
                                (0, 1, -1, -2),  # line.points[0] и test_line.points[-1]
                                (-1, -2 , -1, -2),  # line.points[-1] и test_line.points[-1]
                                (-1,-2, 0, 1),  # line.points[-1] и test_line.points[0]
                            ]
                            for i1, i2, i3, i4 in point_pairs:
                                try:
                                    p11 = line.points[i1]
                                    p12 = line.points[i2]
                                    p21 = test_line.points[i3]
                                    p22 = test_line.points[i4]

                                    if self.border_polygon.contains(Point(p11)) and self.border_polygon.contains(
                                            Point(p12)):
                                        test_distance = Point(p11).distance(Point(p21))
                                        if test_distance < optimal_line_const and test_distance < setting.max_merge_line_value:
                                            v1 = (p11[0] - p21[0], p11[1] - p21[1])
                                            v2 = (p12[0] - p11[0], p12[1] - p11[1])
                                            v3 = (p22[0] - p21[0], p22[1] - p21[1])
                                            angle_first = helper_functions.angle_between_vectors(v1, v2)
                                            if(angle_first>90):
                                                angle_first = 180 - angle_first
                                            angle_second = helper_functions.angle_between_vectors(v1, v3)
                                            if(angle_second>90):
                                                angle_second = 180 - angle_second
                                            if angle_first < setting.max_angle and angle_second < setting.max_angle:
                                                optimal_line_const = test_distance
                                                optimal_line_to_merge_index = k
                                                optimal_start_point_to_merge_index = i1
                                                optimal_end_point_to_merge_index = i3
                                except Exception as e:
                                    print("Wrong Geometry:", e)
                        k += 1

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
                        elif optimal_start_point_to_merge_index == 0 and optimal_end_point_to_merge_index == - 1:
                            line.points = line_to_merge.points + line.points
                            line.start_points = line.start_points + line_to_merge.start_points[::-1]
                        elif optimal_start_point_to_merge_index == - 1 and optimal_end_point_to_merge_index == - 1:
                            line.points = line.points + line_to_merge.points[::-1]
                            line.start_points = line.start_points + line_to_merge.start_points[::-1]
                        elif optimal_start_point_to_merge_index == -1 and optimal_end_point_to_merge_index == 0:
                            line.points = line.points + line_to_merge.points
                            line.start_points = line.start_points + line_to_merge.start_points

                        del availible_lines[optimal_line_to_merge_index]
                    else:
                        answer_lines.append(availible_lines[0])
                        del availible_lines[0]

            if availible_lines:
                answer_lines.append(availible_lines[0])
            self.lines["Contour"] = answer_lines

            return answer_lines
        else:
            return []

    def FixUnboarderLines(self, setting:UFixingLinesSettings):
        if(setting.apply_fix_unborder_lines):
            k = 0
            for line in self.lines["Contour"]:
                k = k + 1
                self.progress_delegate.invoke(
                    "fixing_lines_settings FixUnboarderLines : index = " + str(self.fix_line_index), int(k/len(self.lines["Contour"])*100))
                if (line.points[0] != line.points[-1]):
                    check_unborder = False

                    if(setting.fix_unborder_if_both_point_unborder):
                        check_unborder = not self.border_polygon.contains(Point(line.points[0])) and not self.border_polygon.contains(Point(line.points[-1]))
                    else:
                        check_unborder = not self.border_polygon.contains(Point(line.points[0])) or not self.border_polygon.contains(Point(line.points[-1]))
                    if check_unborder:
                        G = self.create_graph_from_polygon(self.max_border_polygon, setting.hight_find_direction)

                        projection_point, closest_segment =self.direction_from_point_to_polygon(self.max_border_polygon, line.points[0])
                        x_coordinate_start = projection_point.x
                        y_coordinate_start = projection_point.y
                        line.points.insert(0, (x_coordinate_start, y_coordinate_start))

                        start_vertex = self.find_closest_vertex(self.max_border_polygon, Point((x_coordinate_start, y_coordinate_start)))

                        projection_point, closest_segment = self.direction_from_point_to_polygon(self.max_border_polygon, line.points[-1])
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
        for line in self.lines["Contour"]:
            if(line.IsLineClose()) and line.CheckLineNumberPoint():
                line.correct_line =True
            else:
                line.correct_line = False

    def GeneratedOctree(self):
        self.octree_for_lines = Octree(boundary=(self.min_width, self.min_height, self.max_width, self.max_height), capacity=4)
        for line in self.lines["Contour"]:
            self.octree_for_lines.insert(line)


    def GeneratedNestingOfLines(self):
        """ Сама идея очень проста - мы перебираем все элементы последовательно, удаляя пройденный элемент.
         Поскольку проейденые элементы больше не прокручиваются, кода настолько много - выбирается как себе parent, так и предположительные Child.
         Проверки работают на случай косяка предыдуших этапов.
        """
        uncheck_lines = self.lines["Contour"].copy()
        k = 0
        while len(uncheck_lines) > 0:
            k = k + 1
            self.progress_delegate.invoke("generated_neasting_of_lines", int(k/len(self.lines["Contour"])*100))
            check_line = uncheck_lines[0]
            uncheck_lines.remove(check_line)
            min_parent_area = 1000000000
            min_parent = None
            for uncheck_line in uncheck_lines:
                if (check_line.shapely_polygon and uncheck_line.shapely_polygon):
                    if (check_line.evaluate_polygon_overlap(uncheck_line)>self.min_owner_overlap):
                        if check_line.shapely_polygon.area > uncheck_line.shapely_polygon.area:
                            last_parent = uncheck_line.parent
                            uncheck_line.parent = check_line
                            if (uncheck_line.CheckLineParentLoop([])):
                                uncheck_line.parent = last_parent
                            else:
                                if (last_parent and check_line in last_parent.childs):
                                    last_parent.childs.remove(uncheck_line)
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
        for line in self.lines["Contour"]:
            if(line.correct_line == False):
                error_lines.append(line)
        return error_lines

    def RemoveAllErrorLines(self):
        error_lines = self.GetAllErrorLines()
        for error_line in error_lines:
            self.lines["Contour"].remove(error_line)

    def get_normal_from_segment(self, closest_segment, polygon):
        """
        Вычисляет нормаль к отрезку (closest_segment) и проверяет, что она направлена наружу из многоугольника.

        Параметры:
        closest_segment : LineString
            Отрезок, к которому нужно получить нормаль.
        polygon : Polygon
            Многоугольник, из которого нормаль должна быть направлена.

        Возвращает:
        tuple
            Координаты нормали (x, y) от центра отрезка, направленной наружу многоугольника.
        """

        x1, y1 = closest_segment.coords[0]
        x2, y2 = closest_segment.coords[1]

        segment_vector = (x2 - x1, y2 - y1)

        length = ((segment_vector[0] ** 2) + (segment_vector[1] ** 2)) ** 0.5
        if length == 0:
            raise ValueError("Отрезок не может иметь нулевую длину.")

        unit_segment_vector = (segment_vector[0] / length, segment_vector[1] / length)

        normal_vector = (-unit_segment_vector[1], unit_segment_vector[0])  # Поворот на 90 градусов

        mid_point = Point((x1 + x2) / 2, (y1 + y2) / 2)

        test_point = Point(mid_point.x + normal_vector[0] * 0.01, mid_point.y + normal_vector[1] * 0.01)

        if polygon.contains(test_point):
            normal_vector = (-normal_vector[0], -normal_vector[1])

        return normal_vector


    def GeneratedSlopeDirectionEvent(self):
        if(self.use_octree_to_recive_slope_line):
            k = 0
            for slope_line_coord in self.lines["Slope line"]:
                k = k + 1
                self.progress_delegate.invoke("GeneratedSlopeDirectionEvent", int(k / len(self.lines["Slope line"]) * 100))
                coord = slope_line_coord.points[0]
                rotation = slope_line_coord.rotation
                closed_line, dist = self.octree_for_lines.nearest_neighbor_in_range(coord, self.max_distance_to_slope_line)
                if(closed_line):
                    projection_point, closest_segment = self.direction_from_point_to_polygon(
                        closed_line.shapely_polygon, coord)
                    normal = self.get_normal_from_segment(closest_segment, closed_line.shapely_polygon)
                    normal = (
                    normal[0] * 100 * self.global_scale_multiplier, normal[1] * 100 * self.global_scale_multiplier)
                    project_point = [projection_point.x + normal[0], projection_point.y + normal[1]]
                    ray_distance = 10000
                    end_x = project_point[0] + ray_distance * math.cos(rotation + math.pi / 2)
                    end_y = project_point[1] + ray_distance * math.sin(rotation + math.pi / 2)

                    ray = LineString([(project_point[0], project_point[1]), (end_x, end_y)])

                    if ray.intersects(closed_line.shapely_polygon.exterior):
                        closed_line.slope_direction = "Outside"
                    else:
                        closed_line.slope_direction = "Inside"
        else:
            k = 0
            for slope_line_coord in self.lines["Slope line"]:
                k = k + 1
                self.progress_delegate.invoke("GeneratedSlopeDirectionEvent", int(k/len(self.lines["Slope line"])*100))
                min_distance = self.max_distance_to_slope_line;
                closed_line = None
                coord = slope_line_coord.points[0]
                rotation = slope_line_coord.rotation
                for line in self.lines["Contour"]:
                    if(line.slope_direction =="None"):
                        projection_point, closest_segment = self.direction_from_point_to_polygon(line.shapely_polygon, coord)
                        if(min_distance>((projection_point.x - coord[0])**2 + (projection_point.y - coord[1])**2)):
                            min_distance = (projection_point.x - coord[0])**2 + (projection_point.y - coord[1])**2
                            closed_line = line

                if(closed_line):
                    projection_point, closest_segment = self.direction_from_point_to_polygon(closed_line.shapely_polygon, coord)
                    normal = self.get_normal_from_segment(closest_segment, closed_line.shapely_polygon)
                    normal = (normal[0]*100*self.global_scale_multiplier, normal[1]*100*self.global_scale_multiplier )
                    project_point = [projection_point.x +  normal[0], projection_point.y +  normal[1]]
                    ray_distance = 10000
                    end_x = project_point[0] + ray_distance * math.cos(rotation + math.pi/2)
                    end_y = project_point[1] + ray_distance * math.sin(rotation + math.pi/2)

                    ray = LineString([(project_point[0], project_point[1]), (end_x, end_y)])

                    if len(ray.intersects(closed_line.shapely_polygon.exterior)%2 == 1):
                        closed_line.slope_direction = "Outside"# Красный для Outside
                    else:
                        closed_line.slope_direction = "Inside" # Зеленый для Inside

        if self.guess_slope_direction_by_rivers:
            for water_line in self.lines["Water"]:
                min_range, max_range = water_line.GetRange()
                min_range[0] = min_range[0] - self.guess_slope_direction_by_rivers_range
                min_range[1] = min_range[1] - self.guess_slope_direction_by_rivers_range
                max_range[0] = max_range[0] + self.guess_slope_direction_by_rivers_range
                max_range[1] = max_range[1] + self.guess_slope_direction_by_rivers_range

                near_counter_lines : List[line_library.ULine] = self.octree_for_lines.query([min_range[0],min_range[1], max_range[0],max_range[1]])
                error_lines = [line for line in near_counter_lines if line.slope_direction == "None"]
                if(len(error_lines)==0):
                    continue;
                for error_line in error_lines:
                    water_line.CreateLine()
                    error_line.CreateLine()
                    if (water_line.line_string.intersects(error_line.line_string)):
                        intersection: Optional[Point] = water_line.line_string.intersection(error_line.line_string)
                        radius = 25;
                        circle = intersection.buffer(radius, resolution=64)
                        intersection_circle_point = water_line.line_string.intersection(circle)

                        if (intersection_circle_point.geom_type == 'Point'):
                            ray_distance = 10000
                            end_x = intersection_circle_point.coords[0].x + ray_distance * (
                                        intersection.coords[0].x - intersection_circle_point.coords[0].x)
                            end_y = intersection_circle_point.coords[1].y + ray_distance * (
                                        intersection.coords[0].y - intersection_circle_point.coords[0].y)
                            ray = LineString(
                                [(intersection_circle_point.coords[0].x, intersection_circle_point.coords[1].y), (end_x, end_y)])
                            if len(ray.intersects(error_line.shapely_polygon.exterior) % 2 == 1):
                                error_line.slope_direction = "Outside"  # Красный для Outside
                            else:
                                error_line.slope_direction = "Inside"  # Зеленый для Inside

                            pass

                        elif intersection_circle_point.geom_type == "Multipoint":
                            checked_coords: List[Point] = []
                            for coord in water_line.line_string.coords:
                                if (intersection.distance(coord) < radius):
                                    checked_coords.append(coord)
                            in_sum = 0.0
                            out_sum = 0.0
                            for check_coord in checked_coords:
                                in_sum += intersection_circle_point.coords[0].distance(check_coord)
                                out_sum += intersection_circle_point.coords[1].distance(check_coord)
                            if(in_sum!=0.0 and out_sum!=0.0):
                                if(in_sum>out_sum):
                                    ray_distance = 10000
                                    end_x = intersection_circle_point.coords[0].x + ray_distance * (intersection.coords[0].x - intersection_circle_point.coords[0].x)
                                    end_y = intersection_circle_point.coords[0].y + ray_distance * (intersection.coords[0].y - intersection_circle_point.coords[0].y)
                                    ray = LineString([(intersection_circle_point.coords[0].x, intersection_circle_point.coords[1].y), (end_x, end_y)])
                                    if len(ray.intersects(error_line.shapely_polygon.exterior) % 2 == 1):
                                        error_line.slope_direction = "Outside"  # Красный для Outside
                                    else:
                                        error_line.slope_direction = "Inside"  # Зеленый для Inside
                                else:
                                    ray_distance = 10000
                                    end_x = intersection_circle_point.coords[1].x + ray_distance * (intersection.coords[1].x - intersection_circle_point.coords[1].x)
                                    end_y = intersection_circle_point.coords[1].y + ray_distance * (intersection.coords[1].y - intersection_circle_point.coords[1].y)
                                    ray = LineString(
                                        [(intersection_circle_point.coords[0].x, intersection_circle_point.coords[1].y), (end_x, end_y)])
                                    if len(ray.intersects(error_line.shapely_polygon.exterior) % 2 == 1):
                                        error_line.slope_direction = "Outside"  # Красный для Outside
                                    else:
                                        error_line.slope_direction = "Inside"  # Зеленый для Inside

                    else:
                        if (error_line.shapely_polygon):
                            if (error_line.shapely_polygon.contains(water_line.line_string)):
                                error_line.slope_direction = "Inside"
                            else:
                                if (error_line.shapely_polygon.contains(water_line.line_string)):
                                    error_line.slope_direction = "Outside"

                                '''
                                distance = 100000000
                                answer_projection_point = Point(0, 0)
                                answer_closest_segment = None

                                for water_line_point in water_line.points:
                                    projection_point, closest_segment = self.direction_from_point_to_polygon(
                                        error_line.shapely_polygon, water_line_point)
                                    if (projection_point.distance(water_line_point) < distance):
                                        distance = projection_point.distance(water_line_point)
                                        answer_projection_point = projection_point
                                        answer_closest_segment = closest_segment

                                    normal = self.get_normal_from_segment(answer_closest_segment,
                                                                          error_line.shapely_polygon)
                                    normal = (normal[0] * 100 * self.global_scale_multiplier,
                                              normal[1] * 100 * self.global_scale_multiplier)
                                    project_point = [projection_point.x + normal[0], projection_point.y + normal[1]]
                                    ray_distance = 10000
                                    end_x = project_point[0]
                                    end_y = project_point[1]

                                ray = LineString([])

                                if len(ray.intersects(error_line.shapely_polygon.exterior) % 2 == 1):
                                    error_line.slope_direction = "Outside"
                                else:
                                    error_line.slope_direction = "Inside"
                                '''



        if self.blend_slope_line:
            error_lines = [{"line": line, "counter": 0} for line in self.lines["Contour"] if line.slope_direction == "None"]
            counter = 0

            while error_lines:
                if counter >= len(error_lines):
                    counter = 0

                item = error_lines[counter]
                line = item["line"]
                number_repeat = item["counter"]

                if number_repeat > 10:
                    error_lines.pop(counter)
                    continue

                counter_line_result = {"Inside": 0, "Outside": 0}

                sum_connections = (1 if line.parent else 0) + len(line.childs)

                if line.parent:
                    if line.parent.slope_direction == "Inside":
                        counter_line_result["Inside"] += 1
                    if line.parent.slope_direction == "Outside":
                        counter_line_result["Outside"] += 1

                for child in line.childs:
                    if child.slope_direction == "Inside":
                        counter_line_result["Inside"] += 1
                    if child.slope_direction == "Outside":
                        counter_line_result["Outside"] += 1

                success_operation = False
                known_connections = counter_line_result["Inside"] + counter_line_result["Outside"]

                if known_connections > 0:
                    inside_ratio = counter_line_result["Inside"] / known_connections
                    outside_ratio = counter_line_result["Outside"] / known_connections

                    if inside_ratio >= 0.5:
                        line.slope_direction = "Inside"
                        success_operation = True
                    elif outside_ratio >= 0.5:
                        line.slope_direction = "Outside"
                        success_operation = True

                if success_operation:
                    error_lines.pop(counter)
                else:
                    item["counter"] += 1
                    counter += 1


    def GeneratedLineByCoords(self, lines_by_type):
        for type in lines_by_type:
            for line in lines_by_type[type]:
                new_line = line_library.ULine(self.seed, None, [], None, None, line["coords_list"], line["rotation"], 0.0)
                new_line.correct_line = True
                self.lines[type].append(new_line)

        self.SetupBorderPoligonsDataFromLines(-2)

        if(self.use_octree_to_fix_line):
            self.GeneratedOctree()
        self.fix_line_index = 0
        for setting in self.fixing_lines_settings:
            self.progress_delegate.invoke("fixing_lines_settings FixMergeNearLines : index = " + str(self.fix_line_index ), 0)
            self.FixMergeNearLines(setting)
            if(setting.regenerate_borders):
                self.SetupBorderPoligonsDataFromLines(setting.border_distance)
            self.progress_delegate.invoke("fixing_lines_settings FixUnboarderLines : index = " + str(self.fix_line_index ), 0)
            self.FixUnboarderLines(setting)
            self.fix_line_index  = self.fix_line_index  + 1

        self.progress_delegate.invoke("generated_neasting_of_lines", 0)
        for line in self.lines["Contour"]:
            line.CreatePoligon()
        self.GeneratedNestingOfLines()
        self.progress_delegate.invoke("GeneratedSlopeDirectionEvent", 0)
        if (self.use_octree_to_recive_slope_line):
            self.GeneratedOctree()
        self.GeneratedSlopeDirectionEvent()

        self.CheckErrorLines()

        error_lines = self.GetAllErrorLines()
        self.count_error_lines = len(error_lines)
        self.error_lines_delegate.invoke(self.GetAllErrorLines())

        if(self.remove_all_error_lines):
            self.RemoveAllErrorLines()

        self.progress_delegate.invoke("All preparations are completed", 100)


    def FindOwnerLine(self, point, root_lines):
        for line in root_lines:
            if(not line.shapely_polygon):
                continue
            if(line.shapely_polygon.contains(point)):
                if(len(line.childs)>0):
                    result = self.FindOwnerLine(point, line.childs)
                    if(result):
                        return result
                    else:
                        return line
                else:
                    return line
        return None

    def CalculateOwnerLineDepth(self, owner_line):
        if(not owner_line):
            return 0;
        else:
            return owner_line.GetSlopeDirectionDepthFromLineToUp()

    def DrawPlotHeightMap(self):
        root_lines = line_library.GetRootLines(self.lines["Contour"])
        if(len(root_lines)<=0):
            return
        min_depth, max_depth = line_library.GetMinAndMaxSlopeDirectionDepthByLines(root_lines)
        print("Depth equal " + str(max_depth - min_depth))
        image = Image.new("L",
                          (int(self.width + self.first_level_distance), int(self.height + self.first_level_distance)),
                          "black")
        draw = ImageDraw.Draw(image)

        k = 0
        for y in range(int(self.height + self.first_level_distance)):
            for x in range(int(self.width + self.first_level_distance)):
                self.progress_delegate.invoke("Generate Texture", int(k / (
                            int(self.height + self.first_level_distance) * int(
                        self.width + self.first_level_distance)) * 100))
                point = Point(int(x + self.min_width - self.first_level_distance / 2),
                              int(y + self.min_height - self.first_level_distance / 2))

                owner_line = self.FindOwnerLine(point, root_lines)
                intensity = -min_depth + self.CalculateOwnerLineDepth(owner_line)

                if owner_line:
                    tmp_points = []
                    owner_line_point, closest_segment = self.direction_from_point_to_polygon(owner_line.shapely_polygon, [point.x, point.y])
                    for child_line in owner_line.childs:
                        if isinstance(child_line, int):
                            print(child_line.childs)
                            continue
                        child_line_point, closest_segment = self.direction_from_point_to_polygon(child_line.shapely_polygon, [point.x, point.y])
                        dist_to_point = child_line_point.distance(point)
                        if(dist_to_point < self.first_level_distance):
                            clamped_first_level_distance = clamp(self.first_level_distance, 1, min(child_line_point.distance(owner_line_point),self.first_level_distance ))
                            if child_line.slope_direction == "Outside":
                                tmp_points.append([child_line_point,  dist_to_point/clamped_first_level_distance, intensity + 1])
                            elif child_line.slope_direction == "Inside":
                                tmp_points.append([child_line_point,  dist_to_point/clamped_first_level_distance, intensity - 1])
                            else:
                                tmp_points.append([child_line_point,  dist_to_point/clamped_first_level_distance, intensity + 1])
                    sum_points = 0.0
                    for l_point in tmp_points:
                        sum_points = sum_points + l_point[1]
                    sum_weight = 0.0
                    lerp_multiply = 1.0
                    for l_point in tmp_points:
                        lerp_multiply = lerp_multiply * l_point[1]
                        sum_weight = sum_weight + l_point[1]/sum_points * l_point[2]
                    intensity = lerp_multiply * intensity + (1 - lerp_multiply) * sum_weight

                else:
                    sum_distance = 0.0
                    for child in root_lines:
                        min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                        if (min_distance_to_child_poligon < self.first_level_distance):
                            sum_distance += min_distance_to_child_poligon
                    intensity_sum = 0.0
                    if (sum_distance != 0.0):
                        for child in root_lines:
                            min_distance_to_child_poligon = point.distance(child.shapely_polygon.exterior)
                            if (min_distance_to_child_poligon < self.first_level_distance):
                                normalize_distance_to_child_poligon = clamp(
                                    min_distance_to_child_poligon / sum_distance, 0, 1) * clamp(
                                    (1 - min_distance_to_child_poligon / self.first_level_distance), 0, 1)
                                if (child.slope_direction == "Outside"):
                                    intensity_sum += normalize_distance_to_child_poligon
                                elif (child.slope_direction == "Inside"):
                                    intensity_sum -= normalize_distance_to_child_poligon
                                else:
                                    intensity_sum += normalize_distance_to_child_poligon
                        intensity = intensity + intensity_sum

                white_intensity = clamp(int(intensity * 255 / (max_depth - min_depth)),0,255)
                draw.point((int(x), int(y)), fill=white_intensity)
                k = k + 1
        self.cook_image = image
        self.progress_delegate.invoke("Complete", 100)
        return image

    def MainLaunchOperations(self):
        if(os.path.exists(self.file_path)):
            lines_by_type = self.ImportNewFile()
            self.GenerateLinesByLineData(lines_by_type)
            if (self.draw_debug_lines):
                self.DebugDrawLines(self.lines["Contour"])
                self.end_cook_delegate.invoke()
            else:
                self.DrawPlotHeightMap()
                self.end_cook_delegate.invoke()

