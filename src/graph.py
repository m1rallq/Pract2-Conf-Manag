"""Построение графа зависимостей обходом в ширину (BFS) без рекурсии.

Граф хранится как список смежности: словарь «пакет -> его зависимости».
Обход идёт слоями с помощью очереди collections.deque: сначала все
пакеты на глубине 1, потом на глубине 2 и т. д. Каждый пакет
раскрывается один раз, поэтому циклы не приводят к зацикливанию.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List

WHITE = "white"
GRAY = "gray"
BLACK = "black"


class GraphError(Exception):
    """Не удалось получить зависимости одного из пакетов."""


@dataclass
class DependencyGraph:
    """Результат обхода графа зависимостей.

    Attributes:
        root: анализируемый пакет.
        max_depth: заданная максимальная глубина.
        depth: пакет -> глубина (в порядке обхода BFS).
        edges: пакет -> его зависимости (только раскрытые пакеты).
        filtered: пакеты, исключённые фильтром.
        unexpanded: пакеты на предельной глубине, не раскрытые дальше.
        errors: пакет -> сообщение, если его данные получить не удалось.
        cycles: найденные циклы (каждый — список пакетов).
    """

    root: str
    max_depth: int
    depth: Dict[str, int] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)
    filtered: List[str] = field(default_factory=list)
    unexpanded: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)

    @property
    def edge_count(self):
        """Количество рёбер (связей «пакет -> зависимость»)."""
        return sum(len(children) for children in self.edges.values())


def is_filtered(name, name_filter):
    """True, если имя содержит подстроку фильтра (без учёта регистра)."""
    return bool(name_filter) and name_filter.lower() in name.lower()


def _children(graph, name, direct):
    """Возвращает зависимости пакета; ошибку некорневого пакета запоминает.

    Ошибка самого анализируемого пакета пробрасывается дальше: без него
    граф построить нельзя. Ошибка любого другого пакета не прерывает
    обход — пакет остаётся в графе как лист с пометкой.
    """
    try:
        return direct(name)
    except GraphError as error:
        if name == graph.root:
            raise
        graph.errors[name] = str(error)
        return []


def _add_unique(items, value):
    """Добавляет значение в список, если его там ещё нет."""
    if value not in items:
        items.append(value)


def build_graph(root, direct, max_depth, name_filter=None):
    """Строит граф зависимостей пакета root обходом в ширину.

    Args:
        root: имя анализируемого пакета (глубина 0).
        direct: функция «имя -> список прямых зависимостей».
        max_depth: пакеты на этой глубине не раскрываются дальше.
        name_filter: подстрока; пакеты с ней в имени не учитываются.

    Raises:
        GraphError: если не удалось получить зависимости root.
    """
    graph = DependencyGraph(root=root, max_depth=max_depth)
    graph.depth[root] = 0
    queue = deque([root])
    while queue:
        name = queue.popleft()
        level = graph.depth[name]
        if level >= max_depth:
            graph.unexpanded.append(name)
            continue
        graph.edges[name] = []
        for child in _children(graph, name, direct):
            if is_filtered(child, name_filter):
                _add_unique(graph.filtered, child)
                continue
            _add_unique(graph.edges[name], child)
            if child not in graph.depth:
                graph.depth[child] = level + 1
                queue.append(child)
    graph.cycles = find_cycles(graph.edges)
    return graph


def _normalize_cycle(cycle):
    """Поворачивает цикл так, чтобы он начинался с меньшего имени."""
    start = cycle.index(min(cycle))
    return tuple(cycle[start:] + cycle[:start])


def find_cycles(edges):
    """Находит циклы в графе обходом в глубину без рекурсии.

    Вершина «серая», пока она на текущем пути, и «чёрная», когда
    полностью обработана. Ребро в серую вершину замыкает цикл.

    Returns:
        Список циклов; каждый — список имён, где последнее
        совпадает с первым (A, B, C, A).
    """
    color = {}
    found = {}
    for start in edges:
        if color.get(start, WHITE) != WHITE:
            continue
        path = [start]
        stack = [iter(edges.get(start, []))]
        color[start] = GRAY
        while stack:
            child = next(stack[-1], None)
            if child is None:
                color[path.pop()] = BLACK
                stack.pop()
            elif color.get(child, WHITE) == GRAY:
                cycle = path[path.index(child):]
                key = _normalize_cycle(cycle)
                found.setdefault(key, list(key) + [key[0]])
            elif color.get(child, WHITE) == WHITE:
                color[child] = GRAY
                path.append(child)
                stack.append(iter(edges.get(child, [])))
    return list(found.values())
