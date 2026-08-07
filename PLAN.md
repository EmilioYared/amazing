# A-Maze-ing — Implementation Plan

_Working plan for the 42 "A-Maze-ing" maze generator. Project root = this `amazing/` folder._

## Context

The subject (`en.subject (28).pdf`, v2.1) asks for a Python maze generator that:

- Reads a `KEY=VALUE` **config file**, generates a maze (optionally **perfect** = exactly one path entry→exit), and writes it to an output file using a **hex wall encoding**.
- Hides a visible **"42"** made of fully-closed cells.
- Renders the maze in the **terminal (ASCII)** with **interactions** (regenerate, show/hide path, change wall colours).
- Ships the generator as a **reusable, pip-installable `mazegen` package** (single built wheel committed at repo root).
- Meets 42 quality gates: Python 3.10+, **flake8**, **mypy** (fully typed), PEP 257 docstrings, graceful error handling, a **Makefile**, tests, README.

**Confirmed decisions:** Terminal ASCII renderer · mandatory scope first (bonuses later) · README credit line uses `<login1>` placeholder (likely `eyared`).

**Environment:** Windows, Python 3.11.5, no `make` locally (Makefile authored for the Linux grader; verify by running the underlying commands). Installed: matplotlib, numpy, flake8, mypy, setuptools. The `install` target adds `build`, `wheel`, `pytest`.

## Wall / output encoding (locked)

Per-cell 4-bit mask, **closed = 1**: `N=1`, `E=2`, `S=4`, `W=8`. `value = (N?1)|(E?2)|(S?4)|(W?8)` → one hex digit `0`–`F`. Blocked "42" cell = `F`.
- Verified vs. subject: `3=0011` → N,E closed / S,W open; `A=1010` → E,W closed. ✓
- **Coherence by construction:** grid starts all-`0xF`; `carve` clears the shared bit on **both** neighbours, so adjacent walls never disagree.
- **Perimeter fully enclosed, entry/exit included** — only ever carve *internal* edges (neighbour in-bounds); outer border walls stay closed for free. The solution is a purely internal BFS path from the entry cell to the exit cell.
- Output file: `H` rows (one line each, `W` hex digits, `y=0` top) → blank line → 3 lines: `entry x,y`, `exit x,y`, path as `NESW` letters. Every line ends with `\n`.

## Algorithm

**Iterative randomized backtracker (DFS, explicit stack).** A perfect maze is a spanning tree → no cycle → cannot contain even a 2×2 open block, so `PERFECT=True` and "no 3×3 open area" hold for free; corridors are 1-wide.
- `PERFECT=False`: **braid** — shuffle closed internal walls with the seeded RNG, open each only if `would_form_3x3_open` is false, up to a braid ratio. Braiding only adds passages → connectivity preserved, cycles introduced (multiple paths).
- **3×3 rule (locked):** forbidden = a 3×3 rectangle of cells where all 12 internal passages are open. 2×3 / 3×2 fully-open rectangles are allowed. Rectangle test only.
- Seed via `random.Random(seed)` for reproducibility.

## The "42" pattern

Blocked cells = `0xF`, excluded from the traversal graph (edges to them never carved → isolated + coherent automatically).
1. Compute `blocked` from the font; assert ENTRY/EXIT ∉ blocked.
2. Run backtracker over **non-blocked cells only**, start at ENTRY.
3. Verify `visited == all non-blocked`; else the glyph split the region → omit pattern, regenerate, print the mandated console error.

A spanning tree over the non-blocked component still has exactly one ENTRY→EXIT path; blocked cells are degree-0 → PERFECT uniqueness unchanged.

**Font — 3×5 bitmaps (`1`=blocked), glyph = `4` + 1-col gap + `2` = 7 wide × 5 tall:**
```
 "4"          "2"
1 0 1        1 1 1
1 0 1        0 0 1
1 1 1        1 1 1
0 0 1        1 0 0
0 0 1        1 1 1
```
**Minimum size:** glyph (7×5) + 1-cell margin all sides ⇒ **WIDTH ≥ 9, HEIGHT ≥ 7**; below that, omit + print error. Center the glyph; corners stay free so ENTRY(0,0)/EXIT(W−1,H−1) never collide.

## Reusable package (`mazegen`)

Pure-Python, **zero runtime deps** (bytearray grid). setuptools src-layout builds `mazegen-1.0.0-py3-none-any.whl`, committed at repo root; `dist/`, `build/`, `*.egg-info` git-ignored. Graders rebuild from source in a fresh venv (`pip install build && python -m build`). Module doc travels inside the wheel (`src/mazegen/README.md`), duplicated in the main README.

```toml
[build-system]
requires = ["setuptools>=65", "wheel"]
build-backend = "setuptools.build_meta"
[project]
name = "mazegen"
version = "1.0.0"
description = "Reusable maze generation library"
requires-python = ">=3.10"
readme = "src/mazegen/README.md"
dependencies = []
[tool.setuptools.packages.find]
where = ["src"]
```

## Layout

```
amazing/
├── a_maze_ing.py            # MANDATORY exact name — python3 a_maze_ing.py config.txt
├── Makefile  README.md  .gitignore  config.txt  pyproject.toml
├── mazegen-1.0.0-py3-none-any.whl        # built package at root
├── src/mazegen/  __init__.py  grid.py  generator.py  pattern42.py  solver.py  README.md
├── amaze/        __init__.py  config.py  output.py  render_terminal.py
└── tests/        test_grid.py test_config.py test_generator.py test_pattern42.py test_solver.py test_output.py
```

## Locked interfaces (foundation freezes these; parallel agents code against them)

```python
# mazegen/grid.py
N, E, S, W = 1, 2, 4, 8;  ALL = 15
OPPOSITE = {N: S, S: N, E: W, W: E}
DELTA    = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}   # (dx, dy)
LETTER   = {N: "N", E: "E", S: "S", W: "W"}
class Maze:
    width: int; height: int
    def __init__(self, width, height) -> None          # cells init 0xF
    def in_bounds(self, x, y) -> bool
    def walls(self, x, y) -> int
    def has_wall(self, x, y, direction) -> bool
    def is_open(self, x, y, direction) -> bool
    def close_all(self, x, y) -> None                   # 42 cells -> 0xF
    def carve(self, x, y, direction) -> None            # removes wall both sides
    def neighbors(self, x, y)                           # Iterator[(nx, ny, dir)]
    def would_form_3x3_open(self, x, y, direction) -> bool
    def has_any_3x3_open(self) -> bool

# mazegen/generator.py
class MazeGenerator:
    def __init__(self, width, height, entry, exit, *, seed=None,
                 perfect=True, braid=0.0, blocked=None) -> None
    def generate(self) -> Maze
    def get_structure(self) -> Maze
    def solution(self) -> list[str]                     # NESW moves

# mazegen/solver.py
def solve(maze, entry, exit) -> list[str]               # shortest, raises if unreachable
def path_cells(maze, entry, exit) -> list[tuple[int,int]]

# mazegen/pattern42.py
class PatternTooSmallError(Exception): ...
def min_dimensions() -> tuple[int,int]                  # (9, 7), fixed
def blocked_cells(width, height) -> set[tuple[int,int]]  # {} if too small

# amaze/config.py
@dataclass
class Config: width; height; entry; exit; output_file; perfect
              seed=None; algorithm="backtracker"; braid=0.0; pattern=True; display="terminal"
class ConfigError(Exception): ...
def load_config(path) -> Config

# amaze/output.py
def write_output(path, maze, entry, exit, path_moves) -> None

# amaze/render_terminal.py
def render(maze, *, entry=None, exit=None, path=None, show_path=True) -> str
```

## Execution phases

**Phase 0 — Foundation (main thread; blocks everyone):** scaffold tree, `.gitignore`, `pyproject.toml`, default `config.txt`, README skeleton, and fully implement `src/mazegen/grid.py` + freeze the interfaces above. Nothing parallel starts until signatures are frozen.

**Phase 1 — Parallel modules (independent agents, each = module + pytest; depend only on frozen `grid.py`/signatures):**

| Agent | Module | Notes |
|---|---|---|
| A | `mazegen/generator.py` | iterative backtracker + braid; `blocked` via DI |
| B | `mazegen/solver.py` | BFS → NESW |
| C | `mazegen/pattern42.py` | font, blocked set, min-size/omit |
| D | `amaze/config.py` | KEY=VALUE parse + validate |
| E | `amaze/output.py` | hex writer / file format |
| F | `amaze/render_terminal.py` | ASCII |

No edges among A–F (risky edges cut: 3×3 check in `grid`; `blocked` injected; output receives the path string; renderer receives path as data).

**Phase 2 — Integration (main thread):** `a_maze_ing.py` (args, error boundary) + `MazeGenerator` facade in `mazegen/__init__.py` (pattern42 → generator → solver, exposes structure + solution). Wire: parse → blocked → generate → solve → write output → render → interactive loop (regenerate / toggle path / change colours).

**Phase 3 — Finalize (partly parallel):** Makefile (`install run debug clean lint lint-strict package test`), build wheel to root, `flake8 .` + `mypy` clean, full `README.md` (algorithm choice/rationale, reusable-part doc, team/planning), module `README.md`, run `pytest`.

## Verification

- `python a_maze_ing.py config.txt` produces the output file; same seed → byte-identical (reproducibility).
- Output passes coherence check: shared walls agree, perimeter closed, no 3×3 open area, "42" present (or the "too small" message), and for `PERFECT=True` exactly one entry→exit path; the path string actually walks entry→exit.
- `flake8 .` + `mypy` clean; `pytest` green.
- Rebuild the wheel in a fresh venv, `pip install` it, run the documented `MazeGenerator` example.
