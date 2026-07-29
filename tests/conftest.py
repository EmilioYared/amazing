"""Pytest path setup.

Makes both the ``mazegen`` package (under ``src/``) and the application
``amaze`` package (at the project root) importable from tests without an
editable install.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)
