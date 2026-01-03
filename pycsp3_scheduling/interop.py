"""
Interop helpers to build pycsp3 expressions from IntervalVar.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

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


@dataclass(frozen=True)
class IntervalValue(Mapping[str, int | bool]):
    """Solved interval values with dict-like and attribute access."""

    start: int
    length: int
    present: bool = True

    @property
    def end(self) -> int:
        """End time of the interval."""
        return self.start + self.length

    def __getitem__(self, key: str) -> int | bool:
        if key == "start":
            return self.start
        if key == "end":
            return self.end
        if key == "length":
            return self.length
        if key == "present":
            return self.present
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        yield from ("start", "end", "length", "present")

    def __len__(self) -> int:
        return 4

    def __repr__(self) -> str:
        return (
            "IntervalValue(start="
            f"{self.start}, end={self.end}, length={self.length}, present={self.present})"
        )

    def to_dict(self) -> dict[str, int | bool]:
        """Return a plain dict representation."""
        return {
            "start": self.start,
            "end": self.end,
            "length": self.length,
            "present": self.present,
        }


def interval_value(interval: IntervalVar) -> IntervalValue | None:
    """
    Extract the solution values for an interval after solving.
    
    Returns an IntervalValue with 'start', 'end', 'length', 'present' fields,
    or None if the interval is absent (for optional intervals).
    
    Args:
        interval: The interval variable to extract values from.
        
    Returns:
        IntervalValue with start/end/length/present values, or None if absent.
        
    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # ... add constraints and solve ...
        >>> vals = interval_value(task)
        >>> print(f"start={vals.start}, end={vals.end}")
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

    return IntervalValue(start=start, length=length, present=True)
