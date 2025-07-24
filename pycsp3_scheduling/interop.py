"""
Interop helpers to build pycsp3 expressions from IntervalVar.
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import length_value, presence_var, start_var
from pycsp3_scheduling.variables.interval import IntervalVar


def start_time(interval: IntervalVar):
    """Return a pycsp3 variable representing the start time."""
    if not isinstance(interval, IntervalVar):
        raise TypeError("start_time expects an IntervalVar")
    return start_var(interval)


def end_time(interval: IntervalVar):
    """Return a pycsp3 expression representing the end time (start + length)."""
    if not isinstance(interval, IntervalVar):
        raise TypeError("end_time expects an IntervalVar")
    return start_var(interval) + length_value(interval)


def presence_time(interval: IntervalVar):
    """Return a pycsp3 variable representing presence (0/1) for optional intervals."""
    if not isinstance(interval, IntervalVar):
        raise TypeError("presence_time expects an IntervalVar")
    return presence_var(interval)


def interval_value(interval: IntervalVar) -> dict | None:
    """
    Extract the solution values for an interval after solving.
    
    Returns a dict with 'start', 'end', 'length', 'present' keys,
    or None if the interval is absent (for optional intervals).
    
    Args:
        interval: The interval variable to extract values from.
        
    Returns:
        Dict with start/end/length/present values, or None if absent.
        
    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # ... add constraints and solve ...
        >>> vals = interval_value(task)
        >>> print(f"start={vals['start']}, end={vals['end']}")
    """
    from pycsp3 import value
    
    if not isinstance(interval, IntervalVar):
        raise TypeError("interval_value expects an IntervalVar")
    
    # Check presence for optional intervals
    if interval.optional:
        pres = presence_var(interval)
        if value(pres) == 0:
            return None
    
    start = value(start_var(interval))
    length_val = length_value(interval)
    if isinstance(length_val, int):
        length = length_val
    else:
        length = value(length_val)
    
    return {
        'start': start,
        'end': start + length,
        'length': length,
        'present': True,
    }
