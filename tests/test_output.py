"""Tests for :mod:`amaze.output` (output-file formatting and writing).

The expectations are rebuilt from ``Maze.to_rows()`` so the assertions
track the shared grid contract rather than hard-coded hex strings.
"""

from pathlib import Path

from amaze.output import format_output, write_output
from mazegen.grid import E, S, Maze

_ENTRY: tuple[int, int] = (0, 0)
_EXIT: tuple[int, int] = (2, 1)
_MOVES: list[str] = ["E", "E", "S"]


def _sample_maze() -> Maze:
    """Return a small 3x2 maze with a couple of carved passages."""
    maze = Maze(3, 2)
    maze.carve(0, 0, E)
    maze.carve(0, 0, S)
    return maze


def _expected(maze: Maze) -> str:
    """Build the expected file content directly from ``to_rows()``."""
    rows = list(maze.to_rows())
    parts = rows + ["", "0,0", "2,1", "EES"]
    return "".join(f"{part}\n" for part in parts)


def test_format_output_exact_string() -> None:
    """format_output reproduces the exact specified file content."""
    maze = _sample_maze()
    result = format_output(maze, _ENTRY, _EXIT, _MOVES)
    assert result == _expected(maze)


def test_structure_h_hex_lines_blank_then_three() -> None:
    """H hex lines, one blank line, then exactly three trailing lines."""
    maze = _sample_maze()
    content = format_output(maze, _ENTRY, _EXIT, _MOVES)
    lines = content.split("\n")
    assert lines[-1] == ""  # trailing newline -> empty final element
    lines = lines[:-1]
    height = maze.height
    assert len(lines) == height + 4  # H hex + blank + 3
    for row in lines[:height]:
        assert len(row) == maze.width
        assert all(ch in "0123456789ABCDEF" for ch in row)
    assert lines[height] == ""
    assert lines[height + 1] == "0,0"
    assert lines[height + 2] == "2,1"
    assert lines[height + 3] == "EES"


def test_every_line_ends_with_lf_and_no_cr() -> None:
    """Every line ends with a line-feed and no carriage return exists."""
    maze = _sample_maze()
    content = format_output(maze, _ENTRY, _EXIT, _MOVES)
    assert "\r" not in content
    for line in content.splitlines(keepends=True):
        assert line.endswith("\n")


def test_first_hex_row_matches_walls() -> None:
    """Each digit of the first hex row equals maze.walls() there."""
    maze = _sample_maze()
    content = format_output(maze, _ENTRY, _EXIT, _MOVES)
    first_row = content.split("\n")[0]
    for x, digit in enumerate(first_row):
        assert int(digit, 16) == maze.walls(x, 0)


def test_empty_path_when_entry_equals_exit() -> None:
    """The path line is empty when the entry equals the exit."""
    maze = _sample_maze()
    content = format_output(maze, (1, 1), (1, 1), [])
    lines = content.split("\n")
    assert lines[-1] == ""  # trailing newline
    assert lines[-2] == ""  # empty path line
    assert lines[-3] == "1,1"  # exit line


def test_write_output_byte_identical(tmp_path: Path) -> None:
    """write_output writes bytes identical to format_output (LF only)."""
    maze = _sample_maze()
    target = tmp_path / "maze.txt"
    write_output(str(target), maze, _ENTRY, _EXIT, _MOVES)
    expected = format_output(maze, _ENTRY, _EXIT, _MOVES)
    raw = target.read_bytes()
    assert raw == expected.encode("ascii")
    assert b"\r" not in raw
