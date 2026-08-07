"""Block-style terminal renderer for a :class:`mazegen.grid.Maze`.

Rendering is two pure steps: :func:`build_grid` turns a maze into a
``(2*H+1) x (2*W+1)`` grid of kind codes (odd indices are cell
interiors, even indices the walls between them), and :func:`to_string`
paints that grid with ANSI colours or plain ASCII.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from mazegen.grid import ALL, DELTA, E, LETTER, Maze, S

# --- Cell kinds on the render grid --------------------------------------
WALL = 0
OPEN = 1
ENTRY = 2
EXIT = 3
PATH = 4
PATTERN = 5

#: Fixed background colour per marker (ANSI SGR codes).
_MARKER_BG: Dict[int, str] = {
    ENTRY: "45",     # magenta
    EXIT: "41",      # red
    PATH: "46",      # cyan
    PATTERN: "100",  # grey -> the hidden "42"
}

#: Background colours the "Rotate maze colors" action cycles through.
#: Every marker hue above is excluded, along with its bright variant, so
#: a wall can never take a marker's colour or a shade close to it. Black
#: (40) is left out as it would vanish on a dark terminal.
WALL_PALETTE: List[str] = [
    "47",   # white
    "43",   # yellow
    "42",   # green
    "44",   # blue
    "107",  # bright white
    "103",  # bright yellow
    "102",  # bright green
    "104",  # bright blue
]

#: Colour-mode block sizes in terminal characters. A character is about
#: twice as tall as it is wide, so a 2-column wall looks as thick as a
#: 1-row wall and both stay thinner than a cell.
_CELL_W = 4
_CELL_H = 2
_WALL_W = 2
_WALL_H = 1

#: Plain characters used when colour output is unavailable.
_KIND_CHAR: Dict[int, str] = {
    WALL: "#",
    OPEN: " ",
    ENTRY: "S",
    EXIT: "E",
    PATH: "*",
    PATTERN: "@",
}

#: Reverse of :data:`mazegen.grid.LETTER`: move letter -> direction bit.
_LETTER_TO_DIR: Dict[str, int] = {
    letter: bit for bit, letter in LETTER.items()
}

_Cell = Optional[Tuple[int, int]]


def build_grid(
    maze: Maze,
    *,
    entry: _Cell = None,
    exit: _Cell = None,
    path: Optional[List[str]] = None,
    show_path: bool = True,
) -> List[List[int]]:
    """Return a ``(2*H+1) x (2*W+1)`` grid of cell kinds for ``maze``.

    Args:
        maze: The maze to draw.
        entry: Optional ``(x, y)`` start cell.
        exit: Optional ``(x, y)`` goal cell.
        path: Optional solution letters, walked from ``entry``.
        show_path: Whether to draw ``path``.

    Returns:
        Rows of kind codes; cell ``(x, y)`` sits at
        ``grid[2*y + 1][2*x + 1]``.
    """
    rows = 2 * maze.height + 1
    cols = 2 * maze.width + 1
    grid: List[List[int]] = [[WALL] * cols for _ in range(rows)]

    # Open each cell interior and the walls it was carved through.
    for y in range(maze.height):
        for x in range(maze.width):
            cy, cx = 2 * y + 1, 2 * x + 1
            grid[cy][cx] = OPEN
            if x + 1 < maze.width and maze.is_open(x, y, E):
                grid[cy][cx + 1] = OPEN
            if y + 1 < maze.height and maze.is_open(x, y, S):
                grid[cy + 1][cx] = OPEN

    _open_junctions(grid, rows, cols)
    _fill_pattern(maze, grid)

    if show_path and path and entry is not None:
        cells = [entry, *_walk(maze, entry, path)]
        for (px, py), (cx, cy) in zip(cells, cells[1:]):
            grid[py + cy + 1][px + cx + 1] = PATH   # passage between
            grid[2 * cy + 1][2 * cx + 1] = PATH     # the cell reached

    if entry is not None:
        grid[2 * entry[1] + 1][2 * entry[0] + 1] = ENTRY
    if exit is not None:
        grid[2 * exit[1] + 1][2 * exit[0] + 1] = EXIT
    return grid


def _open_junctions(grid: List[List[int]], rows: int, cols: int) -> None:
    """Open wall corners sitting in the middle of a 2x2 open area.

    Args:
        grid: The kind grid to edit in place.
        rows: Number of grid rows.
        cols: Number of grid columns.
    """
    for jy in range(2, rows - 1, 2):
        for jx in range(2, cols - 1, 2):
            if (grid[jy - 1][jx] == OPEN and grid[jy + 1][jx] == OPEN
                    and grid[jy][jx - 1] == OPEN
                    and grid[jy][jx + 1] == OPEN):
                grid[jy][jx] = OPEN


def _fill_pattern(maze: Maze, grid: List[List[int]]) -> None:
    """Paint fully-walled cells (the "42") as solid shapes.

    Args:
        maze: The maze whose blocked cells are found.
        grid: The kind grid to edit in place.
    """
    blocked = {
        (x, y)
        for y in range(maze.height)
        for x in range(maze.width)
        if maze.walls(x, y) == ALL
    }
    for x, y in blocked:
        cy, cx = 2 * y + 1, 2 * x + 1
        grid[cy][cx] = PATTERN
        if (x + 1, y) in blocked:
            grid[cy][cx + 1] = PATTERN
        if (x, y + 1) in blocked:
            grid[cy + 1][cx] = PATTERN
        if (x + 1, y) in blocked and (x, y + 1) in blocked \
                and (x + 1, y + 1) in blocked:
            grid[cy + 1][cx + 1] = PATTERN


def _walk(
    maze: Maze, entry: Tuple[int, int], path: List[str]
) -> List[Tuple[int, int]]:
    """Return the cells visited by walking ``path`` from ``entry``.

    Args:
        maze: The maze being walked.
        entry: The ``(x, y)`` start cell.
        path: Move letters to follow.

    Returns:
        The cells reached, stopping at the first invalid move.
    """
    x, y = entry
    cells: List[Tuple[int, int]] = []
    for move in path:
        direction = _LETTER_TO_DIR.get(move)
        if direction is None:
            break
        dx, dy = DELTA[direction]
        x, y = x + dx, y + dy
        if not maze.in_bounds(x, y):
            break
        cells.append((x, y))
    return cells


def to_string(
    grid: List[List[int]], *, wall_color: int = 0, color: bool = True
) -> str:
    """Paint a kind grid into a printable string.

    Args:
        grid: The kind grid from :func:`build_grid`.
        wall_color: Index into :data:`WALL_PALETTE`; increment to cycle.
        color: Whether to emit ANSI colour blocks instead of ASCII.

    Returns:
        The rendered maze, rows joined by newlines.
    """
    wall_bg = WALL_PALETTE[wall_color % len(WALL_PALETTE)]
    lines: List[str] = []
    for r, row in enumerate(grid):
        if not color:
            lines.append("".join(_KIND_CHAR[kind] for kind in row))
            continue
        line = "".join(
            _block(kind, _CELL_W if c % 2 else _WALL_W, wall_bg)
            for c, kind in enumerate(row)
        )
        lines += [line] * (_CELL_H if r % 2 else _WALL_H)
    return "\n".join(lines)


def _block(kind: int, width: int, wall_bg: str) -> str:
    """Return one coloured block for ``kind``.

    Args:
        kind: The cell kind to paint.
        width: Block width in terminal columns.
        wall_bg: ANSI background code for walls.

    Returns:
        The escape-wrapped block, or plain spaces when open.
    """
    if kind == OPEN:
        return " " * width
    bg = wall_bg if kind == WALL else _MARKER_BG[kind]
    return "\x1b[" + bg + "m" + " " * width + "\x1b[0m"
