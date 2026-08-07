"""Write a generated maze to the A-Maze-ing output file format.

The file holds one line of hex wall digits per maze row (top row first),
a blank line, then the entry, the exit and the solution moves. Every
line ends with a single ``\\n``.
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
        maze: The maze supplying the hex wall digits.
        entry: The ``(x, y)`` entry cell.
        exit: The ``(x, y)`` exit cell.
        path_moves: Solution moves, joined without separators.

    Returns:
        The full file content, every line newline-terminated.
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
    """Write the formatted maze to ``path``.

    Opened with newline translation disabled and ASCII encoding, so the
    bytes match :func:`format_output` on every platform.

    Args:
        path: File to (over)write.
        maze: The maze to serialize.
        entry: The ``(x, y)`` entry cell.
        exit: The ``(x, y)`` exit cell.
        path_moves: Solution moves.

    Raises:
        OSError: If the file cannot be opened or written.
    """
    content = format_output(maze, entry, exit, path_moves)
    with open(path, "w", newline="\n", encoding="ascii") as handle:
        handle.write(content)
