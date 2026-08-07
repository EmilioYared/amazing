_This project has been created as part of the 42 curriculum by anyousse, eyared._

# A-Maze-ing — *This is the way*

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
  (loops) via the `PERFECT` / `BRAID` settings.
- **Reproducible** generation from a `SEED`.
- A hidden **"42"** pattern, omitted with a console message when the maze
  is too small to hold it.
- Guaranteed **coherent** walls, **closed border**, and **no 3×3 open
  area** (corridors never wider than 2 cells).
- Shortest-path solver (BFS) written into the output file and drawn on
  screen.
- **Interactive** terminal view: regenerate, show/hide the path, cycle
  wall colours.
- Clean **flake8** and **mypy** (including `--strict`).

## Instructions

### Install

```bash
make install          # pip install build wheel flake8 mypy + editable install
```

No third-party dependency is required to run the program — `make install`
only adds the build and quality tools.

> On Windows (no `make`): use `make PYTHON=python install`, or run the
> equivalent `python -m pip ...` commands listed in the `Makefile`.

### Run

```bash
python3 a_maze_ing.py config.txt
```

The program writes the maze to `OUTPUT_FILE`, renders it as coloured
blocks, and offers a numbered menu:

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show/Hide path from entry to exit
3. Rotate maze colors
4. Quit
Choice? (1-4):
```

The maze is drawn with solid blocks: the walls take the current
(cyclable) colour, the entry is magenta, the exit red, the solution path
cyan, and the hidden "42" grey. The wall palette deliberately excludes
those four hues, so a wall is never painted the same colour as a marker.
Re-generating also rewrites `OUTPUT_FILE`, so the file always matches
what is on screen. When standard input is not a terminal (e.g. a test
harness), the program writes the file, renders once in plain ASCII, and
exits.

### Make targets

`install`, `run`, `debug` (pdb), `clean`, `lint`, `lint-strict`,
`package` (build the wheel and copy it to the repository root).

## Configuration file format

One `KEY=VALUE` pair per line. Lines starting with `#` are comments and
are ignored, as are blank lines. Unknown keys are ignored, and a key that
appears more than once takes its **last** value. The default file is
[`config.txt`](config.txt).

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

Validation rules: `WIDTH` and `HEIGHT` are integers ≥ 1 whose product is
at most 1 000 000 cells; `ENTRY` and `EXIT` must be inside the grid and
different from each other; `BRAID` must lie in `[0.0, 1.0]`. Any missing
mandatory key, malformed value or failed rule produces a clear
`error: ...` message and exit code 1 — the program never crashes.

Complete example:

```ini
# A-Maze-ing default configuration file.
# One KEY=VALUE pair per line. Lines starting with '#' are comments.

# --- Mandatory keys ---
WIDTH=10
HEIGHT=10
ENTRY=0,0
EXIT=9,9
OUTPUT_FILE=maze.txt
PERFECT=False

# --- Optional keys ---
SEED=42
ALGORITHM=backtracker
# BRAID=0.15
PATTERN=True
DISPLAY=terminal
```

## Output file format

- One **hexadecimal digit per cell**, one row per line, top row first.
  Each digit encodes the cell's **closed** walls (a set bit = a closed
  wall):

  | Bit | Value | Direction |
  |-----|-------|-----------|
  | 0 | 1 | North |
  | 1 | 2 | East |
  | 2 | 4 | South |
  | 3 | 8 | West |

  e.g. `3` (`0011`) closes North+East; `A` (`1010`) closes East+West.
- Then an **empty line**, followed by three lines: the **entry** `x,y`,
  the **exit** `x,y`, and the **shortest path** as `N`/`E`/`S`/`W`
  letters.
- Every line ends with `\n`.

## Algorithm

**Iterative randomized backtracker** (a.k.a. recursive backtracker /
randomized depth-first search), implemented with an explicit stack.

### Why this algorithm

A perfect maze is exactly a *spanning tree* of the grid graph, and the
backtracker builds one directly:

- It guarantees **full connectivity** and, being a tree, **exactly one
  path** between any two cells — satisfying `PERFECT=True` for free.
- A tree has no cycles, so it **cannot** contain a 2×2 (let alone 3×3)
  open block — the "no large open area" rule is satisfied with **zero**
  extra work; corridors are 1 cell wide.
- It is **simple, fast, and memory-light** (an explicit stack avoids
  Python's recursion limit on large mazes; the grid is a flat
  `bytearray`).
- It is fully **reproducible** from a seeded RNG.

For `PERFECT=False`, a **braiding** pass opens a fraction (`BRAID`) of
extra walls to introduce loops, checking a constant-time *3×3-open* guard
before each removal so the "no 3×3 open area" rule is never violated.

### The "42" pattern

The digits are drawn from a 3×5 pixel font (7×5 together) placed at the
centre of the grid with a one-cell margin. Those cells are marked **fully
closed** and excluded from traversal, so they appear as solid blocks and
never affect connectivity or the unique-path property. The glyph is never
scaled to the maze: a larger grid gets the same "42" with more margin. If
the maze is smaller than **9×7**, the pattern is omitted and a message is
printed on the console, as required.

## Reusable module

The generator ships as the pure-Python package **`mazegen`**, built into
a single wheel at the repository root:
[`mazegen-1.0.0-py3-none-any.whl`](mazegen-1.0.0-py3-none-any.whl).
Everything needed to rebuild it from source is in the repository — run
`make package` (or `python -m build`) to regenerate the wheel.

### Instantiate and use the generator

```python
from mazegen import MazeGenerator, blocked_cells

gen = MazeGenerator(20, 15, entry=(0, 0), exit=(19, 14),
                    seed=42, perfect=True,
                    blocked=blocked_cells(20, 15))
maze = gen.generate()
```

### Pass custom parameters

| Parameter | Meaning |
|-----------|---------|
| `width`, `height` | grid size in cells |
| `entry`, `exit` | `(x, y)` start and goal cells |
| `seed` | seed for reproducible output (`None` = random) |
| `perfect` | `True` for a spanning-tree maze |
| `braid` | fraction of extra walls opened when `perfect=False` |
| `blocked` | cells to wall off completely (e.g. the "42") |

```python
gen = MazeGenerator(40, 30, (0, 0), (39, 29),
                    seed=7, perfect=False, braid=0.15)
```

### Access the structure and a solution

```python
maze = gen.get_structure()        # a mazegen.grid.Maze
maze.walls(3, 4)                  # 4-bit wall mask of one cell
maze.has_wall(3, 4, mazegen.E)    # is the east wall closed?

moves = gen.solution()            # ['E', 'S', 'S', ...]
cells = mazegen.path_cells(maze, (0, 0), (19, 14))   # [(0,0), (1,0), ...]
```

`get_structure()` returns the in-memory `Maze` object — this is *not* the
same format as the output file, which is produced by the application
layer. `DisconnectedMazeError` is raised if the `blocked` cells split the
grid into unreachable regions.

Full library documentation: [`src/mazegen/README.md`](src/mazegen/README.md),
which also ships inside the wheel.

### What is reusable, and how

The `mazegen` package (`src/mazegen/`) is the reusable part: the grid
model, the generator, the BFS solver and the "42" glyph placement. It has
**zero third-party dependencies** and knows nothing about config files,
output files or terminals.

The **application layer** (`amaze/` and `a_maze_ing.py`) — config
parsing, output writing, terminal rendering and the CLI — is
intentionally **not** part of the package, so the library stays general
purpose. The "42" reaches the generator only as a set of coordinates via
the `blocked` argument, which is what keeps the two layers independent.

## Project structure

```
amazing/
├── a_maze_ing.py            # CLI entry point (python3 a_maze_ing.py config.txt)
├── config.txt               # default configuration
├── Makefile  pyproject.toml  .gitignore
├── mazegen-1.0.0-py3-none-any.whl   # built reusable package (repo root)
├── src/mazegen/             # reusable library (pure Python, zero deps)
│   ├── grid.py              #   Maze model, wall encoding, 3×3 checks
│   ├── generator.py         #   MazeGenerator (iterative backtracker + braid)
│   ├── solver.py            #   BFS shortest path -> N/E/S/W
│   ├── pattern42.py         #   the hidden "42"
│   └── README.md            #   library documentation (ships in the wheel)
└── amaze/                   # application layer (not reusable)
    ├── config.py            #   KEY=VALUE parsing and validation
    ├── output.py            #   hex output-file writer
    └── render_terminal.py   #   block-style terminal renderer
```

## Quality

```bash
make lint          # flake8 . && mypy . (mandatory flags)
make lint-strict   # flake8 . && mypy . --strict   (also clean)
```

Both are clean. Every function and class carries a PEP 257 docstring in
Google style, and all code is type-hinted.

## Team and project management

### Roles

| Member | Responsibilities |
|--------|------------------|
| **anyousse** | Grid model and wall encoding (`grid.py`), the generation algorithm (`generator.py`), the braiding pass and the 3×3 open-area rule, the hidden "42" glyph (`pattern42.py`), packaging and the wheel build. |
| **eyared** | Configuration parsing and validation (`config.py`), the output-file writer (`output.py`), the terminal renderer and colour handling (`render_terminal.py`), the CLI and interactive menu (`a_maze_ing.py`), the Makefile and documentation. |

Both members reviewed each other's modules, and the BFS solver
(`solver.py`) was written together as it sits on the boundary between the
two halves.

### Planning and how it evolved

We split the work into four phases: **explore → plan → build → verify**.

1. A short foundation phase locked the shared contract — the wall-bit
   encoding and the `Maze` interface — before any other code was written.
2. The independent modules (generator, solver, pattern, config, output,
   renderer) were then built in parallel against that frozen contract.
3. Integration, followed by a finalize phase: packaging, lint, docs.

The plan mostly held. The two things that changed along the way: we
initially expected to need a separate validation pass for wall coherence
and the 3×3 rule, and discovered that carving both sides of a wall at
once and using a spanning tree made most of it unnecessary; and we
deferred the bonuses (multiple algorithms, generation animation, MLX
display), which remain open follow-ups.

### What worked well, what could be improved

**Worked well.** Freezing the `Maze` interface up front let both of us
develop and check our modules independently with almost no rework at
integration. Keeping the geometry checks inside `grid.py` avoided a
circular dependency between the generator and the validators. Passing the
"42" in as plain coordinates kept the library free of project-specific
concerns.

**Could be improved.** We tested the renderer by eye for too long before
writing checks for it, which let a colour collision (walls cycling onto
the path colour) survive longer than it should have. We would also start
the packaging step earlier — leaving the wheel build to the end meant
rebuilding it several times as the source changed.

### Tools

Python 3.11, `flake8`, `mypy`, `build`/`wheel`, `pytest` during
development, and Git.

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
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/) and the
  [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).

### How AI was used

AI (Claude) was used as a productivity aid. Every result was read,
questioned and tested before being kept; nothing was accepted that we
could not explain ourselves.

- **Planning** — analysing the subject and drafting the phased plan and
  the frozen module interfaces.
- **Implementation** — scaffolding first drafts of the independent
  modules once the contract was fixed, and drafting the docstrings.
  Reviewed and rewritten by hand where the generated logic was unclear.
- **Verification** — running flake8, mypy and the end-to-end output
  checks, and investigating the issues they surfaced: a regeneration that
  did not rewrite the output file, unbounded `WIDTH`/`HEIGHT` values that
  raised `MemoryError` instead of a clean error, and wall colours that
  could collide with the entry, exit, path or "42" markers.

Core design decisions — the algorithm choice, the wall-encoding contract,
the "42" placement strategy and the reusable/application split — were
made and validated by us.
