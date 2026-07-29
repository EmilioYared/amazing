# mazegen

A small, **dependency-free** Python library for generating mazes, used by
the 42 *A-Maze-ing* project. Ships as a single wheel and imports with zero
third-party requirements.

## Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

## Quick start

```python
from mazegen import MazeGenerator, blocked_cells

# Optional: reserve the hidden "42" pattern as fully-walled cells.
blocked = blocked_cells(20, 15)          # {} if the grid is too small

gen = MazeGenerator(
    width=20, height=15,
    entry=(0, 0), exit=(19, 14),
    seed=42,             # reproducible; omit / None for random
    perfect=True,        # exactly one entry->exit path
    braid=0.0,           # >0 with perfect=False adds loops
    blocked=blocked,     # optional set of walled-off cells
)

maze = gen.generate()    # -> mazegen.grid.Maze (the structure)
moves = gen.solution()   # -> ['E', 'S', 'S', ...]  (N/E/S/W letters)
```

## Custom parameters

| Parameter | Meaning |
|-----------|---------|
| `width`, `height` | maze dimensions in cells (>= 1) |
| `entry`, `exit` | `(x, y)` cells, in bounds, different, not blocked |
| `seed` | any int for reproducible generation (`None` = random) |
| `perfect` | `True` = single path (spanning tree); `False` = braided |
| `braid` | fraction `0..1` of extra walls to open when not perfect |
| `blocked` | `set[(x, y)]` of cells to wall off and never traverse |

## Accessing the structure and the solution

```python
maze = gen.get_structure()          # the Maze (generated lazily)
maze.width, maze.height             # dimensions
maze.walls(x, y)                    # 4-bit mask for a cell
maze.has_wall(x, y, direction)      # direction in {N, E, S, W}

from mazegen import solve, N, E, S, W
moves = solve(maze, (0, 0), (19, 14))   # shortest path, N/E/S/W letters
```

### Wall encoding

Each cell is a 4-bit mask; a **set** bit means the wall is **closed**:

| Bit | Value | Direction |
|-----|-------|-----------|
| 0 | 1 | North |
| 1 | 2 | East |
| 2 | 4 | South |
| 3 | 8 | West |

Adjacent cells always agree on their shared wall (coherence is enforced by
`Maze.carve`, which clears the bit on both sides at once).

## Public API

`MazeGenerator`, `Maze`, `solve`, `path_cells`, `blocked_cells`,
`min_dimensions`, `fits`, the direction constants `N, E, S, W, ALL`, and
`DisconnectedMazeError` / `PatternTooSmallError`.
