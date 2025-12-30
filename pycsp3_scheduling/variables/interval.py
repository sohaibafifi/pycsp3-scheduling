"""
Interval variable implementation for scheduling models.

An interval variable represents a task/activity with:
- start: start time (can be a range [min, max])
- end: end time (can be a range [min, max])
- size: duration/size (can be a range [min, max])
- optional: whether the interval can be absent
- name: identifier for the variable
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from collections.abc import Sequence

# Type aliases for bounds
Bound = Union[int, tuple[int, int]]

# Constants for default bounds
INTERVAL_MIN = 0
INTERVAL_MAX = 2**30 - 1  # Large but not overflow-prone


@dataclass
class IntervalVar:
    """
    Represents an interval variable for scheduling.

    An interval variable represents a task or activity with a start time,
    end time, and duration. The interval can be optional (may be absent
    from the solution).

    Attributes:
        name: Unique identifier for this interval variable.
        start: Start time bound as int or (min, max) tuple.
        end: End time bound as int or (min, max) tuple.
        size: Duration/size bound as int or (min, max) tuple.
        length: Length bound (can differ from size with intensity functions).
        optional: If True, the interval may be absent from the solution.
        _id: Internal unique identifier.

    Example:
        >>> task = IntervalVar(size=10, name="task1")
        >>> optional_task = IntervalVar(size=(5, 20), optional=True, name="opt")
        >>> bounded_task = IntervalVar(start=(0, 100), end=(10, 200), size=15)
    """

    name: str | None = None
    start: Bound = field(default_factory=lambda: (INTERVAL_MIN, INTERVAL_MAX))
    end: Bound = field(default_factory=lambda: (INTERVAL_MIN, INTERVAL_MAX))
    size: Bound = field(default_factory=lambda: (0, INTERVAL_MAX))
    length: Bound | None = None
    optional: bool = False
    _id: int = field(default=-1, repr=False, compare=False)

    # Class-level counter for unique IDs
    _counter: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Normalize bounds and assign unique ID."""
        # Normalize bounds to tuples
        self.start = self._normalize_bound(self.start)
        self.end = self._normalize_bound(self.end)
        self.size = self._normalize_bound(self.size)
        if self.length is not None:
            self.length = self._normalize_bound(self.length)
        else:
            # Length defaults to size if not specified
            self.length = self.size

        # Assign unique ID if not set
        if self._id == -1:
            self._id = IntervalVar._get_next_id()

        # Generate name if not provided
        if self.name is None:
            self.name = f"_interval_{self._id}"

        # Validate bounds
        self._validate_bounds()

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID for interval variables."""
        # Use a module-level counter stored as class attribute
        current = getattr(IntervalVar, "_id_counter", 0)
        IntervalVar._id_counter = current + 1
        return current

    @staticmethod
    def _normalize_bound(bound: Bound) -> tuple[int, int]:
        """Convert bound to (min, max) tuple."""
        if isinstance(bound, int):
            return (bound, bound)
        if isinstance(bound, tuple) and len(bound) == 2:
            return (int(bound[0]), int(bound[1]))
        raise ValueError(f"Invalid bound: {bound}. Expected int or (min, max) tuple.")

    def _validate_bounds(self) -> None:
        """Validate that bounds are consistent."""
        start_min, start_max = self.start
        end_min, end_max = self.end
        size_min, size_max = self.size

        if start_min > start_max:
            raise ValueError(f"Invalid start bounds: min={start_min} > max={start_max}")
        if end_min > end_max:
            raise ValueError(f"Invalid end bounds: min={end_min} > max={end_max}")
        if size_min > size_max:
            raise ValueError(f"Invalid size bounds: min={size_min} > max={size_max}")
        if size_min < 0:
            raise ValueError(f"Size cannot be negative: min={size_min}")

        # Check feasibility: end >= start + size
        if end_max < start_min + size_min:
            raise ValueError(
                f"Infeasible bounds: end_max={end_max} < start_min + size_min="
                f"{start_min + size_min}"
            )

    @property
    def start_min(self) -> int:
        """Minimum possible start time."""
        return self.start[0]

    @property
    def start_max(self) -> int:
        """Maximum possible start time."""
        return self.start[1]

    @property
    def end_min(self) -> int:
        """Minimum possible end time."""
        return self.end[0]

    @property
    def end_max(self) -> int:
        """Maximum possible end time."""
        return self.end[1]

    @property
    def size_min(self) -> int:
        """Minimum possible size/duration."""
        return self.size[0]

    @property
    def size_max(self) -> int:
        """Maximum possible size/duration."""
        return self.size[1]

    @property
    def length_min(self) -> int:
        """Minimum possible length."""
        assert self.length is not None
        return self.length[0]

    @property
    def length_max(self) -> int:
        """Maximum possible length."""
        assert self.length is not None
        return self.length[1]

    @property
    def is_optional(self) -> bool:
        """Whether this interval can be absent."""
        return self.optional

    @property
    def is_present(self) -> bool:
        """Whether this interval must be present (not optional)."""
        return not self.optional

    @property
    def is_fixed_size(self) -> bool:
        """Whether the size is fixed (not a range)."""
        return self.size[0] == self.size[1]

    @property
    def is_fixed_start(self) -> bool:
        """Whether the start is fixed."""
        return self.start[0] == self.start[1]

    @property
    def is_fixed_end(self) -> bool:
        """Whether the end is fixed."""
        return self.end[0] == self.end[1]

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        """Equality based on unique ID."""
        if not isinstance(other, IntervalVar):
            return NotImplemented
        return self._id == other._id

    def __repr__(self) -> str:
        """String representation."""
        parts = [f"IntervalVar({self.name!r}"]
        if self.is_fixed_size:
            parts.append(f"size={self.size_min}")
        else:
            parts.append(f"size={self.size}")
        if not self.is_fixed_start or self.start_min != INTERVAL_MIN:
            parts.append(f"start={self.start}")
        if not self.is_fixed_end or self.end_max != INTERVAL_MAX:
            parts.append(f"end={self.end}")
        if self.optional:
            parts.append("optional=True")
        return ", ".join(parts) + ")"


def IntervalVarArray(
    size: int | Sequence[int],
    *,
    start: Bound | None = None,
    end: Bound | None = None,
    size_range: Bound | None = None,
    length: Bound | None = None,
    optional: bool = False,
    name: str | None = None,
) -> list[IntervalVar]:
    """
    Create an array of interval variables.

    Args:
        size: Number of intervals, or tuple for multi-dimensional array.
        start: Start bound for all intervals.
        end: End bound for all intervals.
        size_range: Size/duration bound for all intervals (named size_range
                    to avoid conflict with the size parameter).
        length: Length bound for all intervals.
        optional: Whether all intervals are optional.
        name: Base name for intervals (will be suffixed with index).

    Returns:
        List of IntervalVar objects (nested list for multi-dimensional).

    Example:
        >>> tasks = IntervalVarArray(5, size_range=10, name="task")
        >>> ops = IntervalVarArray((3, 4), size_range=(5, 20), optional=True)
    """
    # Handle single dimension
    if isinstance(size, int):
        dims = [size]
    else:
        dims = list(size)

    base_name = name or "_interval"

    def create_recursive(dims: list[int], indices: list[int]) -> list:
        """Recursively create nested array structure."""
        if len(dims) == 1:
            # Base case: create actual interval variables
            result = []
            for i in range(dims[0]):
                idx = indices + [i]
                var_name = f"{base_name}[{']['.join(map(str, idx))}]"
                kwargs: dict = {"name": var_name, "optional": optional}
                if start is not None:
                    kwargs["start"] = start
                if end is not None:
                    kwargs["end"] = end
                if size_range is not None:
                    kwargs["size"] = size_range
                if length is not None:
                    kwargs["length"] = length
                result.append(IntervalVar(**kwargs))
            return result
        else:
            # Recursive case: create nested list
            return [
                create_recursive(dims[1:], indices + [i])
                for i in range(dims[0])
            ]

    return create_recursive(dims, [])


def IntervalVarDict(
    keys: Sequence,
    *,
    start: Bound | None = None,
    end: Bound | None = None,
    size_range: Bound | None = None,
    length: Bound | None = None,
    optional: bool = False,
    name: str | None = None,
) -> dict:
    """
    Create a dictionary of interval variables indexed by keys.

    Args:
        keys: Sequence of keys for the dictionary.
        start: Start bound for all intervals.
        end: End bound for all intervals.
        size_range: Size/duration bound for all intervals.
        length: Length bound for all intervals.
        optional: Whether all intervals are optional.
        name: Base name for intervals.

    Returns:
        Dictionary mapping keys to IntervalVar objects.

    Example:
        >>> tasks = IntervalVarDict(["A", "B", "C"], size_range=10, name="task")
        >>> tasks["A"].size_min  # 10
    """
    base_name = name or "_interval"
    result = {}
    for key in keys:
        var_name = f"{base_name}[{key}]"
        kwargs: dict = {"name": var_name, "optional": optional}
        if start is not None:
            kwargs["start"] = start
        if end is not None:
            kwargs["end"] = end
        if size_range is not None:
            kwargs["size"] = size_range
        if length is not None:
            kwargs["length"] = length
        result[key] = IntervalVar(**kwargs)
    return result


# Registry for all interval variables (for model compilation)
_interval_registry: list[IntervalVar] = []


def register_interval(interval: IntervalVar) -> None:
    """Register an interval variable for model compilation."""
    if interval not in _interval_registry:
        _interval_registry.append(interval)


def get_registered_intervals() -> list[IntervalVar]:
    """Get all registered interval variables."""
    return list(_interval_registry)


def clear_interval_registry() -> None:
    """Clear the interval variable registry."""
    _interval_registry.clear()
    IntervalVar._id_counter = 0
