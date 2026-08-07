"""mazegen -- a small, dependency-free maze generation library.

Example::

    from mazegen import MazeGenerator, blocked_cells

    gen = MazeGenerator(20, 15, (0, 0), (19, 14),
                        seed=42, perfect=True,
                        blocked=blocked_cells(20, 15))
    maze = gen.generate()    # -> mazegen.grid.Maze
    moves = gen.solution()   # -> ['E', 'S', ...]

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
