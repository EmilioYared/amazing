"""Tests for the hidden "42" pattern placement."""

from __future__ import annotations

from mazegen.pattern42 import (
    GLYPH,
    PatternTooSmallError,
    blocked_cells,
    fits,
    min_dimensions,
)


def _pixel_count() -> int:
    """Return the number of ``1`` pixels in the glyph."""
    return sum(sum(row) for row in GLYPH)


def test_min_dimensions_is_fixed() -> None:
    """The glyph plus its one-cell margin always needs a 9x7 grid."""
    assert min_dimensions() == (9, 7)


def test_blocked_cells_in_bounds_and_interior() -> None:
    """Every blocked cell is strictly interior and correctly sized."""
    width, height = 9, 7
    cells = blocked_cells(width, height)
    assert cells
    assert len(cells) == _pixel_count()
    for x, y in cells:
        assert 1 <= x <= width - 2
        assert 1 <= y <= height - 2


def test_glyph_size_never_scales_with_the_maze() -> None:
    """A bigger maze holds the same "42", not a bigger one."""
    for width, height in ((9, 7), (20, 15), (50, 50), (200, 200)):
        cells = blocked_cells(width, height)
        assert len(cells) == _pixel_count()
        xs = {x for x, _ in cells}
        ys = {y for _, y in cells}
        assert max(xs) - min(xs) + 1 == 7
        assert max(ys) - min(ys) + 1 == 5
        for x, y in cells:
            assert 1 <= x <= width - 2
            assert 1 <= y <= height - 2


def test_too_small_grid_returns_empty_set() -> None:
    """A grid below the minimum yields an empty set, not an error."""
    assert blocked_cells(8, 6) == set()
    assert blocked_cells(9, 6) == set()
    assert blocked_cells(8, 7) == set()


def test_corners_are_never_blocked() -> None:
    """Entry/exit corners stay clear for the default carve."""
    width, height = 9, 7
    cells = blocked_cells(width, height)
    assert (0, 0) not in cells
    assert (width - 1, height - 1) not in cells


def test_fits_and_error_class() -> None:
    """``fits`` mirrors ``min_dimensions`` and the error is an Exception."""
    assert fits(9, 7) is True
    assert fits(8, 7) is False
    assert fits(9, 6) is False
    assert issubclass(PatternTooSmallError, Exception)


def test_projection_renders_known_glyph_cells() -> None:
    """Rendering onto a '#/.' grid shows the expected glyph pixels."""
    width, height = 9, 7
    cells = blocked_cells(width, height)
    grid = [["." for _ in range(width)] for _ in range(height)]
    for x, y in cells:
        grid[y][x] = "#"
    ox = (width - 7) // 2  # == 1
    oy = (height - 5) // 2  # == 1
    # Top-left pixel of the "4" (glyph col 0, row 0) is blocked.
    assert grid[oy + 0][ox + 0] == "#"
    # Spacer column (glyph col 3) is always empty.
    assert grid[oy + 0][ox + 3] == "."
    # Top of the "2" (glyph col 4, row 0) is blocked.
    assert grid[oy + 0][ox + 4] == "#"
    # Middle of the "4" (glyph col 1, row 1) is empty.
    assert grid[oy + 1][ox + 1] == "."
