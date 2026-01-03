"""
Sequence variable implementation for scheduling models.

A sequence variable represents an ordered sequence of interval variables,
typically used to model a disjunctive resource (machine) where intervals
must be totally ordered and non-overlapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from pycsp3_scheduling.variables.interval import IntervalVar


@dataclass
class SequenceVar:
    """
    Represents a sequence variable for scheduling.

    A sequence variable represents an ordered set of interval variables.
    It is typically used to model a disjunctive resource where only one
    interval can execute at a time.

    Each interval in the sequence can optionally have an associated type
    (integer identifier) used for transition matrix constraints.

    Attributes:
        intervals: List of interval variables in this sequence.
        types: Optional list of type identifiers (one per interval).
               Used for transition constraints (setup times).
        name: Unique identifier for this sequence variable.
        _id: Internal unique identifier.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=15, name="task2")
        >>> task3 = IntervalVar(size=8, name="task3")
        >>> seq = SequenceVar(intervals=[task1, task2, task3], name="machine1")

        >>> # With types for transition matrix
        >>> seq = SequenceVar(
        ...     intervals=[task1, task2, task3],
        ...     types=[0, 1, 0],
        ...     name="machine1"
        ... )
    """

    intervals: list[IntervalVar] = field(default_factory=list)
    types: list[int] | None = None
    name: str | None = None
    _id: int = field(default=-1, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate and initialize the sequence variable."""
        # Convert intervals to list if needed
        if not isinstance(self.intervals, list):
            self.intervals = list(self.intervals)

        # Validate types length matches intervals
        if self.types is not None:
            if not isinstance(self.types, list):
                self.types = list(self.types)
            if len(self.types) != len(self.intervals):
                raise ValueError(
                    f"Length of types ({len(self.types)}) must match "
                    f"length of intervals ({len(self.intervals)})"
                )
            # Validate types are non-negative integers
            for i, t in enumerate(self.types):
                if not isinstance(t, int) or t < 0:
                    raise ValueError(
                        f"Type at index {i} must be a non-negative integer, got {t}"
                    )

        # Assign unique ID if not set
        if self._id == -1:
            self._id = SequenceVar._get_next_id()

        # Generate name if not provided
        if self.name is None:
            self.name = f"_sequence_{self._id}"

        # Register for model compilation/interop helpers
        register_sequence(self)

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID for sequence variables."""
        current = getattr(SequenceVar, "_id_counter", 0)
        SequenceVar._id_counter = current + 1
        return current

    @property
    def size(self) -> int:
        """Number of intervals in this sequence."""
        return len(self.intervals)

    @property
    def has_types(self) -> bool:
        """Whether this sequence has type identifiers."""
        return self.types is not None

    def get_interval(self, index: int) -> IntervalVar:
        """Get interval at given index."""
        return self.intervals[index]

    def get_type(self, index: int) -> int | None:
        """Get type identifier at given index, or None if no types."""
        if self.types is None:
            return None
        return self.types[index]

    def get_intervals_by_type(self, type_id: int) -> list[IntervalVar]:
        """Get all intervals with the given type identifier."""
        if self.types is None:
            return []
        return [
            interval
            for interval, t in zip(self.intervals, self.types)
            if t == type_id
        ]

    def __len__(self) -> int:
        """Number of intervals in the sequence."""
        return len(self.intervals)

    def __iter__(self):
        """Iterate over intervals."""
        return iter(self.intervals)

    def __getitem__(self, index: int) -> IntervalVar:
        """Get interval by index."""
        return self.intervals[index]

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        """Equality based on unique ID."""
        if not isinstance(other, SequenceVar):
            return NotImplemented
        return self._id == other._id

    def __repr__(self) -> str:
        """String representation."""
        interval_names = [iv.name for iv in self.intervals]
        parts = [f"SequenceVar({self.name!r}"]
        parts.append(f"intervals={interval_names}")
        if self.types is not None:
            parts.append(f"types={self.types}")
        return ", ".join(parts) + ")"


def SequenceVarArray(
    size: int | Sequence[int],
    intervals_per_sequence: list[list[IntervalVar]] | None = None,
    *,
    types_per_sequence: list[list[int]] | None = None,
    name: str | None = None,
) -> list[SequenceVar]:
    """
    Create an array of sequence variables.

    Args:
        size: Number of sequences, or tuple for multi-dimensional array.
        intervals_per_sequence: List of interval lists, one per sequence.
        types_per_sequence: Optional list of type lists, one per sequence.
        name: Base name for sequences (will be suffixed with index).

    Returns:
        List of SequenceVar objects (nested list for multi-dimensional).

    Example:
        >>> # Create sequences for 3 machines
        >>> ops_m0 = [IntervalVar(size=10) for _ in range(5)]
        >>> ops_m1 = [IntervalVar(size=15) for _ in range(5)]
        >>> ops_m2 = [IntervalVar(size=8) for _ in range(5)]
        >>> sequences = SequenceVarArray(
        ...     3,
        ...     intervals_per_sequence=[ops_m0, ops_m1, ops_m2],
        ...     name="machine"
        ... )
    """
    # Handle single dimension
    if isinstance(size, int):
        n = size
    else:
        if len(size) != 1:
            raise ValueError("SequenceVarArray only supports 1D arrays")
        n = size[0]

    if intervals_per_sequence is not None and len(intervals_per_sequence) != n:
        raise ValueError(
            f"Length of intervals_per_sequence ({len(intervals_per_sequence)}) "
            f"must match size ({n})"
        )

    if types_per_sequence is not None and len(types_per_sequence) != n:
        raise ValueError(
            f"Length of types_per_sequence ({len(types_per_sequence)}) "
            f"must match size ({n})"
        )

    base_name = name or "_sequence"
    result = []

    for i in range(n):
        seq_name = f"{base_name}[{i}]"
        intervals = intervals_per_sequence[i] if intervals_per_sequence else []
        types = types_per_sequence[i] if types_per_sequence else None
        result.append(SequenceVar(intervals=intervals, types=types, name=seq_name))

    return result


# Registry for all sequence variables (for model compilation)
_sequence_registry: list[SequenceVar] = []


def register_sequence(sequence: SequenceVar) -> None:
    """Register a sequence variable for model compilation."""
    if sequence not in _sequence_registry:
        _sequence_registry.append(sequence)


def get_registered_sequences() -> list[SequenceVar]:
    """Get all registered sequence variables."""
    return list(_sequence_registry)


def clear_sequence_registry() -> None:
    """Clear the sequence variable registry."""
    _sequence_registry.clear()
    SequenceVar._id_counter = 0
