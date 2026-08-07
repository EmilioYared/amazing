#!/usr/bin/env python3
"""A-Maze-ing -- command-line maze generator.

Usage::

    python3 a_maze_ing.py config.txt

Reads a configuration file, generates a maze hiding a "42", writes it to
the configured output file, renders it in the terminal and offers an
interactive menu.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

# Make the src-layout ``mazegen`` package importable when running this
# script directly (i.e. without ``pip install``).
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from amaze.config import Config, ConfigError, load_config  # noqa: E402
from amaze.output import write_output  # noqa: E402
from amaze.render_terminal import build_grid, to_string  # noqa: E402
from mazegen.generator import (  # noqa: E402
    DisconnectedMazeError,
    MazeGenerator,
)
from mazegen.grid import Maze  # noqa: E402
from mazegen.pattern42 import blocked_cells, fits, min_dimensions  # noqa: E402
from mazegen.solver import solve  # noqa: E402

_Cell = Tuple[int, int]

#: Colour swatches for the on-screen legend: (label, ANSI background).
_LEGEND = [
    ("entry", "45"),
    ("exit", "41"),
    ("path", "46"),
    ("'42'", "100"),
]

_MENU = (
    "=== A-Maze-ing ===\n"
    "1. Re-generate a new maze\n"
    "2. Show/Hide path from entry to exit\n"
    "3. Rotate maze colors\n"
    "4. Quit"
)


def _enable_windows_ansi() -> None:
    """Best-effort enable ANSI escape sequences on a Windows console."""
    if os.name != "nt":
        return
    try:
        import ctypes

        windll = getattr(ctypes, "windll", None)
        if windll is None:
            return
        handle = windll.kernel32.GetStdHandle(-11)
        windll.kernel32.SetConsoleMode(handle, 7)
    except Exception:
        return


def _compute_blocked(cfg: Config, verbose: bool = True) -> Set[_Cell]:
    """Return the '42' cells, or an empty set with a message.

    The pattern is omitted when disabled, when the maze is too small, or
    when it would collide with the entry or exit.

    Args:
        cfg: The maze configuration.
        verbose: Whether to print the reason to stderr.

    Returns:
        The cells to wall off, possibly empty.
    """
    if not cfg.pattern:
        return set()
    if not fits(cfg.width, cfg.height):
        if verbose:
            min_w, min_h = min_dimensions()
            print(
                "warning: '42' pattern omitted: maze too small "
                "(need at least %dx%d, got %dx%d)"
                % (min_w, min_h, cfg.width, cfg.height),
                file=sys.stderr,
            )
        return set()
    blocked = blocked_cells(cfg.width, cfg.height)
    if cfg.entry in blocked or cfg.exit in blocked:
        if verbose:
            print(
                "warning: '42' pattern omitted: it collides with the "
                "entry or exit cell",
                file=sys.stderr,
            )
        return set()
    return blocked


def _generate(
    cfg: Config, seed: Optional[int], blocked: Set[_Cell],
    verbose: bool = True,
) -> Maze:
    """Generate a maze, dropping the pattern if it disconnects the maze.

    Args:
        cfg: The maze configuration.
        seed: Seed for this generation.
        blocked: Cells to wall off.
        verbose: Whether to print the retry reason to stderr.

    Returns:
        The generated maze.

    Raises:
        DisconnectedMazeError: If generation fails with no pattern.
    """
    try:
        gen = MazeGenerator(
            cfg.width, cfg.height, cfg.entry, cfg.exit,
            seed=seed, perfect=cfg.perfect, braid=cfg.braid,
            blocked=blocked,
        )
        return gen.generate()
    except DisconnectedMazeError:
        if not blocked:
            raise
        if verbose:
            print(
                "warning: '42' pattern omitted: it disconnects the maze; "
                "regenerating without it",
                file=sys.stderr,
            )
        gen = MazeGenerator(
            cfg.width, cfg.height, cfg.entry, cfg.exit,
            seed=seed, perfect=cfg.perfect, braid=cfg.braid, blocked=set(),
        )
        return gen.generate()


def _build_maze(
    cfg: Config, seed: Optional[int], verbose: bool = True,
) -> Tuple[Maze, List[str]]:
    """Generate a maze and its shortest solution.

    Args:
        cfg: The maze configuration.
        seed: Seed for this generation.
        verbose: Whether to print warnings to stderr.

    Returns:
        The maze and its solution moves.
    """
    blocked = _compute_blocked(cfg, verbose=verbose)
    maze = _generate(cfg, seed, blocked, verbose=verbose)
    moves = solve(maze, cfg.entry, cfg.exit)
    return maze, moves


def _write(cfg: Config, maze: Maze, moves: List[str]) -> bool:
    """Write ``maze`` to ``cfg.output_file``, reporting any failure.

    Called for the first maze and after every regeneration, so the file
    always matches what is on screen.

    Args:
        cfg: The maze configuration.
        maze: The maze to write.
        moves: Solution moves.

    Returns:
        Whether the file was written.
    """
    try:
        write_output(cfg.output_file, maze, cfg.entry, cfg.exit, moves)
    except OSError as exc:
        print("error: could not write output: %s" % exc, file=sys.stderr)
        return False
    print("maze written to %s" % cfg.output_file)
    return True


def _legend(color: bool) -> str:
    """Return a one-line colour key for the markers.

    Args:
        color: Whether colour output is available.

    Returns:
        The legend line.
    """
    if not color:
        return "S entry   E exit   * path   @ '42'"
    parts = [
        "\x1b[%sm  \x1b[0m %s" % (bg, label) for label, bg in _LEGEND
    ]
    return "  ".join(parts)


def _display(
    maze: Maze, cfg: Config, moves: List[str],
    show_path: bool, color_idx: int,
) -> None:
    """Render the maze to stdout with the current view options.

    Args:
        maze: The maze to draw.
        cfg: The maze configuration.
        moves: Solution moves.
        show_path: Whether to draw the path.
        color_idx: Current wall-colour index.
    """
    color = sys.stdout.isatty()
    grid = build_grid(
        maze, entry=cfg.entry, exit=cfg.exit,
        path=moves, show_path=show_path,
    )
    print()
    print(to_string(grid, wall_color=color_idx, color=color))
    print(_legend(color))
    print("entry=%s  exit=%s  solution=%d moves"
          % (cfg.entry, cfg.exit, len(moves)))


def _interactive(
    cfg: Config, seed: Optional[int], maze: Maze, moves: List[str],
) -> None:
    """Run the render/menu loop, rendering once if stdin is not a TTY.

    Args:
        cfg: The maze configuration.
        seed: The configured seed, offset on each regeneration.
        maze: The maze to display first.
        moves: Its solution moves.
    """
    show_path = True
    color_idx = 0
    regen = 0
    while True:
        _display(maze, cfg, moves, show_path, color_idx)
        if not sys.stdin.isatty():
            return
        print(_MENU)
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            regen += 1
            new_seed = None if seed is None else seed + regen
            try:
                maze, moves = _build_maze(cfg, new_seed, verbose=False)
            except (ValueError, DisconnectedMazeError) as exc:
                print("error: %s" % exc, file=sys.stderr)
            else:
                _write(cfg, maze, moves)
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            color_idx += 1
        elif choice == "4":
            return
        else:
            print("Please choose 1, 2, 3 or 4.")


def main(argv: List[str]) -> int:
    """Run the program.

    Args:
        argv: Command-line arguments, ``argv[1]`` being the config file.

    Returns:
        The process exit code.
    """
    if len(argv) != 2:
        print("usage: python3 a_maze_ing.py config.txt", file=sys.stderr)
        return 1
    try:
        cfg = load_config(argv[1])
    except ConfigError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    try:
        maze, moves = _build_maze(cfg, cfg.seed)
    except (ValueError, DisconnectedMazeError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    except (MemoryError, OverflowError):
        print("error: maze too large to allocate (%dx%d)"
              % (cfg.width, cfg.height), file=sys.stderr)
        return 1

    if not _write(cfg, maze, moves):
        return 1

    _enable_windows_ansi()
    _interactive(cfg, cfg.seed, maze, moves)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
