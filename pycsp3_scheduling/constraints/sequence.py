"""
Sequence-based constraints for scheduling.
"""

from __future__ import annotations

from collections.abc import Iterable

from pycsp3_scheduling.constraints._pycsp3 import length_value, start_var
from pycsp3_scheduling.variables.interval import IntervalVar
from pycsp3_scheduling.variables.sequence import SequenceVar


def SeqNoOverlap(sequence, transition_matrix=None, is_direct: bool = False):
    """
    Enforce non-overlap on a sequence of intervals.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        transition_matrix: Optional setup-time matrix (not yet supported).
        is_direct: Whether to use direct transitions (not yet supported).

        SeqNoOverlap currently ignores transition_matrix/is_direct and raises NotImplementedError if provided.
    """
    if transition_matrix is not None or is_direct:
        raise NotImplementedError("transition_matrix/is_direct not supported yet.")

    if isinstance(sequence, SequenceVar):
        intervals = sequence.intervals
    elif isinstance(sequence, Iterable):
        intervals = list(sequence)
    else:
        raise TypeError("sequence must be a SequenceVar or iterable of IntervalVar")

    for interval in intervals:
        if not isinstance(interval, IntervalVar):
            raise TypeError("SeqNoOverlap expects IntervalVar elements")

    origins = [start_var(interval) for interval in intervals]
    lengths = [length_value(interval) for interval in intervals]

    from pycsp3 import NoOverlap

    return NoOverlap(origins=origins, lengths=lengths)
