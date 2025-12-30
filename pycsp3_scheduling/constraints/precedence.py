"""
Precedence constraints for interval variables.
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import length_value, start_var
from pycsp3_scheduling.variables.interval import IntervalVar


def end_before_start(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval a ends before interval b starts.

    Semantics (when both present):
        start(b) >= start(a) + length(a) + delay
    """
    if not isinstance(a, IntervalVar) or not isinstance(b, IntervalVar):
        raise TypeError("end_before_start expects IntervalVar inputs")
    if not isinstance(delay, int):
        raise TypeError("delay must be an int")
    start_a = start_var(a)
    start_b = start_var(b)
    duration_a = length_value(a)
    return start_a + duration_a + delay <= start_b
