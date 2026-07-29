"""Shortest-path maze solver.

Breadth-first search over the open-passage graph of a :class:`Maze`.
Two public helpers share the same search: :func:`solve` returns the
shortest route as move letters (``'N'``/``'E'``/``'S'``/``'W'``) while
:func:`path_cells` returns the same route as ``(x, y)`` cells.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from mazegen.grid import LETTER, Maze

#: One step of a reconstructed path: a cell and the direction moved to
#: reach it (``None`` for the entry cell).
_Step = tuple[tuple[int, int], Optional[int]]


def _reconstruct(
    parents: dict[tuple[int, int], _Step],
    entry: tuple[int, int],
    exit: tuple[int, int],
) -> list[_Step]:
    """Walk ``parents`` back from ``exit`` to ``entry`` into a path."""
    path: list[_Step] = []
    cell = exit
    while cell != entry:
        prev, direction = parents[cell]
        path.append((cell, direction))
        cell = prev
    path.append((entry, None))
    path.reverse()
    return path


def _bfs_path(
    maze: Maze,
    entry: tuple[int, int],
    exit: tuple[int, int],
) -> list[_Step]:
    """Return the shortest ``entry``->``exit`` path as steps.

    Each element pairs a cell with the direction moved to reach it; the
    first element is ``(entry, None)``. Breadth-first search guarantees
    the returned path is a shortest one.

    Raises:
        ValueError: If ``entry`` or ``exit`` is out of bounds, or if
            ``exit`` cannot be reached from ``entry``.
    """
    if not maze.in_bounds(*entry):
        raise ValueError(f"entry {entry} is out of bounds")
    if not maze.in_bounds(*exit):
        raise ValueError(f"exit {exit} is out of bounds")
    if entry == exit:
        return [(entry, None)]

    parents: dict[tuple[int, int], _Step] = {entry: (entry, None)}
    queue: deque[tuple[int, int]] = deque([entry])
    while queue:
        x, y = queue.popleft()
        for nx, ny, direction in maze.neighbors(x, y):
            nxt = (nx, ny)
            if nxt in parents or not maze.is_open(x, y, direction):
                continue
            parents[nxt] = ((x, y), direction)
            if nxt == exit:
                return _reconstruct(parents, entry, exit)
            queue.append(nxt)
    raise ValueError(
        f"exit {exit} is unreachable from entry {entry}"
    )


def solve(
    maze: Maze,
    entry: tuple[int, int],
    exit: tuple[int, int],
) -> list[str]:
    """Return the shortest route from ``entry`` to ``exit`` as letters.

    The result is a list of move letters (``'N'``/``'E'``/``'S'``/
    ``'W'``); an empty list means ``entry == exit``.

    Raises:
        ValueError: If ``entry``/``exit`` is out of bounds or ``exit``
            is unreachable.
    """
    return [
        LETTER[direction]
        for _, direction in _bfs_path(maze, entry, exit)
        if direction is not None
    ]


def path_cells(
    maze: Maze,
    entry: tuple[int, int],
    exit: tuple[int, int],
) -> list[tuple[int, int]]:
    """Return the shortest route as ``(x, y)`` cells, inclusive.

    The list runs from ``entry`` to ``exit``; ``entry == exit`` yields
    ``[entry]``.

    Raises:
        ValueError: If ``entry``/``exit`` is out of bounds or ``exit``
            is unreachable.
    """
    return [cell for cell, _ in _bfs_path(maze, entry, exit)]
