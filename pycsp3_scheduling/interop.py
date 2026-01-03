"""
Interop helpers to build pycsp3 expressions from IntervalVar.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True)
class ModelStatistics(Mapping[str, int]):
    """Statistics about the scheduling model."""

    nb_interval_vars: int
    nb_optional_interval_vars: int
    nb_sequences: int
    nb_sequences_with_types: int
    nb_cumul_functions: int
    nb_state_functions: int

    def __getitem__(self, key: str) -> int:
        if key == "nb_interval_vars":
            return self.nb_interval_vars
        if key == "nb_optional_interval_vars":
            return self.nb_optional_interval_vars
        if key == "nb_sequences":
            return self.nb_sequences
        if key == "nb_sequences_with_types":
            return self.nb_sequences_with_types
        if key == "nb_cumul_functions":
            return self.nb_cumul_functions
        if key == "nb_state_functions":
            return self.nb_state_functions
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        yield from (
            "nb_interval_vars",
            "nb_optional_interval_vars",
            "nb_sequences",
            "nb_sequences_with_types",
            "nb_cumul_functions",
            "nb_state_functions",
        )

    def __len__(self) -> int:
        return 6

    def __repr__(self) -> str:
        return (
            "ModelStatistics("
            f"nb_interval_vars={self.nb_interval_vars}, "
            f"nb_optional_interval_vars={self.nb_optional_interval_vars}, "
            f"nb_sequences={self.nb_sequences}, "
            f"nb_sequences_with_types={self.nb_sequences_with_types}, "
            f"nb_cumul_functions={self.nb_cumul_functions}, "
            f"nb_state_functions={self.nb_state_functions})"
        )

    def to_dict(self) -> dict[str, int]:
        """Return a plain dict representation."""
        return {
            "nb_interval_vars": self.nb_interval_vars,
            "nb_optional_interval_vars": self.nb_optional_interval_vars,
            "nb_sequences": self.nb_sequences,
            "nb_sequences_with_types": self.nb_sequences_with_types,
            "nb_cumul_functions": self.nb_cumul_functions,
            "nb_state_functions": self.nb_state_functions,
        }


@dataclass(frozen=True)
class SolutionStatistics(Mapping[str, object]):
    """Statistics about the solved schedule."""

    status: object | None
    objective_value: int | float | None
    solve_time: float | None
    nb_interval_vars: int
    nb_intervals_present: int
    nb_intervals_absent: int
    min_start: int | None
    max_end: int | None
    makespan: int | None
    span: int | None

    def __getitem__(self, key: str) -> object:
        if key == "status":
            return self.status
        if key == "objective_value":
            return self.objective_value
        if key == "solve_time":
            return self.solve_time
        if key == "nb_interval_vars":
            return self.nb_interval_vars
        if key == "nb_intervals_present":
            return self.nb_intervals_present
        if key == "nb_intervals_absent":
            return self.nb_intervals_absent
        if key == "min_start":
            return self.min_start
        if key == "max_end":
            return self.max_end
        if key == "makespan":
            return self.makespan
        if key == "span":
            return self.span
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        yield from (
            "status",
            "objective_value",
            "solve_time",
            "nb_interval_vars",
            "nb_intervals_present",
            "nb_intervals_absent",
            "min_start",
            "max_end",
            "makespan",
            "span",
        )

    def __len__(self) -> int:
        return 10

    def __repr__(self) -> str:
        return (
            "SolutionStatistics("
            f"status={self.status}, "
            f"objective_value={self.objective_value}, "
            f"solve_time={self.solve_time}, "
            f"nb_interval_vars={self.nb_interval_vars}, "
            f"nb_intervals_present={self.nb_intervals_present}, "
            f"nb_intervals_absent={self.nb_intervals_absent}, "
            f"min_start={self.min_start}, "
            f"max_end={self.max_end}, "
            f"makespan={self.makespan}, "
            f"span={self.span})"
        )

    def to_dict(self) -> dict[str, object]:
        """Return a plain dict representation."""
        return {
            "status": self.status,
            "objective_value": self.objective_value,
            "solve_time": self.solve_time,
            "nb_interval_vars": self.nb_interval_vars,
            "nb_intervals_present": self.nb_intervals_present,
            "nb_intervals_absent": self.nb_intervals_absent,
            "min_start": self.min_start,
            "max_end": self.max_end,
            "makespan": self.makespan,
            "span": self.span,
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


def model_statistics() -> ModelStatistics:
    """Return statistics about the current scheduling model."""
    from pycsp3_scheduling.functions.cumul_functions import get_registered_cumuls
    from pycsp3_scheduling.functions.state_functions import (
        get_registered_state_functions,
    )
    from pycsp3_scheduling.variables.interval import get_registered_intervals
    from pycsp3_scheduling.variables.sequence import get_registered_sequences

    intervals = get_registered_intervals()
    sequences = get_registered_sequences()
    nb_optional = sum(1 for interval in intervals if interval.optional)
    nb_typed_sequences = sum(1 for seq in sequences if seq.has_types)

    return ModelStatistics(
        nb_interval_vars=len(intervals),
        nb_optional_interval_vars=nb_optional,
        nb_sequences=len(sequences),
        nb_sequences_with_types=nb_typed_sequences,
        nb_cumul_functions=len(get_registered_cumuls()),
        nb_state_functions=len(get_registered_state_functions()),
    )


def solution_statistics(
    intervals: Sequence[IntervalVar] | None = None,
    *,
    status: object | None = None,
    objective: Any | None = None,
    solve_time: float | None = None,
) -> SolutionStatistics:
    """
    Return statistics about the current solution.

    Args:
        intervals: Optional list of intervals to analyze. Defaults to the
            registered intervals.
        status: Optional solve status from pycsp3 (SAT, OPTIMUM, UNSAT, etc.).
        objective: Optional objective expression or value to evaluate.
        solve_time: Optional elapsed solve time in seconds.
    """
    if intervals is None:
        from pycsp3_scheduling.variables.interval import get_registered_intervals

        intervals = get_registered_intervals()

    interval_values = [interval_value(interval) for interval in intervals]
    present = [val for val in interval_values if val is not None]

    min_start = min((val.start for val in present), default=None)
    max_end = max((val.end for val in present), default=None)
    makespan = max_end
    span = None if min_start is None or max_end is None else max_end - min_start

    objective_value: int | float | None
    if objective is None:
        objective_value = None
    elif isinstance(objective, (int, float)):
        objective_value = objective
    else:
        from pycsp3 import value
        try:
            objective_value = value(objective)
        except (AssertionError, TypeError):
            objective_value = None

    return SolutionStatistics(
        status=status,
        objective_value=objective_value,
        solve_time=solve_time,
        nb_interval_vars=len(intervals),
        nb_intervals_present=len(present),
        nb_intervals_absent=len(intervals) - len(present),
        min_start=min_start,
        max_end=max_end,
        makespan=makespan,
        span=span,
    )
