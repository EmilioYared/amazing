"""Serialize a generated maze to the A-Maze-ing output-file format.

The on-disk format (in order) is:

1. ``H`` lines, each the row's wall digits as uppercase hex with no
   separators, top row (``y == 0``) first.
2. One blank line.
3. ``<entry_x>,<entry_y>``.
4. ``<exit_x>,<exit_y>``.
5. The shortest-path solution as concatenated move letters (for
   example ``"EESSW"``); empty when the entry equals the exit.

Every line -- including the blank line and the final path line -- is
terminated by a single line-feed newline; carriage returns are never
emitted.
"""

from mazegen.grid import Maze


def format_output(
    maze: Maze,
    entry: tuple[int, int],
    exit: tuple[int, int],
    path_moves: list[str],
) -> str:
    """Return the exact output-file content for ``maze``.

    Args:
        maze: The maze whose rows supply the hex wall digits.
        entry: The ``(x, y)`` entry cell.
        exit: The ``(x, y)`` exit cell.
        path_moves: Solution moves (``"N"``/``"E"``/``"S"``/``"W"``),
            joined without separators; pass an empty list when the
            entry equals the exit.

    Returns:
        The full file content, every line terminated by a line-feed
        newline.
    """
    lines: list[str] = list(maze.to_rows())
    lines.append("")
    lines.append(f"{entry[0]},{entry[1]}")
    lines.append(f"{exit[0]},{exit[1]}")
    lines.append("".join(path_moves))
    return "".join(f"{line}\n" for line in lines)


def write_output(
    path: str,
    maze: Maze,
    entry: tuple[int, int],
    exit: tuple[int, int],
    path_moves: list[str],
) -> None:
    """Write the formatted maze output to ``path``.

    The file is opened in text mode with newline translation disabled
    (line-feed only) and ASCII encoding, so its bytes match
    :func:`format_output` exactly on every platform.

    Args:
        path: Filesystem path of the output file to (over)write.
        maze: The maze to serialize.
        entry: The ``(x, y)`` entry cell.
        exit: The ``(x, y)`` exit cell.
        path_moves: Solution moves passed to :func:`format_output`.

    Raises:
        OSError: If the file cannot be opened or written; propagated
            unchanged for the CLI layer to handle.
    """
    content = format_output(maze, entry, exit, path_moves)
    with open(path, "w", newline="\n", encoding="ascii") as handle:
        handle.write(content)
