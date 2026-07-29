"""Tests for :mod:`mazegen.generator`."""

from __future__ import annotations

from typing import List, Set, Tuple

import pytest

from mazegen.generator import DisconnectedMazeError, MazeGenerator
from mazegen.grid import ALL, E, S, Maze

_Cell = Tuple[int, int]


def _open_internal_edges(maze: Maze) -> int:
    """Count distinct open internal walls (each undirected edge once)."""
    count = 0
    for y in range(maze.height):
        for x in range(maze.width):
            for nx, ny, direction in maze.neighbors(x, y):
                if direction in (E, S) and maze.is_open(x, y, direction):
                    count += 1
    return count


def _reachable(maze: Maze, start: _Cell) -> Set[_Cell]:
    """Return every cell reachable from ``start`` through open walls."""
    seen: Set[_Cell] = {start}
    stack: List[_Cell] = [start]
    while stack:
        x, y = stack.pop()
        for nx, ny, direction in maze.neighbors(x, y):
            if maze.is_open(x, y, direction) and (nx, ny) not in seen:
                seen.add((nx, ny))
                stack.append((nx, ny))
    return seen


def test_reproducible_with_same_seed() -> None:
    """Two generators with the same seed produce identical rows."""
    gen_a = MazeGenerator(10, 10, (0, 0), (9, 9), seed=1234)
    gen_b = MazeGenerator(10, 10, (0, 0), (9, 9), seed=1234)
    rows_a = list(gen_a.generate().to_rows())
    rows_b = list(gen_b.generate().to_rows())
    assert rows_a == rows_b


def test_perfect_maze_is_spanning_tree() -> None:
    """A perfect maze is connected, acyclic and has no 3x3 open area."""
    width, height = 8, 8
    gen = MazeGenerator(width, height, (0, 0), (7, 7), seed=7)
    maze = gen.generate()

    assert _open_internal_edges(maze) == width * height - 1
    assert len(_reachable(maze, (0, 0))) == width * height
    for y in range(height):
        for x in range(width):
            assert maze.walls(x, y) != ALL  # no isolated cell
    assert maze.has_any_3x3_open() is False


def test_perimeter_is_fully_closed() -> None:
    """Every border cell keeps its outward-facing wall closed."""
    width, height = 6, 9
    gen = MazeGenerator(width, height, (0, 0), (5, 8), seed=3)
    maze = gen.generate()

    for x in range(width):
        assert maze.has_wall(x, 0, 1)  # N
        assert maze.has_wall(x, height - 1, 4)  # S
    for y in range(height):
        assert maze.has_wall(0, y, 8)  # W
        assert maze.has_wall(width - 1, y, 2)  # E


def test_blocked_cell_isolated_rest_connected() -> None:
    """A blocked interior cell stays fully walled and non-traversable."""
    width, height = 5, 5
    blocked: Set[_Cell] = {(2, 2)}
    gen = MazeGenerator(
        width, height, (0, 0), (4, 4), seed=11, blocked=blocked
    )
    maze = gen.generate()

    assert maze.walls(2, 2) == ALL
    reachable = _reachable(maze, (0, 0))
    assert (2, 2) not in reachable
    assert len(reachable) == width * height - len(blocked)


def test_blocked_splitting_region_raises() -> None:
    """Blocked cells sealing off a cell raise DisconnectedMazeError."""
    # Wall (0, 0) in completely: its only neighbours are blocked.
    blocked: Set[_Cell] = {(1, 0), (0, 1)}
    gen = MazeGenerator(
        3, 3, (2, 2), (1, 1), seed=5, blocked=blocked
    )
    with pytest.raises(DisconnectedMazeError):
        gen.generate()


def test_braided_maze_adds_loops_without_3x3() -> None:
    """Braiding adds passages but never a 3x3 open area."""
    width, height = 6, 6
    gen = MazeGenerator(
        width, height, (0, 0), (5, 5),
        seed=1234, perfect=False, braid=0.5,
    )
    maze = gen.generate()

    assert maze.has_any_3x3_open() is False
    assert _open_internal_edges(maze) > width * height - 1


def test_get_structure_generates_lazily() -> None:
    """get_structure builds the maze on first access and caches it."""
    gen = MazeGenerator(4, 4, (0, 0), (3, 3), seed=2)
    maze = gen.get_structure()
    assert maze is gen.get_structure()


def test_entry_out_of_bounds_raises() -> None:
    """An out-of-bounds entry is rejected."""
    with pytest.raises(ValueError):
        MazeGenerator(5, 5, (5, 0), (4, 4))


def test_entry_equals_exit_raises() -> None:
    """Equal entry and exit are rejected."""
    with pytest.raises(ValueError):
        MazeGenerator(5, 5, (2, 2), (2, 2))


def test_entry_in_blocked_raises() -> None:
    """An entry that is also blocked is rejected."""
    with pytest.raises(ValueError):
        MazeGenerator(5, 5, (1, 1), (4, 4), blocked={(1, 1)})


def test_invalid_dimensions_raise() -> None:
    """Non-positive dimensions are rejected."""
    with pytest.raises(ValueError):
        MazeGenerator(0, 5, (0, 0), (0, 1))
