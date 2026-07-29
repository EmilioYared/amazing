"""mazegen — a small, dependency-free maze generation library.

Public API::

    from mazegen import MazeGenerator, solve, blocked_cells

    blocked = blocked_cells(20, 15)          # optional hidden "42"
    gen = MazeGenerator(20, 15, (0, 0), (19, 14),
                        seed=42, perfect=True, blocked=blocked)
    maze = gen.generate()                    # -> mazegen.grid.Maze
    moves = gen.solution()                   # -> ['E', 'S', ...] (N/E/S/W)

See ``README.md`` for the full guide.
"""

from mazegen.generator import DisconnectedMazeError, MazeGenerator
from mazegen.grid import (
    ALL,
    DELTA,
    E,
    LETTER,
    N,
    OPPOSITE,
    S,
    W,
    Maze,
)
from mazegen.pattern42 import (
    PatternTooSmallError,
    blocked_cells,
    fits,
    min_dimensions,
)
from mazegen.solver import path_cells, solve

__version__ = "1.0.0"

__all__ = [
    "MazeGenerator",
    "DisconnectedMazeError",
    "Maze",
    "solve",
    "path_cells",
    "blocked_cells",
    "min_dimensions",
    "fits",
    "PatternTooSmallError",
    "N",
    "E",
    "S",
    "W",
    "ALL",
    "OPPOSITE",
    "DELTA",
    "LETTER",
    "__version__",
]
