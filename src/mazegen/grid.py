"""Maze grid model and wall geometry.

Wall encoding, one hex digit per cell::

    bit 0 (1) North    bit 1 (2) East
    bit 2 (4) South    bit 3 (8) West

A set bit means the wall is closed, a cleared bit that it is open.
"""

from __future__ import annotations

from typing import Dict, Iterator, Optional, Tuple

# --- Wall direction constants (bit values) ---
N: int = 1
E: int = 2
S: int = 4
W: int = 8
ALL: int = N | E | S | W  # 15 -> a fully walled cell

#: Opposite direction of each wall (the shared edge between two cells).
OPPOSITE: Dict[int, int] = {N: S, S: N, E: W, W: E}

#: Grid displacement ``(dx, dy)`` per direction (y grows downward).
DELTA: Dict[int, Tuple[int, int]] = {
    N: (0, -1),
    S: (0, 1),
    E: (1, 0),
    W: (-1, 0),
}

#: Move letter for each direction.
LETTER: Dict[int, str] = {N: "N", E: "E", S: "S", W: "W"}

#: Iteration order when walking a cell's four neighbours.
_DIRECTIONS: Tuple[int, ...] = (N, E, S, W)

#: An edge named by its top/left cell using only ``E`` or ``S``, so every
#: physical wall has exactly one representation.
_Edge = Tuple[int, int, int]


class Maze:
    """A rectangular grid of cells, each holding a 4-bit wall mask.

    Every cell starts fully walled. Passages are opened with
    :meth:`carve`, which clears the shared bit on both neighbours so the
    two sides of a wall can never disagree.

    Args:
        width: Number of cells per row.
        height: Number of rows.

    Raises:
        ValueError: If a dimension is below 1.
    """

    __slots__ = ("width", "height", "_cells")

    def __init__(self, width: int, height: int) -> None:
        """Create a grid of ``width`` x ``height`` fully walled cells."""
        if width < 1 or height < 1:
            raise ValueError("maze dimensions must be >= 1")
        self.width: int = width
        self.height: int = height
        self._cells: bytearray = bytearray([ALL]) * (width * height)

    # --- Indexing helpers ---------------------------------------------
    def _idx(self, x: int, y: int) -> int:
        """Return the flat index of cell ``(x, y)``."""
        return y * self.width + x

    def in_bounds(self, x: int, y: int) -> bool:
        """Return whether ``(x, y)`` lies inside the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    # --- Wall queries -------------------------------------------------
    def walls(self, x: int, y: int) -> int:
        """Return the 4-bit wall mask of cell ``(x, y)``."""
        return self._cells[self._idx(x, y)]

    def has_wall(self, x: int, y: int, direction: int) -> bool:
        """Return whether the wall on ``direction`` is closed."""
        return bool(self._cells[self._idx(x, y)] & direction)

    def is_open(self, x: int, y: int, direction: int) -> bool:
        """Return whether the wall on ``direction`` is open."""
        return not self._cells[self._idx(x, y)] & direction

    # --- Wall mutation ------------------------------------------------
    def close_all(self, x: int, y: int) -> None:
        """Fully wall cell ``(x, y)`` (used for the '42' pattern)."""
        self._cells[self._idx(x, y)] = ALL

    def carve(self, x: int, y: int, direction: int) -> None:
        """Open the wall between ``(x, y)`` and its ``direction`` neighbour.

        Clears the matching bit on both cells so the shared edge stays
        coherent. Carving toward the outer border is refused, which is
        what keeps the border closed.

        Args:
            x: Cell column.
            y: Cell row.
            direction: One of :data:`N`, :data:`E`, :data:`S`, :data:`W`.

        Raises:
            ValueError: If the neighbour lies outside the grid.
        """
        dx, dy = DELTA[direction]
        nx, ny = x + dx, y + dy
        if not self.in_bounds(nx, ny):
            raise ValueError("cannot carve the outer border")
        self._cells[self._idx(x, y)] &= ~direction & ALL
        self._cells[self._idx(nx, ny)] &= ~OPPOSITE[direction] & ALL

    # --- Neighbourhood ------------------------------------------------
    def neighbors(self, x: int, y: int) -> Iterator[Tuple[int, int, int]]:
        """Yield ``(nx, ny, direction)`` for each in-bounds neighbour."""
        for direction in _DIRECTIONS:
            dx, dy = DELTA[direction]
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny):
                yield nx, ny, direction

    # --- 3x3 open-area rule -------------------------------------------
    # A "3x3 open area" is a 3x3 block of cells whose 12 internal
    # passages are all open. 2x3 and 3x2 open rectangles are allowed.
    def _edge_open(self, ex: int, ey: int, edir: int,
                   override: Optional[_Edge]) -> bool:
        """Return whether canonical edge ``(ex, ey, edir)`` is open.

        Args:
            ex: Owner cell column.
            ey: Owner cell row.
            edir: Either :data:`E` or :data:`S`.
            override: An edge to treat as open regardless of its stored
                state, used to test a hypothetical carve.

        Returns:
            Whether the edge counts as open.
        """
        if override is not None and override == (ex, ey, edir):
            return True
        return self.is_open(ex, ey, edir)

    def _block_open(self, cx: int, cy: int,
                    override: Optional[_Edge] = None) -> bool:
        """Return whether the 3x3 block at ``(cx, cy)`` is fully open."""
        for yy in range(cy, cy + 3):
            for xx in range(cx, cx + 2):
                if not self._edge_open(xx, yy, E, override):
                    return False
        for yy in range(cy, cy + 2):
            for xx in range(cx, cx + 3):
                if not self._edge_open(xx, yy, S, override):
                    return False
        return True

    def has_any_3x3_open(self) -> bool:
        """Return whether any 3x3 fully-open block exists."""
        for cy in range(self.height - 2):
            for cx in range(self.width - 2):
                if self._block_open(cx, cy):
                    return True
        return False

    def _canonical_edge(self, x: int, y: int,
                        direction: int) -> Optional[_Edge]:
        """Return the top/left ``E``/``S`` name of an edge.

        Args:
            x: Cell column.
            y: Cell row.
            direction: Any of the four directions.

        Returns:
            The canonical edge, or ``None`` for a border wall.
        """
        dx, dy = DELTA[direction]
        nx, ny = x + dx, y + dy
        if not self.in_bounds(nx, ny):
            return None
        if direction == E:
            return (x, y, E)
        if direction == W:
            return (nx, ny, E)
        if direction == S:
            return (x, y, S)
        return (nx, ny, S)  # direction == N

    def would_form_3x3_open(self, x: int, y: int,
                            direction: int) -> bool:
        """Return whether opening this wall completes a 3x3 open block.

        Only the few 3x3 windows containing the edge are inspected, so
        the check is constant time.

        Args:
            x: Cell column.
            y: Cell row.
            direction: The wall to test.

        Returns:
            Whether carving here would break the no-3x3 rule.
        """
        edge = self._canonical_edge(x, y, direction)
        if edge is None:
            return False
        ex, ey, edir = edge
        if edir == E:
            cx_range = range(ex - 1, ex + 1)
            cy_range = range(ey - 2, ey + 1)
        else:  # edir == S
            cx_range = range(ex - 2, ex + 1)
            cy_range = range(ey - 1, ey + 1)
        for cy in cy_range:
            if cy < 0 or cy > self.height - 3:
                continue
            for cx in cx_range:
                if cx < 0 or cx > self.width - 3:
                    continue
                if self._block_open(cx, cy, override=edge):
                    return True
        return False

    # --- Convenience --------------------------------------------------
    def to_rows(self) -> Iterator[str]:
        """Yield one uppercase hex string per row, top row first."""
        for y in range(self.height):
            start = y * self.width
            row = self._cells[start:start + self.width]
            yield "".join("%X" % v for v in row)
