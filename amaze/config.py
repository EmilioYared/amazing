"""Parse and validate the A-Maze-ing configuration file.

The file is a ``KEY=VALUE`` text format (see ``config.txt``). Blank lines
and ``#`` comments are ignored, unknown keys are skipped, and a repeated
key takes its last value. This module does not depend on ``mazegen``.
"""

from dataclasses import dataclass
from typing import Optional

_MANDATORY = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")

#: Upper bound on ``WIDTH * HEIGHT``. Without it a huge size makes the
#: grid allocation raise ``MemoryError`` instead of a clear error.
_MAX_CELLS = 1_000_000


@dataclass
class Config:
    """Validated maze configuration.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: The ``(x, y)`` entry cell.
        exit: The ``(x, y)`` exit cell.
        output_file: Path the maze is written to.
        perfect: Whether the maze has exactly one entry->exit path.
        seed: Optional seed for reproducible generation.
        algorithm: Generation algorithm name.
        braid: Fraction of extra walls opened when not perfect.
        pattern: Whether to draw the hidden "42".
        display: Rendering mode.
    """

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int] = None
    algorithm: str = "backtracker"
    braid: float = 0.0
    pattern: bool = True
    display: str = "terminal"


class ConfigError(Exception):
    """Raised when the configuration file is missing or invalid."""


def _parse_bool(key: str, value: str) -> bool:
    """Parse ``true``/``false``, case-insensitively.

    Args:
        key: Key name, used in the error message.
        value: Raw text to parse.

    Returns:
        The parsed boolean.

    Raises:
        ConfigError: If the value is not a boolean.
    """
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ConfigError(
        f"{key} must be true or false, got: {value!r}"
    )


def _parse_positive_int(key: str, value: str) -> int:
    """Parse a strictly positive integer.

    Args:
        key: Key name, used in the error message.
        value: Raw text to parse.

    Returns:
        The parsed integer.

    Raises:
        ConfigError: If the value is not an integer above 0.
    """
    try:
        parsed = int(value.strip())
    except ValueError:
        raise ConfigError(
            f"{key} must be an integer, got: {value!r}"
        ) from None
    if parsed < 1:
        raise ConfigError(f"{key} must be >= 1, got: {parsed}")
    return parsed


def _parse_point(key: str, value: str) -> tuple[int, int]:
    """Parse an ``x,y`` pair.

    Args:
        key: Key name, used in the error message.
        value: Raw text to parse.

    Returns:
        The parsed ``(x, y)`` tuple.

    Raises:
        ConfigError: If the value is not two integers.
    """
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(
            f"{key} must be in 'x,y' form, got: {value!r}"
        )
    try:
        x = int(parts[0].strip())
        y = int(parts[1].strip())
    except ValueError:
        raise ConfigError(
            f"{key} must be two integers 'x,y', got: {value!r}"
        ) from None
    return (x, y)


def _parse_seed(value: str) -> Optional[int]:
    """Parse an optional integer seed.

    Args:
        value: Raw text; empty means unset.

    Returns:
        The seed, or ``None`` when unset.

    Raises:
        ConfigError: If a non-empty value is not an integer.
    """
    stripped = value.strip()
    if stripped == "":
        return None
    try:
        return int(stripped)
    except ValueError:
        raise ConfigError(
            f"SEED must be an integer, got: {value!r}"
        ) from None


def _parse_braid(value: str) -> float:
    """Parse a braid fraction in ``[0.0, 1.0]``.

    Args:
        value: Raw text to parse.

    Returns:
        The parsed fraction.

    Raises:
        ConfigError: If the value is not a number in range.
    """
    try:
        parsed = float(value.strip())
    except ValueError:
        raise ConfigError(
            f"BRAID must be a number, got: {value!r}"
        ) from None
    if not 0.0 <= parsed <= 1.0:
        raise ConfigError(
            f"BRAID must be within [0.0, 1.0], got: {parsed}"
        )
    return parsed


def _validate_point(
    key: str, point: tuple[int, int], width: int, height: int
) -> None:
    """Ensure ``point`` lies within the maze bounds.

    Args:
        key: Key name, used in the error message.
        point: The ``(x, y)`` cell to check.
        width: Maze width in cells.
        height: Maze height in cells.

    Raises:
        ConfigError: If the point is outside the grid.
    """
    x, y = point
    if not 0 <= x <= width - 1 or not 0 <= y <= height - 1:
        raise ConfigError(
            f"{key} {point} is out of bounds for a "
            f"{width}x{height} maze"
        )


def _read_pairs(path: str) -> dict[str, str]:
    """Read the file into an uppercase key -> value mapping.

    Args:
        path: Path to the configuration file.

    Returns:
        The parsed pairs, later keys overriding earlier ones.

    Raises:
        ConfigError: If the file is missing or a line has no ``=``.
    """
    pairs: dict[str, str] = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for lineno, raw in enumerate(handle, start=1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    raise ConfigError(
                        f"line {lineno}: expected KEY=VALUE, "
                        f"got: {line!r}"
                    )
                key, value = line.split("=", 1)
                pairs[key.strip().upper()] = value.strip()
    except FileNotFoundError:
        raise ConfigError(f"config file not found: {path}") from None
    return pairs


def load_config(path: str) -> Config:
    """Load, parse and validate the configuration at ``path``.

    Args:
        path: Path to the configuration file.

    Returns:
        The validated configuration.

    Raises:
        ConfigError: On a missing key, malformed value or failed
            validation.
    """
    pairs = _read_pairs(path)

    missing = [key for key in _MANDATORY if key not in pairs]
    if missing:
        raise ConfigError(
            "missing mandatory key(s): " + ", ".join(missing)
        )

    width = _parse_positive_int("WIDTH", pairs["WIDTH"])
    height = _parse_positive_int("HEIGHT", pairs["HEIGHT"])
    if width * height > _MAX_CELLS:
        raise ConfigError(
            f"WIDTH x HEIGHT must be at most {_MAX_CELLS} cells, got "
            f"{width * height} ({width}x{height})"
        )
    entry = _parse_point("ENTRY", pairs["ENTRY"])
    exit_ = _parse_point("EXIT", pairs["EXIT"])
    output_file = pairs["OUTPUT_FILE"]
    if output_file == "":
        raise ConfigError("OUTPUT_FILE must not be empty")
    perfect = _parse_bool("PERFECT", pairs["PERFECT"])

    seed = _parse_seed(pairs.get("SEED", ""))
    algorithm = pairs.get("ALGORITHM", "backtracker")
    braid = _parse_braid(pairs.get("BRAID", "0.0"))
    pattern = _parse_bool("PATTERN", pairs.get("PATTERN", "true"))
    display = pairs.get("DISPLAY", "terminal")

    _validate_point("ENTRY", entry, width, height)
    _validate_point("EXIT", exit_, width, height)
    if entry == exit_:
        raise ConfigError("ENTRY and EXIT must differ")

    return Config(
        width=width,
        height=height,
        entry=entry,
        exit=exit_,
        output_file=output_file,
        perfect=perfect,
        seed=seed,
        algorithm=algorithm,
        braid=braid,
        pattern=pattern,
        display=display,
    )
