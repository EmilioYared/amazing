_This project has been created as part of the 42 curriculum by <login1>._

# A-Maze-ing — *This is the way*

Generate a maze from a configuration file, hide a "42" inside it, solve it,
write it to a hex-encoded file, and explore it in the terminal.

![render](https://img.shields.io/badge/render-terminal%20ASCII-blue)
![python](https://img.shields.io/badge/python-3.10%2B-green)
![lint](https://img.shields.io/badge/flake8%20%2B%20mypy-clean-brightgreen)

## Description

**A-Maze-ing** is a maze generator written in Python 3.10+. It reads a
plain-text configuration file, generates a maze — optionally a *perfect*
maze with a single path between the entry and the exit — that contains a
hidden **"42"** drawn with fully-closed cells, writes it to an output file
using a compact hexadecimal wall encoding, and renders it in the terminal
with an interactive loop.

The maze-generation logic is packaged as a **reusable, dependency-free
library** (`mazegen`) that can be `pip`-installed and imported by other
projects.

### Features

- Perfect mazes (spanning tree, one unique path) and **braided** mazes
  (loops) via a `PERFECT`/`BRAID` setting.
- **Reproducible** generation from a `SEED`.
- A hidden **"42"** pattern (omitted with a clear message when the maze is
  too small to hold it).
- Guaranteed **coherent** walls, **closed border**, and **no 3×3 open
  area** (corridors never wider than 2 cells).
- Shortest-path solver (BFS) written into the output and drawn on screen.
- **Interactive** terminal view: regenerate, show/hide the path, cycle
  wall colours.
- Clean **flake8** and **mypy** (including `--strict`), with a **pytest**
  suite (61 tests).

## Instructions

### Install

```bash
make install          # pip install build wheel pytest flake8 mypy + editable install
# or, minimally, just run it directly — no third-party deps are required.
```

> On Windows (no `make`): `make PYTHON=python install`, or run the
> equivalent `python -m pip ...` commands shown in the `Makefile`.

### Run

```bash
python3 a_maze_ing.py config.txt
```

The program writes the maze to `OUTPUT_FILE`, renders it as coloured
blocks, and — in an interactive terminal — offers a numbered menu:

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show/Hide path from entry to exit
3. Rotate maze colors
4. Quit
Choice? (1-4):
```

The maze is drawn with solid blocks: the walls take the current (cyclable)
colour, the entry is magenta, the exit red, the solution path cyan, and the
hidden "42" grey. When standard input is not a terminal (e.g. a test
harness), the program writes the file, renders once in plain ASCII, and
exits.

### Make targets

`install`, `run`, `debug` (pdb), `clean`, `lint`, `lint-strict`, `test`,
`package` (build the wheel and copy it to the repo root).

## Configuration file format

One `KEY=VALUE` pair per line. Lines starting with `#` are comments and are
ignored. Unknown keys are ignored. See [`config.txt`](config.txt).

**Mandatory keys**

| Key | Description | Example |
|-----|-------------|---------|
| `WIDTH` | maze width in cells | `WIDTH=20` |
| `HEIGHT` | maze height in cells | `HEIGHT=15` |
| `ENTRY` | entry cell `x,y` | `ENTRY=0,0` |
| `EXIT` | exit cell `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | perfect maze? | `PERFECT=True` |

**Optional keys**

| Key | Default | Description |
|-----|---------|-------------|
| `SEED` | random | integer seed for reproducible mazes |
| `ALGORITHM` | `backtracker` | generation algorithm |
| `BRAID` | `0.0` | fraction `0..1` of extra walls to open when `PERFECT=False` |
| `PATTERN` | `True` | draw the hidden "42" |
| `DISPLAY` | `terminal` | rendering mode |

Entry and exit must be different, inside the grid, and not on a "42" cell.

## Output file format

- One **hexadecimal digit per cell**, one row per line, top row first. Each
  digit encodes the cell's **closed** walls (a set bit = a closed wall):

  | Bit | Value | Direction |
  |-----|-------|-----------|
  | 0 | 1 | North |
  | 1 | 2 | East |
  | 2 | 4 | South |
  | 3 | 8 | West |

  e.g. `3` (`0011`) closes North+East; `A` (`1010`) closes East+West.
- Then an **empty line**, followed by three lines: the **entry** `x,y`, the
  **exit** `x,y`, and the **shortest path** as `N`/`E`/`S`/`W` letters.
- Every line ends with `\n`.

A validation of these invariants (coherence, closed border, no 3×3 open
area, spanning-tree for perfect mazes, and a walkable path) is exercised by
the test suite and the end-to-end checks.

## Algorithm

**Iterative randomized backtracker** (a.k.a. recursive backtracker /
randomized depth-first search), implemented with an explicit stack.

**Why this algorithm.** A perfect maze is exactly a *spanning tree* of the
grid graph, and the backtracker builds one directly:

- It guarantees **full connectivity** and, being a tree, **exactly one
  path** between any two cells — satisfying `PERFECT=True` for free.
- A tree has no cycles, so it **cannot** contain a 2×2 (let alone 3×3) open
  block — the "no large open area" rule is satisfied with **zero** extra
  work; corridors are 1 cell wide.
- It is **simple, fast, and memory-light** (an explicit stack avoids
  Python's recursion limit on large mazes; the grid is a flat `bytearray`).
- It is fully **reproducible** from a seeded RNG.

For `PERFECT=False`, a **braiding** pass opens a fraction (`BRAID`) of
extra walls to introduce loops, checking a constant-time *3×3-open* guard
before each removal so the "no 3×3 open area" rule is never violated.

### The "42" pattern

The digits are drawn from a 3×5 pixel font (7×5 together) placed at the
centre of the grid with a one-cell margin. Those cells are marked
**fully closed** and excluded from traversal, so they appear as solid
blocks and never affect connectivity or the unique-path property. If the
maze is smaller than **9×7**, the pattern is omitted and a message is
printed, as required.

## Reusable module

The generator ships as the pure-Python package **`mazegen`**, built into a
single wheel at the repository root:
[`mazegen-1.0.0-py3-none-any.whl`](mazegen-1.0.0-py3-none-any.whl). Rebuild
it from source at any time with `make package` (or `python -m build`).

```python
from mazegen import MazeGenerator, blocked_cells

gen = MazeGenerator(20, 15, entry=(0, 0), exit=(19, 14),
                    seed=42, perfect=True, blocked=blocked_cells(20, 15))
maze = gen.generate()      # the structure (mazegen.grid.Maze)
moves = gen.solution()     # a solution: ['E', 'S', 'S', ...]
```

- **Instantiate & use:** construct `MazeGenerator(...)`, call `generate()`.
- **Custom parameters:** `width`, `height`, `entry`, `exit`, `seed`,
  `perfect`, `braid`, `blocked` (see `src/mazegen/README.md`).
- **Access the structure & a solution:** `get_structure()` returns the
  `Maze` (query `walls(x, y)` / `has_wall(x, y, d)`); `solution()` — or
  `mazegen.solve(maze, entry, exit)` — returns the shortest path.

The **application layer** (`amaze/` and `a_maze_ing.py`) — config parsing,
output writing, terminal rendering, and the CLI — is intentionally **not**
part of the reusable package, so the library stays free of app concerns and
third-party dependencies.

## Project structure

```
amazing/
├── a_maze_ing.py            # CLI entry point (python3 a_maze_ing.py config.txt)
├── config.txt               # default configuration
├── Makefile  pyproject.toml  .flake8  .gitignore
├── mazegen-1.0.0-py3-none-any.whl   # built reusable package (repo root)
├── src/mazegen/             # reusable library (pure Python, zero deps)
│   ├── grid.py              #   Maze model, wall encoding, 3×3 checks
│   ├── generator.py         #   MazeGenerator (iterative backtracker + braid)
│   ├── solver.py            #   BFS shortest path -> N/E/S/W
│   ├── pattern42.py         #   the hidden "42"
│   └── README.md            #   library documentation (ships in the wheel)
├── amaze/                   # application layer (not reusable)
│   ├── config.py  output.py  render_terminal.py
└── tests/                   # pytest suite (61 tests)
```

## Testing & quality

```bash
make test          # pytest  (61 passing)
make lint          # flake8 . && mypy . (mandatory flags)
make lint-strict   # flake8 . && mypy . --strict   (also clean)
```

## Team & project management

- **Roles.** _<to be completed by the team — e.g. algorithm/generator,
  I/O & config, rendering & UX, packaging & docs.>_
- **Planning.** The work was split into an *explore → plan → build → verify*
  flow (see [`PLAN.md`](PLAN.md)): a foundation phase locked the shared
  grid contract, then the independent modules (generator, solver, pattern,
  config, output, renderer) were built in parallel against that contract,
  followed by integration and a finalize phase (packaging, lint, docs).
- **What worked well.** Freezing the `Maze` interface up front let the
  modules be developed and unit-tested independently with no rework at
  integration; keeping the geometry checks in `grid.py` avoided a
  circular dependency between the generator and the validators.
- **What could be improved.** Bonuses (multiple algorithms, generation
  animation, a graphical display) were deliberately deferred and remain
  open follow-ups.
- **Tools.** Python 3.11, `pytest`, `flake8`, `mypy`, `build`/`wheel`,
  and Git. Development was assisted by AI (see below).

## Resources

Classic references on maze generation:

- Jamis Buck, *Mazes for Programmers* (Pragmatic Bookshelf) and his
  [maze algorithm articles](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap).
- Wikipedia: [Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
  and [Spanning tree](https://en.wikipedia.org/wiki/Spanning_tree).
- Walter D. Pullen, [*Think Labyrinth!* — maze algorithms](https://www.astrolog.org/labyrnth/algrithm.htm).
- Python docs: [`random`](https://docs.python.org/3/library/random.html),
  [`typing`](https://docs.python.org/3/library/typing.html),
  [packaging with `pyproject.toml`](https://packaging.python.org/).

### How AI was used

AI (Claude Code) was used as a productivity aid, with every result reviewed
and tested:

- **Planning:** analysing the subject and drafting the phased plan and the
  frozen module interfaces (`PLAN.md`).
- **Implementation:** scaffolding and generating first drafts of the
  independent modules and their unit tests against the locked contract.
- **Verification:** running flake8/mypy/pytest and the end-to-end output
  checks, and fixing issues surfaced by them.

Core design decisions (algorithm choice, the wall-encoding contract, the
"42" placement strategy, the reusable/app split) were made and validated by
the team; AI-generated code was only kept where it was fully understood.
