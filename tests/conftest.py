"""Pytest configuration for pycsp3-scheduling tests."""

from __future__ import annotations

import sys


def _disable_pycsp3_compile() -> None:
    """Prevent pycsp3 from compiling on import during tests."""
    if sys.argv and sys.argv[-1] != "-nocompile":
        sys.argv.append("-nocompile")


_disable_pycsp3_compile()
