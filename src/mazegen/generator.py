"""Randomized maze generation on top of the shared grid model.

Builds a :class:`~mazegen.grid.Maze` with an iterative randomized
backtracker (depth-first search with an explicit stack). Supports a set
of fully-closed ``blocked`` cells (the "42") and an optional braiding
pass that adds loops without ever creating a 3x3 open area.
"""

from __future__ import annotations

import math
import random
from typing import List, Optional, Set, Tuple

from mazegen.grid import E, S, Maze

_Cell = Tuple[int, int]


class DisconnectedMazeError(Exception):
    """Raised when blocked cells split the traversable region."""


class MazeGenerator:
    """Generate a maze with a reproducible randomized backtracker.

    Args:
        width: Number of cells per row.
        height: Number of rows.
        entry: ``(x, y)`` start cell.
        exit: ``(x, y)`` goal cell, different from ``entry``.
        seed: Optional seed for reproducible output.
        perfect: If true, produce a perfect (loop-free) maze.
        braid: Fraction in ``[0, 1]`` of closed internal walls to open
            during braiding, used only when ``perfect`` is false.
        blocked: Cells to wall off completely and never traverse.

    Raises:
        ValueError: If an argument is out of range or inconsistent.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: _Cell,
        exit: _Cell,
        *,
        seed: Optional[int] = None,
        perfect: bool = True,
        braid: float = 0.0,
        blocked: Optional[Set[_Cell]] = None,
    ) -> None:
        """Validate the arguments and store the generation parameters."""
        if width < 1 or height < 1:
            raise ValueError("width and height must be >= 1")
        blocked_set: Set[_Cell] = set(blocked) if blocked else set()
        if not self._in_bounds(entry, width, height):
            raise ValueError("entry is out of bounds")
        if not self._in_bounds(exit, width, height):
            raise ValueError("exit is out of bounds")
        if entry == exit:
            raise ValueError("entry and exit must differ")
        if entry in blocked_set:
            raise ValueError("entry must not be a blocked cell")
        if exit in blocked_set:
            raise ValueError("exit must not be a blocked cell")

        self._width: int = width
        self._height: int = height
        self._entry: _Cell = entry
        self._exit: _Cell = exit
        self._perfect: bool = perfect
        self._braid: float = braid
        self._blocked: Set[_Cell] = blocked_set
        self._rng: random.Random = random.Random(seed)
        self._maze: Optional[Maze] = None

    @staticmethod
    def _in_bounds(cell: _Cell, width: int, height: int) -> bool:
        """Return whether ``cell`` lies inside a ``width`` x ``height``."""
        x, y = cell
        return 0 <= x < width and 0 <= y < height

    def generate(self) -> Maze:
        """Build, store and return the maze.

        Runs the backtracker over the non-blocked cells from ``entry``,
        then braids if requested.

        Returns:
            The generated maze.

        Raises:
            DisconnectedMazeError: If blocked cells leave some cell
                unreachable.
        """
        maze = Maze(self._width, self._height)
        for cell in self._blocked:
            maze.close_all(*cell)

        visited: Set[_Cell] = {self._entry}
        stack: List[_Cell] = [self._entry]
        while stack:
            x, y = stack[-1]
            candidates = [
                (nx, ny, direction)
                for nx, ny, direction in maze.neighbors(x, y)
                if (nx, ny) not in self._blocked
                and (nx, ny) not in visited
            ]
            if candidates:
                nx, ny, direction = self._rng.choice(candidates)
                maze.carve(x, y, direction)
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

        expected = self._width * self._height - len(self._blocked)
        if len(visited) != expected:
            raise DisconnectedMazeError(
                "blocked cells split the traversable region"
            )

        if not self._perfect and self._braid > 0:
            self._braid_maze(maze)

        self._maze = maze
        return maze

    def _braid_maze(self, maze: Maze) -> None:
        """Open extra internal walls without forming a 3x3 open area."""
        candidates: List[Tuple[int, int, int]] = []
        for y in range(self._height):
            for x in range(self._width):
                if (x, y) in self._blocked:
                    continue
                for nx, ny, direction in maze.neighbors(x, y):
                    if direction not in (E, S):
                        continue
                    if (nx, ny) in self._blocked:
                        continue
                    if maze.has_wall(x, y, direction):
                        candidates.append((x, y, direction))

        self._rng.shuffle(candidates)
        target = math.floor(self._braid * len(candidates))
        opened = 0
        for x, y, direction in candidates:
            if opened >= target:
                break
            if not maze.would_form_3x3_open(x, y, direction):
                maze.carve(x, y, direction)
                opened += 1

    def get_structure(self) -> Maze:
        """Return the maze, generating it on first access."""
        if self._maze is None:
            return self.generate()
        return self._maze

    def solution(self) -> List[str]:
        """Return the shortest ``entry`` -> ``exit`` route as move letters."""
        from mazegen.solver import solve  # lazy: avoids an import cycle

        return solve(self.get_structure(), self._entry, self._exit)
