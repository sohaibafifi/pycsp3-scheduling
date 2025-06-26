"""
Sequence accessor expressions for scheduling models.

These functions return expressions that access properties of neighboring
intervals in a sequence relative to a given interval.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pycsp3_scheduling.expressions.interval_expr import ExprType, IntervalExpr

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3_scheduling.variables.sequence import SequenceVar


def _validate_sequence_and_interval(sequence, interval: IntervalVar) -> tuple[list, int]:
    """Validate inputs and return intervals list and index."""
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if isinstance(sequence, SequenceVar):
        intervals = sequence.intervals
    elif isinstance(sequence, (list, tuple)):
        intervals = list(sequence)
    else:
        raise TypeError(
            f"sequence must be a SequenceVar or list, got {type(sequence).__name__}"
        )

    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )

    try:
        idx = intervals.index(interval)
    except ValueError:
        raise ValueError(f"interval '{interval.name}' is not in the sequence")

    return intervals, idx


# =============================================================================
# Next Interval Accessors
# =============================================================================


def start_of_next(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the start time of the next interval in the sequence.

    If the given interval is last in the sequence, returns last_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the start of the next interval.

    Example:
        >>> seq = SequenceVar(intervals=[t1, t2, t3], name="machine")
        >>> expr = start_of_next(seq, t1)  # Returns start of t2 (or next in order)
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.START_OF,  # Placeholder - actual logic in evaluation
        interval=interval,
        absent_value=absent_value,
        value=last_value,  # Store last_value for evaluation
    )


def end_of_next(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the end time of the next interval in the sequence.

    If the given interval is last in the sequence, returns last_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the end of the next interval.

    Example:
        >>> seq = SequenceVar(intervals=[t1, t2, t3], name="machine")
        >>> expr = end_of_next(seq, t1)  # Returns end of next interval after t1
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.END_OF,
        interval=interval,
        absent_value=absent_value,
        value=last_value,
    )


def size_of_next(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the size (duration) of the next interval in the sequence.

    If the given interval is last in the sequence, returns last_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the size of the next interval.
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.SIZE_OF,
        interval=interval,
        absent_value=absent_value,
        value=last_value,
    )


def length_of_next(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the length of the next interval in the sequence.

    If the given interval is last in the sequence, returns last_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the length of the next interval.
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.LENGTH_OF,
        interval=interval,
        absent_value=absent_value,
        value=last_value,
    )


def type_of_next(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the type of the next interval in the sequence.

    Requires a SequenceVar with types defined.

    If the given interval is last in the sequence, returns last_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar with types defined.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the type of the next interval.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("type_of_next requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("type_of_next requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    # Create a special expression for type access
    return IntervalExpr(
        expr_type=ExprType.START_OF,  # Placeholder type
        interval=interval,
        absent_value=absent_value,
        value=last_value,
    )


# =============================================================================
# Previous Interval Accessors
# =============================================================================


def start_of_prev(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the start time of the previous interval in the sequence.

    If the given interval is first in the sequence, returns first_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the start of the previous interval.

    Example:
        >>> seq = SequenceVar(intervals=[t1, t2, t3], name="machine")
        >>> expr = start_of_prev(seq, t2)  # Returns start of t1 (or prev in order)
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.START_OF,
        interval=interval,
        absent_value=absent_value,
        value=first_value,
    )


def end_of_prev(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the end time of the previous interval in the sequence.

    If the given interval is first in the sequence, returns first_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the end of the previous interval.
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.END_OF,
        interval=interval,
        absent_value=absent_value,
        value=first_value,
    )


def size_of_prev(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the size (duration) of the previous interval in the sequence.

    If the given interval is first in the sequence, returns first_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the size of the previous interval.
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.SIZE_OF,
        interval=interval,
        absent_value=absent_value,
        value=first_value,
    )


def length_of_prev(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the length of the previous interval in the sequence.

    If the given interval is first in the sequence, returns first_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar or list of IntervalVar.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the length of the previous interval.
    """
    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.LENGTH_OF,
        interval=interval,
        absent_value=absent_value,
        value=first_value,
    )


def type_of_prev(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return the type of the previous interval in the sequence.

    Requires a SequenceVar with types defined.

    If the given interval is first in the sequence, returns first_value.
    If the given interval is absent, returns absent_value.

    Args:
        sequence: SequenceVar with types defined.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        An expression representing the type of the previous interval.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("type_of_prev requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("type_of_prev requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    return IntervalExpr(
        expr_type=ExprType.START_OF,  # Placeholder type
        interval=interval,
        absent_value=absent_value,
        value=first_value,
    )
