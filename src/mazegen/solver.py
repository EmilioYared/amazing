"""Shortest-path maze solver.

Breadth-first search over the open passages of a :class:`Maze`.
:func:`solve` returns the route as move letters, :func:`path_cells` the
same route as cells.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from mazegen.grid import LETTER, Maze

#: One path step: a cell and the direction taken to reach it.
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
    """Return the shortest ``entry`` -> ``exit`` path as steps.

    Args:
        maze: The maze to search.
        entry: The ``(x, y)`` start cell.
        exit: The ``(x, y)`` goal cell.

    Returns:
        Steps from ``entry`` to ``exit``, the first being
        ``(entry, None)``.

    Raises:
        ValueError: If a cell is out of bounds or ``exit`` is
            unreachable.
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
    """Return the shortest route as ``N``/``E``/``S``/``W`` letters.

    Args:
        maze: The maze to solve.
        entry: The ``(x, y)`` start cell.
        exit: The ``(x, y)`` goal cell.

    Returns:
        The move letters; empty when ``entry == exit``.

    Raises:
        ValueError: If a cell is out of bounds or ``exit`` is
            unreachable.
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

    Args:
        maze: The maze to solve.
        entry: The ``(x, y)`` start cell.
        exit: The ``(x, y)`` goal cell.

    Returns:
        The cells from ``entry`` to ``exit``.

    Raises:
        ValueError: If a cell is out of bounds or ``exit`` is
            unreachable.
    """
    return [cell for cell, _ in _bfs_path(maze, entry, exit)]
