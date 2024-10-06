from shapely.geometry import Polygon, Point, LineString
import networkx as nx
import matplotlib.pyplot as plt


def create_graph_from_polygon(polygon, direction='both'):
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
            G.add_edge(i, i + 1, weight=LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]]).length)
        if direction == 'backward' or direction == 'both':
            G.add_edge(i + 1, i, weight=LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]]).length)

    # Замыкаем полигон
    if direction == 'forward' or direction == 'both':
        G.add_edge(len(polygon.exterior.coords) - 1, 0,
                   weight=LineString([polygon.exterior.coords[-1], polygon.exterior.coords[0]]).length)
    if direction == 'backward' or direction == 'both':
        G.add_edge(0, len(polygon.exterior.coords) - 1,
                   weight=LineString([polygon.exterior.coords[-1], polygon.exterior.coords[0]]).length)

    return G


def find_closest_vertex(polygon, point):
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


def find_path_one_way(G, start_vertex, end_vertex):
    """
    Поиск пути в графе только в одну сторону, с использованием направленного графа.
    """
    try:
        path = nx.shortest_path(G, start_vertex, end_vertex)
    except nx.NetworkXNoPath:
        path = None  # Если пути нет
    return path


# Визуализация полигона и путей
def plot_path(polygon, path, G, title="Path"):
    fig, ax = plt.subplots()
    x, y = polygon.exterior.xy
    ax.plot(x, y, 'o-', label="Polygon")

    path_coords = [G.nodes[i]['coord'] for i in path]
    path_line = LineString(path_coords)
    px, py = path_line.xy
    ax.plot(px, py, 'r-', label="Path")

    ax.set_title(title)
    plt.legend()
    plt.show()


def get_path_points(G, path):
    """
    Возвращает список координат точек для заданного пути
    """
    return [G.nodes[i]['coord'] for i in path]


# Пример использования

# Создаем полигон (например, пятиугольник)
polygon = Polygon([(0, 0), (4, 0), (5, 3), (3, 5), (1, 4)])

# Задаем две точки на гранях полигона
point1 = Point(2, 0)  # Лежит на первой грани
point2 = Point(3, 5)  # Лежит на четвертой грани

# Задаем общее направление для всего графа
direction = 'forward'  # Возможные значения: 'forward', 'backward', 'both'

# Создаем граф из полигона с указанным направлением
G = create_graph_from_polygon(polygon, direction)

# Находим ближайшие вершины к нашим точкам
start_vertex = find_closest_vertex(polygon, point1)
end_vertex = find_closest_vertex(polygon, point2)

# Поиск пути в одну сторону (направленный граф)
one_way_path = find_path_one_way(G, start_vertex, end_vertex)

if one_way_path:
    # Выводим путь в виде индексов вершин
    print("Путь в одну сторону (индексы):", one_way_path)

    # Преобразуем индексы в координаты точек
    path_points = get_path_points(G, one_way_path)

    # Выводим координаты точек пути
    print("Путь в одну сторону (координаты точек):", path_points)

    # Визуализация пути
    plot_path(polygon, one_way_path, G, title="One Way Path")
else:
    print("Путь в одну сторону отсутствует.")
