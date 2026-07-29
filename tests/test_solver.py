"""Tests for :mod:`mazegen.solver` (BFS shortest-path solving)."""

import pytest

from mazegen.grid import DELTA, E, Maze, N, S, W
from mazegen.solver import path_cells, solve


def test_unique_path_letters_and_cells() -> None:
    """A single carved corridor yields its exact letters and cells."""
    maze = Maze(3, 3)
    maze.carve(0, 0, E)
    maze.carve(1, 0, E)
    maze.carve(2, 0, S)
    maze.carve(2, 1, S)
    entry = (0, 0)
    exit = (2, 2)
    assert solve(maze, entry, exit) == ["E", "E", "S", "S"]
    assert path_cells(maze, entry, exit) == [
        (0, 0), (1, 0), (2, 0), (2, 1), (2, 2),
    ]


def test_two_routes_returns_shorter() -> None:
    """When two routes exist BFS returns the shorter one."""
    maze = Maze(3, 3)
    # Short route: (0,0) -> (0,1) -> (0,2).
    maze.carve(0, 0, S)
    maze.carve(0, 1, S)
    # Long detour: (0,0)->(1,0)->(1,1)->(1,2)->(0,2).
    maze.carve(0, 0, E)
    maze.carve(1, 0, S)
    maze.carve(1, 1, S)
    maze.carve(1, 2, W)
    moves = solve(maze, (0, 0), (0, 2))
    assert moves == ["S", "S"]
    assert len(moves) == 2


def test_unreachable_raises_value_error() -> None:
    """A fully closed grid has no route to a distinct exit."""
    maze = Maze(2, 2)
    with pytest.raises(ValueError):
        solve(maze, (0, 0), (1, 1))
    with pytest.raises(ValueError):
        path_cells(maze, (0, 0), (1, 1))


def test_out_of_bounds_raises_value_error() -> None:
    """Out-of-bounds entry or exit is rejected."""
    maze = Maze(2, 2)
    with pytest.raises(ValueError):
        solve(maze, (-1, 0), (1, 1))
    with pytest.raises(ValueError):
        path_cells(maze, (0, 0), (2, 2))


def test_entry_equals_exit() -> None:
    """No moves and a single-cell path when entry == exit."""
    maze = Maze(3, 3)
    assert solve(maze, (1, 1), (1, 1)) == []
    assert path_cells(maze, (1, 1), (1, 1)) == [(1, 1)]


def test_walk_follows_moves_to_exit() -> None:
    """Applying each move via DELTA lands exactly on the exit."""
    maze = Maze(3, 3)
    maze.carve(0, 0, E)
    maze.carve(1, 0, E)
    maze.carve(2, 0, S)
    maze.carve(2, 1, S)
    entry = (0, 0)
    exit = (2, 2)
    letter_delta = {
        "N": DELTA[N],
        "E": DELTA[E],
        "S": DELTA[S],
        "W": DELTA[W],
    }
    x, y = entry
    for move in solve(maze, entry, exit):
        dx, dy = letter_delta[move]
        x, y = x + dx, y + dy
    assert (x, y) == exit
