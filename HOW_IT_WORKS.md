# How A-Maze-ing Works — a detailed walkthrough

This document explains, in depth, how the whole program is built and how a
single run flows from a config file to a rendered maze. It is meant as a
study/defense aid: after reading it you should be able to point at any line
and say *why* it exists.

---

## Table of contents

1. [Bird's-eye view](#1-birds-eye-view)
2. [Project layout — two layers](#2-project-layout--two-layers)
3. [The wall model — `mazegen/grid.py`](#3-the-wall-model--mazegengridpy)
4. [Generation — `mazegen/generator.py`](#4-generation--mazegengeneratorpy)
5. [The hidden "42" — `mazegen/pattern42.py`](#5-the-hidden-42--mazegenpattern42py)
6. [Solving — `mazegen/solver.py`](#6-solving--mazegensolverpy)
7. [Configuration — `amaze/config.py`](#7-configuration--amazeconfigpy)
8. [The output file — `amaze/output.py`](#8-the-output-file--amazeoutputpy)
9. [Terminal rendering — `amaze/render_terminal.py`](#9-terminal-rendering--amazerender_terminalpy)
10. [The CLI & interactive loop — `a_maze_ing.py`](#10-the-cli--interactive-loop--a_maze_ingpy)
11. [End-to-end walkthrough](#11-end-to-end-walkthrough)
12. [Requirement traceability](#12-requirement-traceability)
13. [Running, building, testing](#13-running-building-testing)

---

## 1. Bird's-eye view

The program is one pipeline:

```
config.txt
   │  parse + validate            (amaze/config.py)
   ▼
Config ────────────────────────────────────────────────┐
   │  compute the "42" cells       (mazegen/pattern42)  │
   ▼                                                     │
blocked set ─┐                                           │
   │  randomized backtracker (+ optional braiding)       │
   ▼          (mazegen/generator.py + grid.py)           │
Maze  ───────┬──────────────────────────────────────────┘
   │         │  BFS shortest path  (mazegen/solver.py)
   │         ▼
   │      moves = ['E','S',...]
   │         │
   ├─────────┴──► write output file (amaze/output.py)   → maze.txt
   │
   └───────────► render blocks + interactive menu       → your terminal
                 (amaze/render_terminal.py + a_maze_ing.py)
```

Everything is deterministic given a **seed**: the same config + seed always
produces the same maze, the same output file, and the same solution.

---

## 2. Project layout — two layers

The code is split into a **reusable library** and a **non-reusable app**,
because the subject requires the generation logic to ship as a
`pip`-installable module (`mazegen-*.whl`) that a *future* project can
import.

```
amazing/
├── a_maze_ing.py          # CLI entry point (the only file you run)
├── config.txt             # default configuration
│
├── src/mazegen/           # ← REUSABLE LIBRARY (zero third-party deps)
│   ├── grid.py            #   Maze data model + wall geometry
│   ├── generator.py       #   MazeGenerator (backtracker + braiding)
│   ├── pattern42.py        #   the hidden "42" glyph placement
│   ├── solver.py          #   BFS shortest-path solver
│   ├── __init__.py        #   the public API surface
│   └── README.md          #   library docs (shipped inside the wheel)
│
├── amaze/                 # ← APP LAYER (glue, not reusable)
│   ├── config.py          #   parse & validate config.txt
│   ├── output.py          #   serialize the maze to the hex file format
│   └── render_terminal.py  #   draw the maze as coloured blocks
│
├── tests/                 # pytest suite (65 tests)
├── pyproject.toml         # build metadata for the mazegen wheel
└── Makefile  .flake8      # automation + lint config
```

**Why the split?** `mazegen` knows nothing about config files, terminals,
or the CLI — it only knows mazes. That keeps it small, dependency-free, and
importable anywhere:

```python
from mazegen import MazeGenerator, blocked_cells, solve
```

The `amaze` package and `a_maze_ing.py` are the *application* that wires the
library to this specific project (files, colours, menu). They are
deliberately **not** part of the wheel.

> **Import trick:** because `mazegen` lives under `src/`, running
> `python a_maze_ing.py` without installing anything would normally fail to
> import it. The CLI's first job is to prepend `src/` to `sys.path` so the
> library is importable both when installed *and* when run straight from the
> repo.

---

## 3. The wall model — `mazegen/grid.py`

This is the foundation every other module builds on.

### 3.1 Wall encoding

Each cell stores which of its four walls are **closed** as a 4-bit mask:

| Bit | Value | Direction | Constant |
|-----|-------|-----------|----------|
| 0   | 1     | North     | `N`      |
| 1   | 2     | East      | `E`      |
| 2   | 4     | South     | `S`      |
| 3   | 8     | West      | `W`      |

- A **set** bit = wall **closed**. A **cleared** bit = wall **open**.
- `ALL = N|E|S|W = 15` means a fully-walled (isolated) cell.
- Example: `0b0011 = 3` → North+East closed, South+West open.

Helper dictionaries make the geometry readable:

- `OPPOSITE = {N:S, S:N, E:W, W:E}` — the shared edge seen from the other
  cell.
- `DELTA = {N:(0,-1), S:(0,1), E:(1,0), W:(-1,0)}` — grid step per
  direction. **`y` grows downward** (row 0 is the top).
- `LETTER = {N:'N', E:'E', S:'S', W:'W'}` — how a move is written in the
  output file and the solution.

### 3.2 The `Maze` container

```python
self._cells: bytearray = bytearray([ALL]) * (width * height)
```

- One **byte per cell**, laid out row-major (`index = y*width + x`), so a
  50×60 maze is 3000 bytes — tiny and cache-friendly.
- Every cell starts **fully walled**; the generator *opens* passages.
- `__slots__` keeps the object lean.

Query methods: `walls(x,y)` (the mask), `has_wall(x,y,dir)`,
`is_open(x,y,dir)`, `in_bounds(x,y)`.

### 3.3 Carving — coherence by construction

```python
def carve(self, x, y, direction):
    nx, ny = x + dx, y + dy               # the neighbour
    self._cells[idx(x, y)]  &= ~direction        # open my side
    self._cells[idx(nx, ny)] &= ~OPPOSITE[dir]   # open their side
```

The single most important invariant in the whole project:
**a wall is always opened on *both* cells at once.** This makes it
*impossible* to end up with cell A saying "east is open" while cell B (to
its east) says "west is closed". The subject explicitly forbids that
incoherence, and `carve` rules it out structurally rather than by later
checking. Carving toward an out-of-bounds neighbour (the outer border) is
refused, so **the border stays closed** automatically.

### 3.4 The "no 3×3 open area" rule

The subject forbids open areas wider than 2 cells (a 2×3 or 3×2 open block
is fine; a **3×3** is not). A *perfect* maze can never contain one (see
§4.2), so this machinery only matters for **braiding**, which removes walls
and could otherwise open a large room.

- A "3×3 open area" = a 3×3 block of cells whose **12 internal passages**
  (6 horizontal + 6 vertical) are all open.
- `would_form_3x3_open(x, y, dir)` answers *"if I opened this one wall,
  would it complete a forbidden 3×3?"* in **constant time**, by inspecting
  only the few 3×3 windows that actually contain that edge (via
  `_canonical_edge`, which maps any wall to a single top/left owner so each
  physical edge has one representation).
- `has_any_3x3_open()` is the full scan, used by tests/validation.

### 3.5 Serialization helper

`to_rows()` yields one hex string per row (`"%X"` per cell). This is exactly
the first block of the output file — the renderer and the file writer both
lean on the same source of truth.

---

## 4. Generation — `mazegen/generator.py`

### 4.1 The algorithm: iterative randomized backtracker

Also known as *randomized depth-first search*. In plain words: wander
randomly, carving as you go; when you hit a dead end, back up to the last
cell that still has an unvisited neighbour, and keep going.

```
visited = {entry};  stack = [entry]
while stack:
    x, y = stack[-1]                          # look at the top of the stack
    candidates = unvisited, non-blocked neighbours of (x, y)
    if candidates:
        pick one at random
        carve the wall to it                  # <- opens a passage
        mark it visited; push it
    else:
        stack.pop()                           # dead end: backtrack
```

It uses an **explicit stack, never recursion**, so a huge maze can't blow
Python's recursion limit. Randomness comes from `random.Random(seed)` — a
private RNG instance, so results are **reproducible** and don't disturb
global random state.

### 4.2 Why a backtracker? (the key insight)

A **perfect maze is exactly a spanning tree** of the grid: every cell
connected, exactly one path between any two cells, no loops. The backtracker
builds one directly, which buys three subject requirements *for free*:

- **Full connectivity** — every reachable cell is visited and carved into.
- **Exactly one path** (`PERFECT=True`) — a tree has no cycles.
- **No large open areas** — a tree can't even contain a 2×2 loop, so
  corridors are 1 cell wide; the 3×3 rule is satisfied with zero effort.

### 4.3 Blocked cells (the "42")

Before wandering, the generator marks the "42" cells fully closed and never
lets the walk step into them:

```python
candidates = [n for n in neighbours(x, y)
              if n not in blocked and n not in visited]
```

So the "42" cells become solid islands that don't participate in the maze.

### 4.4 The connectivity check

After the walk, it verifies every **non-blocked** cell was visited:

```python
if len(visited) != width*height - len(blocked):
    raise DisconnectedMazeError(...)
```

This fires when the "42" pattern happens to wall off part of the grid so it
can't be reached. The CLI catches it and simply **regenerates without the
pattern** (see §10.3), matching the subject's "omit the 42 if it doesn't
fit" rule.

### 4.5 Braiding (non-perfect mazes)

When `PERFECT=False` **and** `BRAID > 0`, a second pass adds loops:

1. Collect every closed **internal** wall (only `E`/`S` per cell, to avoid
   listing each edge twice; skip walls touching a blocked cell).
2. Shuffle them (seeded) and try to open `floor(braid × count)` of them.
3. Before each removal, `would_form_3x3_open` vetoes any wall that would
   create a forbidden 3×3 room.

The result is a maze with some loops (multiple paths) but **still no large
open areas**. With the shipped default (`BRAID` unset → `0.0`) no braiding
happens, so the default maze is perfect even though `PERFECT=False`.

### 4.6 Public methods

- `generate()` → build & return the `Maze`.
- `get_structure()` → the `Maze`, generating lazily on first access.
- `solution()` → the shortest path as letters (imports `solve` lazily to
  avoid a circular import).

---

## 5. The hidden "42" — `mazegen/pattern42.py`

### 5.1 A tiny pixel font

Each digit is a 3×5 grid of pixels (`1` = a cell to wall off):

```
   "4"            "2"
 1 0 1          1 1 1
 1 0 1          0 0 1
 1 1 1          1 1 1
 0 0 1          1 0 0
 0 0 1          1 1 1
```

`GLYPH` glues them with a **blank spacer column** between → a **7×5** shape
(`"4" + gap + "2"`).

### 5.2 Placement

- `min_dimensions()` → the smallest grid that fits the glyph **plus a
  one-cell margin on every side** = `(7 + 2, 5 + 2)` = **9×7**, a constant.
- `fits(w, h)` → does the grid clear that minimum?
- `blocked_cells(w, h)` → the set of `(x, y)` cells to close. The glyph is
  **centred**, and each font pixel becomes **exactly one cell**. If the grid
  is too small, it returns an **empty set** (not an error) so the caller can
  print the mandated "too small" message and carry on.

The glyph is **never scaled to the maze**: a 200×200 maze hides the same
7×5 "42" as a 9×7 one, just with more margin around it.

The one-cell margin guarantees the pattern never touches the border and
keeps the default corner entry/exit clear.

### 5.3 Why fully-closed cells?

Fully-walled cells are unreachable, so they don't affect connectivity or the
unique-path property, and in the render they show up as a solid block —
which is precisely how the "42" becomes *visible*.

---

## 6. Solving — `mazegen/solver.py`

A plain **breadth-first search** over the open-passage graph. BFS explores
in rings of increasing distance, so the first time it reaches the exit it has
found a **shortest** route.

```
parents = {entry: (entry, None)}
queue = [entry]
while queue:
    x, y = queue.popleft()
    for each neighbour reachable through an OPEN wall:
        record parents[neighbour] = ((x,y), direction moved)
        if neighbour == exit: reconstruct and stop
        queue.append(neighbour)
```

`_reconstruct` walks the `parents` chain back from the exit to the entry and
reverses it. Two public views share this one search:

- `solve(maze, entry, exit)` → the path as **letters** `['E','S','S',…]`
  (what goes into the output file and drives the on-screen path).
- `path_cells(maze, entry, exit)` → the same path as **`(x, y)` cells**.

Out-of-bounds endpoints or an unreachable exit raise `ValueError`.

---

## 7. Configuration — `amaze/config.py`

### 7.1 Format

One `KEY=VALUE` per line; blank lines and `#` comments are ignored; unknown
keys are ignored; keys are upper-cased. Everything is read through a context
manager (`with open(...)`), and a missing file becomes a friendly
`ConfigError`, never a traceback.

### 7.2 Keys

**Mandatory:** `WIDTH`, `HEIGHT`, `ENTRY`, `EXIT`, `OUTPUT_FILE`, `PERFECT`.

**Optional:** `SEED` (int, reproducibility), `ALGORITHM` (`backtracker`),
`BRAID` (0.0–1.0), `PATTERN` (draw the "42"?), `DISPLAY` (`terminal`).

### 7.3 Validation

Each value is parsed by a small typed helper (`_parse_positive_int`,
`_parse_point`, `_parse_bool`, `_parse_seed`, `_parse_braid`) that raises a
clear `ConfigError` on bad input. After parsing, the loader checks that
entry and exit are **in bounds** and **different**. The result is a frozen
`@dataclass Config` — one tidy object passed around the app.

---

## 8. The output file — `amaze/output.py`

The exact on-disk format required by the subject:

```
<hex row 0>          ← one hex digit per cell, top row first
<hex row 1>
...
<hex row H-1>
                     ← one blank line
<entry_x>,<entry_y>
<exit_x>,<exit_y>
<path letters>       ← e.g. EESSWSE...  (empty if entry == exit)
```

- `format_output` builds the string; `write_output` writes it.
- The file is opened with `newline="\n"` and `encoding="ascii"`, so the
  bytes are **identical on every OS** (no Windows `\r\n` surprises) — this
  matters because an automated grader may byte-compare it.
- Every line, including the blank one and the final path line, ends in a
  single `\n`.

---

## 9. Terminal rendering — `amaze/render_terminal.py`

The renderer matches the reference screenshots in the PDF: the maze is a
grid of **solid coloured blocks**, not thin lines. It is split into two
small, pure functions so it is easy to test and reason about.

### 9.1 `build_grid` → a grid of "kinds"

A `W×H` maze becomes a **`(2H+1) × (2W+1)`** grid of integer *kind* codes:

```
 odd row / odd col  → a cell interior
 odd row / even col → the vertical wall between two side-by-side cells
 even row / odd col → the horizontal wall between two stacked cells
 even row / even col→ a wall corner / junction
```

Kinds: `WALL`, `OPEN`, `ENTRY`, `EXIT`, `PATH`, `PATTERN`. Construction:

1. Start with **everything `WALL`** (matches "all walls closed").
2. For each cell, set its interior `OPEN`, and set the east/south wall
   `OPEN` wherever the maze carved a passage.
3. `_open_junctions` — open a corner that sits in the middle of a legal
   2×2 open space, so a lone wall pixel doesn't float inside a wide
   corridor.
4. `_fill_pattern` — paint fully-walled cells (the "42") and the walls
   *between* adjacent blocked cells as `PATTERN`, so the digits read as one
   solid shape instead of scattered dots.
5. `_walk` the solution letters from the entry and mark the cells it
   crosses **and the passage segment between each pair** as `PATH` (only
   when `show_path`). Colouring the connectors — not just the cell centres
   — is what makes the path a single continuous ribbon instead of a dashed
   line of coloured cells separated by black gaps.
6. Finally stamp `ENTRY` and `EXIT` on their cells (so they always win over
   a `PATH` mark at the endpoints).

`build_grid` is **pure** — same inputs always give the same grid — which is
why it is straightforward to unit-test.

### 9.2 `to_string` → the printable string

Turns the kind grid into text. The key idea is that **walls are thin and
cells are big**, matching the PDF's first screenshot:

- **On a terminal** (`color=True`): every position is painted with ANSI
  background colour, but the size depends on whether it is a cell or a wall.
  A **cell** is `_CELL_W`×`_CELL_H` (`4`×`2`); a **wall/corner** is
  `_WALL_W`×`_WALL_H` (`2`×`1`). The odd sizes matter because a terminal
  character is about **twice as tall as it is wide**: a wall that is 2
  columns wide looks as thick as a wall that is 1 row tall, so **vertical and
  horizontal walls have the same apparent thickness**, and both stay thinner
  than a cell. Because odd grid indices are cells and even indices are walls,
  `to_string` just picks each block's width from its column index and repeats
  the line for the taller cell rows. (`_block` renders one coloured rectangle
  of the requested width.)
- **Otherwise** (pipes, tests): one **plain ASCII** char per grid cell —
  `#` wall, space open, `S` entry, `E` exit, `*` path, `@` "42" — so output
  stays compact, readable and diff-able with no escape codes.

Colour scheme:

| Kind      | Colour            | ANSI bg |
|-----------|-------------------|---------|
| wall      | cyclable palette  | `47/43/42/46/44/45/41` |
| entry     | magenta           | `45`    |
| exit      | red               | `41`    |
| path      | cyan              | `46`    |
| "42"      | grey              | `100`   |

The `wall_color` index is what the menu's **"Rotate maze colors"** advances;
`to_string` just takes it modulo the palette length.

---

## 10. The CLI & interactive loop — `a_maze_ing.py`

### 10.1 `main(argv)` — the happy path

```
1. check argv is exactly [prog, config_path]      else usage error → exit 1
2. load_config(path)                               ConfigError → exit 1
3. maze, moves = _build_maze(cfg, cfg.seed)        gen/solve errors → exit 1
4. write_output(cfg.output_file, ...)              OSError → exit 1
5. print "maze written to <file>"
6. enable ANSI on Windows; run the interactive loop
```

Every failure mode prints a clear message to `stderr` and returns a non-zero
exit code — the program **never crashes with a traceback**, as required.

### 10.2 `_build_maze` — generate + solve in one place

Wraps the three steps every generation needs — compute the "42" cells, run
the generator (with fallbacks), and solve — so both the initial run *and*
the "regenerate" menu action share identical logic.

### 10.3 The "42" fallback logic

The pattern is dropped, with a message, in three situations:

1. **Disabled** (`PATTERN=False`) → no pattern.
2. **Too small** — `fits()` is false → print the "need at least W×H"
   message and omit it.
3. **Collision** — a pattern cell lands on the entry or exit → omit it.
4. **Disconnection** — if generation raises `DisconnectedMazeError` because
   the pattern walled off part of the grid, `_generate` retries once with
   an empty blocked set.

### 10.4 The interactive menu

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show/Hide path from entry to exit
3. Rotate maze colors
4. Quit
Choice? (1-4):
```

Loop behaviour:

- `1` **Regenerate** — bumps the seed (`seed + regen_count`) so each new maze
  is different but still reproducible, then rebuilds and re-solves.
- `2` **Show/Hide path** — flips a boolean the renderer reads.
- `3` **Rotate maze colors** — increments the wall-colour index.
- `4` **Quit** — return cleanly.
- Anything else → a gentle "Please choose 1, 2, 3 or 4."

If **stdin is not a terminal** (a pipe, a test harness, `< /dev/null`), the
program renders **once** in plain ASCII and exits — so it is safe to run
non-interactively. `EOF`/`Ctrl-C` also exit cleanly.

### 10.5 `_enable_windows_ansi`

On Windows, the classic console doesn't interpret `\x1b[...m` escapes until
you enable *virtual terminal processing*. This helper flips that flag via
`ctypes` so the coloured blocks show up; on any failure it silently does
nothing (colour is a nicety, not a requirement).

---

## 11. End-to-end walkthrough

Running `python a_maze_ing.py config.txt` with the shipped config
(`WIDTH=20 HEIGHT=20 ENTRY=0,0 EXIT=19,19 PERFECT=False SEED=42 PATTERN=True`):

1. **Config** → `Config(width=20, height=20, entry=(0,0), exit=(19,19),
   output_file="maze.txt", perfect=False, seed=42, braid=0.0, pattern=True)`.
2. **"42" cells** → `blocked_cells(20, 20)` returns the centred glyph cells
   (20×20 easily clears 9×7). Neither corner collides, so they're kept.
3. **Generate** → `MazeGenerator(...seed=42...)` runs the backtracker over
   all non-blocked cells. `braid=0.0`, so no braiding: the maze is a perfect
   spanning tree with a solid "42" island in the middle.
4. **Solve** → BFS from `(0,0)` to `(19,19)` → the shortest move list.
5. **Write** → `maze.txt`: 20 hex rows (20 digits each), a blank line,
   `0,0`, `19,19`, then the path letters — every line `\n`-terminated.
6. **Render** → a `41 × 41` kind grid painted as coloured blocks — thin
   walls around chunky cells: white walls, magenta entry (top-left), red
   exit (bottom-right), a continuous cyan path, grey "42" in the centre —
   then the numbered menu.
7. **Interact** → menu keys mutate `show_path` / colour index / seed and the
   screen redraws each loop.

Re-running with the **same seed** reproduces byte-for-byte the same
`maze.txt`.

---

## 12. Requirement traceability

| Subject requirement | Where it's handled |
|---------------------|--------------------|
| `python3 a_maze_ing.py config.txt` usage | `a_maze_ing.py :: main` |
| `KEY=VALUE` config, `#` comments, mandatory keys | `amaze/config.py` |
| Never crash; clear errors | `try/except` in `main`; `ConfigError`, `DisconnectedMazeError` |
| Random **but reproducible** via seed | `random.Random(seed)` in `generator.py` |
| 0–4 walls per cell at N/E/S/W | `grid.py` wall bitmask |
| Coherent shared walls | `Maze.carve` opens both sides at once |
| Closed outer border | `carve` refuses out-of-bounds neighbours |
| Full connectivity, no isolated cells (except "42") | backtracker + `DisconnectedMazeError` check |
| No open area wider than 2 (no 3×3) | tree is 1-wide; `would_form_3x3_open` guards braiding |
| Visible "42" of fully-closed cells | `pattern42.py` + `_fill_pattern` in the renderer |
| "42" omitted (with message) when too small | `_compute_blocked` + `fits()` |
| `PERFECT=True` → exactly one path | spanning tree (no braiding) |
| Hex output: rows, blank line, entry, exit, path | `amaze/output.py` |
| Terminal visual + interactions (regen/path/colour) | `render_terminal.py` + interactive loop |
| Reusable `MazeGenerator` class, pip-installable | `src/mazegen/` + `pyproject.toml` → `mazegen-*.whl` |

---

## 13. Running, building, testing

> On Windows use `python`; on POSIX use `python3` (or the `make` targets).

```powershell
# Run (generate maze.txt + interactive menu)
python a_maze_ing.py config.txt

# Install for development (makes `mazegen` importable outside src/)
python -m pip install -e .

# Tests / lint / types
python -m pytest tests/ -q
python -m flake8 .
python -m mypy . --strict

# Rebuild the reusable wheel
python -m build --wheel
```

The equivalent `make` targets (`install`, `run`, `debug`, `clean`, `lint`,
`lint-strict`, `test`, `package`) exist for graders on a POSIX box with
`make` installed.

### Using the library directly

```python
from mazegen import MazeGenerator, blocked_cells, solve

gen = MazeGenerator(20, 15, entry=(0, 0), exit=(19, 14),
                    seed=42, perfect=True, blocked=blocked_cells(20, 15))
maze  = gen.generate()          # the structure (mazegen.grid.Maze)
moves = gen.solution()          # ['E', 'S', 'S', ...]  (N/E/S/W letters)
```
