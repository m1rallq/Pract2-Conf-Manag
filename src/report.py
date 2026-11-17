"""Текстовый отчёт о построенном графе зависимостей."""

NONE_MARK = "—"


def _join(names):
    """Список имён через запятую или прочерк, если список пуст."""
    return ", ".join(names) if names else NONE_MARK


def format_levels(graph):
    """Пакеты по уровням глубины в порядке обхода BFS."""
    levels = {}
    for name, level in graph.depth.items():
        levels.setdefault(level, []).append(name)
    return [f"  уровень {level}: {_join(names)}"
            for level, names in sorted(levels.items())]


def format_edges(graph):
    """Список смежности: пакет -> его зависимости."""
    lines = []
    for name in graph.depth:
        if name in graph.errors:
            lines.append(f"  {name} -> ? (ошибка: {graph.errors[name]})")
        elif name in graph.edges:
            lines.append(f"  {name} -> {_join(graph.edges[name])}")
        else:
            lines.append(f"  {name} -> ... (не раскрыт: достигнута "
                         "глубина)")
    return lines


def format_cycles(graph):
    """Найденные циклы в виде A -> B -> A."""
    if not graph.cycles:
        return ["  не найдены"]
    return ["  " + " -> ".join(cycle) for cycle in graph.cycles]


def format_graph(graph, name_filter=None):
    """Полный текстовый отчёт о графе зависимостей."""
    lines = [
        f"Граф зависимостей пакета {graph.root} "
        f"(глубина до {graph.max_depth}, "
        f"фильтр: {name_filter or NONE_MARK})",
        "",
        "Пакеты по уровням (порядок обхода BFS):",
    ]
    lines += format_levels(graph)
    lines += ["", "Зависимости:"]
    lines += format_edges(graph)
    lines += ["", "Циклические зависимости:"]
    lines += format_cycles(graph)
    lines += [
        "",
        f"Итого: пакетов {len(graph.depth)}, связей {graph.edge_count}",
        f"Исключены фильтром: {_join(graph.filtered)}",
        f"Не раскрыты из-за глубины: {_join(graph.unexpanded)}",
    ]
    return "\n".join(lines)
