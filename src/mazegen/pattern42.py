"""Hidden "42" glyph placement for the maze generator.

This module computes the set of grid cells that must be fully closed
(walled off) so that a hidden "42" appears in the finished maze. The
glyph is drawn from a compact 3x5 pixel font: the digit ``4``, a single
blank spacer column, and the digit ``2`` -- a combined shape 7 cells
wide and 5 cells tall. The glyph is always drawn at that fixed size --
one cell per font pixel, never scaled to the maze -- and is centred
inside the grid with a one-cell margin so the default entry/exit corners
stay clear. A bigger maze therefore holds the same "42", not a bigger
one.

Coordinates use the same convention as :mod:`mazegen.grid`: ``x`` grows
to the right and ``y`` grows downward, with the interior of a
``width`` x ``height`` grid spanning ``1 <= x <= width - 2`` and
``1 <= y <= height - 2``.
"""

from __future__ import annotations

#: One 3x5 pixel row block per digit (1 = blocked cell, 0 = empty).
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
    """Return the minimum ``(width, height)`` for the pattern.

    The glyph occupies :data:`GLYPH_WIDTH` by :data:`GLYPH_HEIGHT` cells,
    plus a one-cell margin on every side so the pattern never touches the
    outer border.

    Returns:
        The minimum ``(width, height)`` in cells -- always ``(9, 7)``.
    """
    return (GLYPH_WIDTH + 2, GLYPH_HEIGHT + 2)


def fits(width: int, height: int) -> bool:
    """Return ``True`` if the grid can hold the pattern.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.
    """
    min_w, min_h = min_dimensions()
    return width >= min_w and height >= min_h


def blocked_cells(width: int, height: int) -> set[tuple[int, int]]:
    """Return the interior cells that spell out a centred "42".

    Each font pixel set to ``1`` becomes exactly one blocked cell, so the
    glyph is always :data:`GLYPH_WIDTH` x :data:`GLYPH_HEIGHT` cells
    whatever the maze size. It is centred so a one-cell margin remains on
    every side, keeping all returned cells strictly interior.

    If the grid is smaller than :func:`min_dimensions`, an empty set is
    returned so the caller can print the mandated "too small" message and
    simply omit the pattern.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.

    Returns:
        The set of blocked ``(x, y)`` cells (possibly empty).
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
