"""
Interop helpers to build pycsp3 expressions from IntervalVar.
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import length_value, start_var
from pycsp3_scheduling.variables.interval import IntervalVar


def start_time(interval: IntervalVar):
    """Return a pycsp3 variable representing the start time."""
    if not isinstance(interval, IntervalVar):
        raise TypeError("start_time expects an IntervalVar")
    return start_var(interval)


def end_time(interval: IntervalVar):
    """Return a pycsp3 expression representing the end time."""
    if not isinstance(interval, IntervalVar):
        raise TypeError("end_time expects an IntervalVar")
    return start_var(interval) + length_value(interval)
