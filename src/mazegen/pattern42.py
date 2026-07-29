"""Hidden "42" glyph placement for the maze generator.

This module computes the set of grid cells that must be fully closed
(walled off) so that a hidden "42" appears in the finished maze. The
glyph is drawn from a compact 3x5 pixel font: the digit ``4``, a single
blank spacer column, and the digit ``2`` -- a combined shape 7 cells
wide and 5 cells tall. The glyph can be scaled up by an integer factor
and is always centred inside the grid with a one-cell margin so the
default entry/exit corners stay clear.

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

#: Unscaled glyph dimensions in cells.
GLYPH_WIDTH: int = 7
GLYPH_HEIGHT: int = 5


class PatternTooSmallError(Exception):
    """Raised when a grid is too small to hold the "42" pattern."""


def min_dimensions(scale: int = 1) -> tuple[int, int]:
    """Return the minimum ``(width, height)`` for the pattern.

    The scaled glyph occupies ``7 * scale`` by ``5 * scale`` cells, plus
    a one-cell margin on every side so the pattern never touches the
    outer border.

    Args:
        scale: Positive integer magnification factor.

    Returns:
        The minimum ``(width, height)`` in cells.

    Raises:
        ValueError: If ``scale`` is less than 1.
    """
    if scale < 1:
        raise ValueError("scale must be >= 1")
    return (GLYPH_WIDTH * scale + 2, GLYPH_HEIGHT * scale + 2)


def fits(width: int, height: int, scale: int = 1) -> bool:
    """Return ``True`` if the grid can hold the scaled pattern.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.
        scale: Positive integer magnification factor.

    Raises:
        ValueError: If ``scale`` is less than 1.
    """
    min_w, min_h = min_dimensions(scale)
    return width >= min_w and height >= min_h


def blocked_cells(
    width: int, height: int, scale: int = 1
) -> set[tuple[int, int]]:
    """Return the interior cells that spell out a centred "42".

    Each font pixel set to ``1`` expands to a ``scale`` x ``scale`` block
    of blocked cells. The glyph is centred so a one-cell margin remains
    on every side, keeping all returned cells strictly interior.

    If the grid is smaller than :func:`min_dimensions` for ``scale``, an
    empty set is returned so the caller can print the mandated "too
    small" message and simply omit the pattern.

    Args:
        width: Grid width in cells.
        height: Grid height in cells.
        scale: Positive integer magnification factor.

    Returns:
        The set of blocked ``(x, y)`` cells (possibly empty).

    Raises:
        ValueError: If ``scale`` is less than 1.
    """
    if not fits(width, height, scale):
        return set()
    ox = (width - GLYPH_WIDTH * scale) // 2
    oy = (height - GLYPH_HEIGHT * scale) // 2
    cells: set[tuple[int, int]] = set()
    for row, pixels in enumerate(GLYPH):
        for col, pixel in enumerate(pixels):
            if not pixel:
                continue
            base_x = ox + col * scale
            base_y = oy + row * scale
            for i in range(scale):
                for j in range(scale):
                    cells.add((base_x + i, base_y + j))
    return cells
