"""Tests for :mod:`amaze.render_terminal` (block-style rendering)."""

from mazegen.grid import E, Maze

from amaze.render_terminal import (
    ENTRY,
    EXIT,
    OPEN,
    PATH,
    PATTERN,
    WALL,
    build_grid,
    to_string,
)


def _corridor(width: int) -> Maze:
    """Return a 1-tall maze carved into a single open corridor."""
    maze = Maze(width, 1)
    for x in range(width - 1):
        maze.carve(x, 0, E)
    return maze


def test_grid_dimensions() -> None:
    """The kind grid is ``2*H+1`` rows by ``2*W+1`` columns."""
    maze = Maze(3, 2)
    grid = build_grid(maze)
    assert len(grid) == 2 * maze.height + 1
    assert all(len(row) == 2 * maze.width + 1 for row in grid)


def test_border_is_walled() -> None:
    """Every cell on the grid border is a closed wall."""
    grid = build_grid(_corridor(3))
    assert all(kind == WALL for kind in grid[0])
    assert all(kind == WALL for kind in grid[-1])
    assert all(row[0] == WALL and row[-1] == WALL for row in grid)


def test_carved_passage_is_open() -> None:
    """A carved east wall shows as an open cell between two interiors."""
    grid = build_grid(_corridor(3))
    assert grid[1][1] == OPEN      # cell (0, 0) interior
    assert grid[1][2] == OPEN      # wall carved to (1, 0)
    assert grid[1][3] == OPEN      # cell (1, 0) interior


def test_entry_and_exit_markers() -> None:
    """Entry and exit occupy their cell interiors with their own kinds."""
    grid = build_grid(_corridor(3), entry=(0, 0), exit=(2, 0))
    assert grid[1][1] == ENTRY
    assert grid[1][5] == EXIT


def test_path_respects_show_path() -> None:
    """Intermediate path cells are marked only when ``show_path``."""
    shown = build_grid(
        _corridor(3), entry=(0, 0), exit=(2, 0),
        path=["E", "E"], show_path=True,
    )
    assert shown[1][3] == PATH      # intermediate cell (1, 0)
    assert shown[1][1] == ENTRY     # endpoints keep their markers
    assert shown[1][5] == EXIT
    hidden = build_grid(
        _corridor(3), entry=(0, 0), exit=(2, 0),
        path=["E", "E"], show_path=False,
    )
    assert all(PATH not in row for row in hidden)


def test_blocked_cell_is_pattern() -> None:
    """A fully-walled cell renders as the '42' pattern kind."""
    maze = Maze(1, 1)              # the single cell keeps all four walls
    grid = build_grid(maze)
    assert grid[1][1] == PATTERN


def test_to_string_plain_uses_ascii() -> None:
    """Colour-free output uses plain characters and no escape codes."""
    out = to_string(build_grid(_corridor(3), entry=(0, 0)), color=False)
    assert "#" in out and "S" in out
    assert "\x1b" not in out
    lines = out.split("\n")
    assert all(len(line) == 2 * 3 + 1 for line in lines)


def test_to_string_colour_has_escape_codes() -> None:
    """Coloured output emits ANSI blocks that are two columns wide."""
    out = to_string(build_grid(_corridor(3)), color=True)
    assert "\x1b[" in out
    assert "\x1b[0m" in out
