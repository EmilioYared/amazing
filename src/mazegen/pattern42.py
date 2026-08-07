"""Hidden "42" glyph placement.

Computes the cells that must be fully closed so a "42" appears in the
finished maze. The glyph comes from a 3x5 pixel font -- the digit ``4``,
a blank spacer column, then the digit ``2`` -- giving a fixed 7x5 shape.
It is never scaled to the maze: a bigger grid gets the same "42" with
more margin around it.

Coordinates follow :mod:`mazegen.grid`: ``x`` grows right, ``y`` grows
downward.
"""

from __future__ import annotations

#: One 3x5 pixel block per digit (1 = blocked cell, 0 = empty).
_DIGIT_4: tuple[tuple[int, ...], ...] = (
    (1, 0, 1),
    (1, 0, 1),
    (1, 1, 1),
    (0, 0, 1),
    (0, 0, 1),
)
_DIGIT_2: tuple[tuple[int, ...], ...] = (
    (1, 1, 1),
    (0, 0, 1),
    (1, 1, 1),
    (1, 0, 0),
    (1, 1, 1),
)

#: The combined "4 2" glyph: ``4`` + one blank column + ``2``.
GLYPH: tuple[tuple[int, ...], ...] = tuple(
    four + (0,) + two for four, two in zip(_DIGIT_4, _DIGIT_2)
)

#: Fixed glyph dimensions in cells.
GLYPH_WIDTH: int = 7
GLYPH_HEIGHT: int = 5


class PatternTooSmallError(Exception):
    """Raised when a grid is too small to hold the "42" pattern."""


def min_dimensions() -> tuple[int, int]:
    """Return the smallest grid that fits the pattern.

    Returns:
        The minimum ``(width, height)``, always ``(9, 7)``: the glyph
        plus a one-cell margin on every side.
    """
    return (GLYPH_WIDTH + 2, GLYPH_HEIGHT + 2)


def fits(width: int, height: int) -> bool:
    """Return whether the grid can hold the pattern.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.

    Returns:
        Whether both dimensions clear :func:`min_dimensions`.
    """
    min_w, min_h = min_dimensions()
    return width >= min_w and height >= min_h


def blocked_cells(width: int, height: int) -> set[tuple[int, int]]:
    """Return the interior cells that spell out a centred "42".

    Each font pixel becomes one blocked cell. The glyph is centred so a
    one-cell margin remains on every side.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.

    Returns:
        The blocked ``(x, y)`` cells, or an empty set when the grid is
        too small, so the caller can report it and omit the pattern.
    """
    if not fits(width, height):
        return set()
    ox = (width - GLYPH_WIDTH) // 2
    oy = (height - GLYPH_HEIGHT) // 2
    return {
        (ox + col, oy + row)
        for row, pixels in enumerate(GLYPH)
        for col, pixel in enumerate(pixels)
        if pixel
    }
