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


def test_min_dimensions_scale_1_and_2() -> None:
    """Minimum dimensions match the documented scaled sizes."""
    assert min_dimensions(1) == (9, 7)
    assert min_dimensions(2) == (16, 12)


def test_min_dimensions_rejects_bad_scale() -> None:
    """A scale below 1 is a programmer error."""
    for bad in (0, -1, -5):
        try:
            min_dimensions(bad)
        except ValueError:
            continue
        raise AssertionError("expected ValueError for scale < 1")


def test_blocked_cells_in_bounds_and_interior() -> None:
    """Every blocked cell is strictly interior and correctly sized."""
    width, height, scale = 9, 7, 1
    cells = blocked_cells(width, height, scale)
    assert cells
    assert len(cells) == _pixel_count() * scale ** 2
    for x, y in cells:
        assert 1 <= x <= width - 2
        assert 1 <= y <= height - 2


def test_blocked_cells_scaled_size() -> None:
    """Scaling multiplies the blocked cell count by ``scale**2``."""
    scale = 2
    width, height = min_dimensions(scale)
    cells = blocked_cells(width, height, scale)
    assert len(cells) == _pixel_count() * scale ** 2
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
    width, height, scale = 9, 7, 1
    cells = blocked_cells(width, height, scale)
    grid = [["." for _ in range(width)] for _ in range(height)]
    for x, y in cells:
        grid[y][x] = "#"
    ox = (width - 7 * scale) // 2  # == 1
    oy = (height - 5 * scale) // 2  # == 1
    # Top-left pixel of the "4" (glyph col 0, row 0) is blocked.
    assert grid[oy + 0][ox + 0] == "#"
    # Spacer column (glyph col 3) is always empty.
    assert grid[oy + 0][ox + 3] == "."
    # Top of the "2" (glyph col 4, row 0) is blocked.
    assert grid[oy + 0][ox + 4] == "#"
    # Middle of the "4" (glyph col 1, row 1) is empty.
    assert grid[oy + 1][ox + 1] == "."
