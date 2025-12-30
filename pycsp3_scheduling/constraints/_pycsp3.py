"""
Helpers for bridging IntervalVar objects to pycsp3 variables.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pycsp3_scheduling.variables.interval import (
    INTERVAL_MAX,
    INTERVAL_MIN,
    IntervalVar,
    get_registered_intervals,
)

if TYPE_CHECKING:
    from pycsp3.classes.main.variables import Variable

_start_vars: dict[IntervalVar, Any] = {}
_length_vars: dict[IntervalVar, Any] = {}


def _var_id(prefix: str, interval: IntervalVar) -> str:
    return f"{prefix}{interval._id}"


def _default_horizon(intervals: list[IntervalVar]) -> int:
    horizon = 0
    for interval in intervals:
        if interval.end_max != INTERVAL_MAX:
            horizon = max(horizon, interval.end_max)
        elif interval.start_max != INTERVAL_MAX:
            horizon = max(horizon, interval.start_max + interval.length_max)
        else:
            horizon += interval.length_max
    return max(horizon, 0)


def _range_from_bounds(min_val: int, max_val: int, horizon: int) -> range:
    if max_val == INTERVAL_MAX:
        max_val = horizon
    if max_val < min_val:
        max_val = min_val
    return range(min_val, max_val + 1)


def _require_pycsp3():
    try:
        from pycsp3 import Var
        from pycsp3.classes.main.variables import Variable
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise ImportError(
            "pycsp3 is required to build scheduling constraints. "
            "Install a compatible version and Python runtime."
        ) from exc
    return Var, Variable


def start_var(interval: IntervalVar) -> Any:
    """Return (or create) a pycsp3 variable for the interval start time."""
    if interval.optional:
        raise NotImplementedError("Optional intervals are not supported yet.")
    if interval in _start_vars:
        return _start_vars[interval]
    Var, _ = _require_pycsp3()
    intervals = get_registered_intervals() or [interval]
    horizon = _default_horizon(intervals)
    dom = _range_from_bounds(interval.start_min, interval.start_max, horizon)
    var = Var(dom=dom, id=_var_id("iv_s_", interval))
    _start_vars[interval] = var
    return var


def length_value(interval: IntervalVar) -> Any:
    """Return a fixed length or a pycsp3 variable for interval length."""
    if interval.length_min == interval.length_max:
        return interval.length_min
    if interval in _length_vars:
        return _length_vars[interval]
    Var, _ = _require_pycsp3()
    dom = range(interval.length_min, interval.length_max + 1)
    var = Var(dom=dom, id=_var_id("iv_l_", interval))
    _length_vars[interval] = var
    return var


def clear_pycsp3_cache() -> None:
    """Clear cached pycsp3 variables for intervals."""
    _start_vars.clear()
    _length_vars.clear()
