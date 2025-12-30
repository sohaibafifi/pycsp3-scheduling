"""
Variable types for scheduling models.

This module provides:
- IntervalVar: Represents a task/activity with start, end, and duration
- SequenceVar: Represents an ordered sequence of intervals on a resource
"""

from __future__ import annotations

from pycsp3_scheduling.variables.interval import (
    INTERVAL_MAX,
    INTERVAL_MIN,
    IntervalVar,
    IntervalVarArray,
    IntervalVarDict,
    clear_interval_registry,
    get_registered_intervals,
    register_interval,
)
from pycsp3_scheduling.variables.sequence import (
    SequenceVar,
    SequenceVarArray,
    clear_sequence_registry,
    get_registered_sequences,
    register_sequence,
)

__all__ = [
    # Interval variables
    "IntervalVar",
    "IntervalVarArray",
    "IntervalVarDict",
    "INTERVAL_MIN",
    "INTERVAL_MAX",
    "register_interval",
    "get_registered_intervals",
    "clear_interval_registry",
    # Sequence variables
    "SequenceVar",
    "SequenceVarArray",
    "register_sequence",
    "get_registered_sequences",
    "clear_sequence_registry",
]
