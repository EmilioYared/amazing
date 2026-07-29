"""Tests for :mod:`amaze.config`."""

from pathlib import Path

import pytest

from amaze.config import Config, ConfigError, load_config

_FULL = """\
# comment line
WIDTH=20
HEIGHT=15

ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
ALGORITHM=backtracker
BRAID=0.15
PATTERN=True
DISPLAY=terminal
"""


def _write(tmp_path: Path, text: str) -> str:
    """Write ``text`` to a temp config file and return its path."""
    target = tmp_path / "config.txt"
    target.write_text(text, encoding="utf-8")
    return str(target)


def test_valid_full_config(tmp_path: Path) -> None:
    """A complete config parses into the expected Config."""
    cfg = load_config(_write(tmp_path, _FULL))
    assert cfg == Config(
        width=20,
        height=15,
        entry=(0, 0),
        exit=(19, 14),
        output_file="maze.txt",
        perfect=True,
        seed=42,
        algorithm="backtracker",
        braid=0.15,
        pattern=True,
        display="terminal",
    )


def test_optional_defaults(tmp_path: Path) -> None:
    """Omitting optional keys yields their defaults."""
    text = (
        "WIDTH=5\nHEIGHT=5\nENTRY=0,0\nEXIT=4,4\n"
        "OUTPUT_FILE=out.txt\nPERFECT=False\n"
    )
    cfg = load_config(_write(tmp_path, text))
    assert cfg.seed is None
    assert cfg.algorithm == "backtracker"
    assert cfg.braid == 0.0
    assert cfg.pattern is True
    assert cfg.display == "terminal"


def test_comments_and_blank_lines_ignored(tmp_path: Path) -> None:
    """Blank lines and ``#`` comments do not affect parsing."""
    text = (
        "# header\n\n   \nWIDTH=3\n# mid\nHEIGHT=3\n"
        "ENTRY=0,0\nEXIT=2,2\nOUTPUT_FILE=m.txt\nPERFECT=True\n"
    )
    cfg = load_config(_write(tmp_path, text))
    assert cfg.width == 3
    assert cfg.height == 3


def test_case_insensitive_keys(tmp_path: Path) -> None:
    """Keys are matched case-insensitively."""
    text = (
        "width=4\nHeIgHt=4\nentry=0,0\nExit=3,3\n"
        "output_file=m.txt\nperfect=true\n"
    )
    cfg = load_config(_write(tmp_path, text))
    assert cfg.width == 4
    assert cfg.perfect is True


def test_unknown_keys_ignored(tmp_path: Path) -> None:
    """Extra unknown keys are silently ignored."""
    text = _FULL + "MYSTERY=42\nEXTRA=hello\n"
    cfg = load_config(_write(tmp_path, text))
    assert cfg.width == 20


@pytest.mark.parametrize("key", list(
    ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")
))
def test_missing_mandatory_key(tmp_path: Path, key: str) -> None:
    """Each missing mandatory key raises ConfigError."""
    lines = [
        line for line in _FULL.splitlines()
        if not line.upper().startswith(key + "=")
    ]
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, "\n".join(lines) + "\n"))
    assert key in str(exc.value)


def test_file_not_found(tmp_path: Path) -> None:
    """A missing file raises ConfigError, not FileNotFoundError."""
    missing = str(tmp_path / "does_not_exist.txt")
    with pytest.raises(ConfigError) as exc:
        load_config(missing)
    assert "not found" in str(exc.value)


def test_line_without_equals(tmp_path: Path) -> None:
    """A non-comment line lacking ``=`` raises ConfigError."""
    text = _FULL + "this line has no equals sign\n"
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, text))
    assert "KEY=VALUE" in str(exc.value)


def test_malformed_entry(tmp_path: Path) -> None:
    """A malformed ENTRY value raises ConfigError."""
    text = _FULL.replace("ENTRY=0,0", "ENTRY=0")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_entry_out_of_bounds(tmp_path: Path) -> None:
    """An out-of-bounds ENTRY raises ConfigError."""
    text = _FULL.replace("ENTRY=0,0", "ENTRY=99,0")
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, text))
    assert "out of bounds" in str(exc.value)


def test_entry_equals_exit(tmp_path: Path) -> None:
    """ENTRY equal to EXIT raises ConfigError."""
    text = _FULL.replace("EXIT=19,14", "EXIT=0,0")
    with pytest.raises(ConfigError) as exc:
        load_config(_write(tmp_path, text))
    assert "differ" in str(exc.value)


def test_non_positive_width(tmp_path: Path) -> None:
    """A width below 1 raises ConfigError."""
    text = _FULL.replace("WIDTH=20", "WIDTH=0")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


@pytest.mark.parametrize(
    "raw, expected",
    [("True", True), ("False", False), ("true", True), ("false", False)],
)
def test_perfect_bool_parsing(
    tmp_path: Path, raw: str, expected: bool
) -> None:
    """PERFECT accepts True/False/true/false."""
    text = _FULL.replace("PERFECT=True", f"PERFECT={raw}")
    cfg = load_config(_write(tmp_path, text))
    assert cfg.perfect is expected


def test_perfect_invalid(tmp_path: Path) -> None:
    """A non-boolean PERFECT value raises ConfigError."""
    text = _FULL.replace("PERFECT=True", "PERFECT=maybe")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


@pytest.mark.parametrize("value", ["-0.1", "1.5", "abc"])
def test_braid_out_of_range(tmp_path: Path, value: str) -> None:
    """A BRAID outside [0.0, 1.0] or non-numeric raises ConfigError."""
    text = _FULL.replace("BRAID=0.15", f"BRAID={value}")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))


def test_seed_invalid(tmp_path: Path) -> None:
    """A non-integer SEED raises ConfigError."""
    text = _FULL.replace("SEED=42", "SEED=notanint")
    with pytest.raises(ConfigError):
        load_config(_write(tmp_path, text))
