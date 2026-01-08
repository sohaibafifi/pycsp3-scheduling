"""
Sequence accessor expressions for scheduling models.

These functions return expressions that access properties of neighboring
intervals in a sequence relative to a given interval.

The key functions for building transition-based objectives are:
- type_of_next(sequence, interval, last_value, absent_value)
- type_of_prev(sequence, interval, first_value, absent_value)

These return pycsp3 variables that can be used to index into transition matrices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pycsp3_scheduling.expressions.interval_expr import ExprType, IntervalExpr

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3_scheduling.variables.sequence import SequenceVar


# Cache for type_of_next/type_of_prev variables to avoid duplication
_type_of_next_vars: dict[tuple[int, int], Any] = {}
_type_of_prev_vars: dict[tuple[int, int], Any] = {}
_sequence_position_vars: dict[int, list[Any]] = {}
_sequence_present_count_vars: dict[int, Any] = {}


def clear_sequence_expr_cache() -> None:
    """Clear cached sequence expression variables."""
    _type_of_next_vars.clear()
    _type_of_prev_vars.clear()
    _sequence_position_vars.clear()
    _sequence_present_count_vars.clear()


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


def _ensure_sequence_positions(sequence: SequenceVar) -> tuple[list[Any], Any]:
    """Create (or reuse) position variables and ordering constraints for a sequence."""
    if sequence._id in _sequence_position_vars:
        return (
            _sequence_position_vars[sequence._id],
            _sequence_present_count_vars[sequence._id],
        )

    try:
        from pycsp3 import Var, satisfy
        from pycsp3.classes.nodes import Node, TypeNode
    except ImportError:
        raise ImportError("pycsp3 is required for sequence position variables")

    from pycsp3_scheduling.constraints._pycsp3 import (
        start_var,
        length_value,
        presence_var,
    )

    intervals = sequence.intervals
    n = len(intervals)

    positions: list[Any] = []
    presences: list[Any] = []

    for interval in intervals:
        pres = presence_var(interval) if interval.optional else 1
        presences.append(pres)

        pos_dom = range(0, n + 1) if interval.optional else range(1, n + 1)
        pos_var = Var(dom=pos_dom, id=f"seqpos{sequence._id}_{interval._id}")
        positions.append(pos_var)

        if interval.optional:
            # Presence <-> position 0
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, pres, 1),
                    Node.build(TypeNode.EQ, pos_var, 0),
                )
            )
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.NE, pos_var, 0),
                    Node.build(TypeNode.EQ, pres, 0),
                )
            )

    # Count of present intervals
    count_var = Var(dom=range(0, n + 1), id=f"seqcount{sequence._id}")
    if presences:
        if len(presences) == 1:
            sum_presences = presences[0]
        else:
            sum_presences = Node.build(TypeNode.ADD, *presences)
        satisfy(Node.build(TypeNode.EQ, count_var, sum_presences))
    else:
        satisfy(Node.build(TypeNode.EQ, count_var, 0))

    # Present intervals must occupy positions 1..count_var (no gaps)
    for interval, pos_var, pres in zip(intervals, positions, presences):
        if interval.optional:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, pres, 0),
                    Node.build(TypeNode.LE, pos_var, count_var),
                )
            )
        else:
            satisfy(Node.build(TypeNode.LE, pos_var, count_var))

    # All-different positions for present intervals
    for i in range(n):
        for j in range(i + 1, n):
            pos_i = positions[i]
            pos_j = positions[j]
            interval_i = intervals[i]
            interval_j = intervals[j]

            if interval_i.optional or interval_j.optional:
                disjuncts = [Node.build(TypeNode.NE, pos_i, pos_j)]
                if interval_i.optional:
                    disjuncts.insert(0, Node.build(TypeNode.EQ, presences[i], 0))
                if interval_j.optional:
                    disjuncts.insert(0, Node.build(TypeNode.EQ, presences[j], 0))
                satisfy(Node.build(TypeNode.OR, *disjuncts))
            else:
                satisfy(Node.build(TypeNode.NE, pos_i, pos_j))

    # Link temporal order to positions
    starts = [start_var(interval) for interval in intervals]
    ends: list[Any] = []
    for interval, start in zip(intervals, starts):
        length = length_value(interval)
        if isinstance(length, int):
            end = Node.build(TypeNode.ADD, start, length) if length > 0 else start
        else:
            end = Node.build(TypeNode.ADD, start, length)
        ends.append(end)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            disjuncts = [
                Node.build(TypeNode.LT, starts[j], ends[i]),
                Node.build(TypeNode.LT, positions[i], positions[j]),
            ]
            if intervals[i].optional:
                disjuncts.insert(0, Node.build(TypeNode.EQ, presences[i], 0))
            if intervals[j].optional:
                disjuncts.insert(0, Node.build(TypeNode.EQ, presences[j], 0))
            satisfy(Node.build(TypeNode.OR, *disjuncts))

    _sequence_position_vars[sequence._id] = positions
    _sequence_present_count_vars[sequence._id] = count_var
    return positions, count_var


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
) -> Any:
    """
    Return a variable representing the type of the next interval in the sequence.

    This is the key function for building transition-based objectives like
    CP Optimizer's IloTypeOfNext pattern. The returned variable can be used
    to index into a TransitionMatrix.

    Requires a SequenceVar with types defined.

    Semantics:
    - If the interval is present and not last: returns the type of the next interval
    - If the interval is present and last: returns last_value
    - If the interval is absent: returns absent_value

    Args:
        sequence: SequenceVar with types defined.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        A pycsp3 variable representing the type of the next interval.
        This variable can be used to index into arrays/matrices.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.

    Example:
        >>> seq = SequenceVar(intervals=[t1, t2, t3], types=[0, 1, 2], name="machine")
        >>> next_type = type_of_next(seq, t1, last_value=3, absent_value=4)
        >>> # If t2 follows t1 in the schedule, next_type == 1
        >>> # If t1 is last, next_type == 3
        >>> # If t1 is absent, next_type == 4
        >>> 
        >>> # Use with TransitionMatrix for distance objective:
        >>> M = TransitionMatrix(travel_times, last_value=depot_return)
        >>> cost = M[type_of_interval, next_type]
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("type_of_next requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("type_of_next requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    
    # Check cache
    cache_key = (sequence._id, interval._id)
    if cache_key in _type_of_next_vars:
        return _type_of_next_vars[cache_key]
    
    # Build the type_of_next variable and constraints
    var = _build_type_of_next_var(sequence, interval, idx, last_value, absent_value)
    _type_of_next_vars[cache_key] = var
    return var


def _build_type_of_next_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
    last_value: int,
    absent_value: int,
) -> Any:
    """
    Build a pycsp3 variable for type_of_next with appropriate constraints.

    Successor-variable encoding using position variables:
    - Each interval has a position (0 if absent, otherwise 1..m).
    - The successor index is the interval at position +1, or a last/absent marker.
    - Use an element constraint to map successor index to type values.
    """
    try:
        from pycsp3 import Var, satisfy
        from pycsp3.classes.nodes import Node, TypeNode
    except ImportError:
        raise ImportError("pycsp3 is required for type_of_next")

    from pycsp3_scheduling.constraints._pycsp3 import (
        presence_var,
    )
    from pycsp3_scheduling.expressions.element import element

    intervals = sequence.intervals
    types = sequence.types
    n = len(intervals)

    # Build extended types array: [type_0, ..., type_{n-1}, last_value, absent_value]
    last_idx = n
    absent_idx = n + 1
    types_extended = list(types) + [last_value, absent_value]

    # Successor index variable (interval index, last, absent)
    next_idx_domain = set(range(n)) - {idx}
    next_idx_domain.add(last_idx)
    if interval.optional:
        next_idx_domain.add(absent_idx)

    next_idx = Var(dom=next_idx_domain, id=f"succ{sequence._id}_{interval._id}")

    # Result variable mapped from successor index
    result_domain = set(types_extended[j] for j in next_idx_domain)
    result_var = Var(dom=result_domain, id=f"tonext{sequence._id}_{interval._id}")
    satisfy(result_var == element(types_extended, next_idx))

    # Position-based successor channeling
    positions, count_var = _ensure_sequence_positions(sequence)
    pos_i = positions[idx]
    pres_i = presence_var(interval) if interval.optional else 1
    pos_i_plus_1 = Node.build(TypeNode.ADD, pos_i, 1)

    if interval.optional:
        # Absent <-> successor is absent marker
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 1),
                Node.build(TypeNode.EQ, next_idx, absent_idx),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, next_idx, absent_idx),
                Node.build(TypeNode.EQ, pres_i, 0),
            )
        )

    # Last position <-> successor is last marker
    if interval.optional:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 0),
                Node.build(TypeNode.NE, pos_i, count_var),
                Node.build(TypeNode.EQ, next_idx, last_idx),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, next_idx, last_idx),
                Node.build(TypeNode.EQ, pres_i, 1),
            )
        )
    else:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, pos_i, count_var),
                Node.build(TypeNode.EQ, next_idx, last_idx),
            )
        )

    satisfy(
        Node.build(
            TypeNode.OR,
            Node.build(TypeNode.NE, next_idx, last_idx),
            Node.build(TypeNode.EQ, pos_i, count_var),
        )
    )

    # Successor mapping: pos_j == pos_i + 1 <-> next_idx = j
    for j in range(n):
        if j == idx:
            continue
        pos_j = positions[j]

        # next_idx = j => pos_j = pos_i + 1
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, next_idx, j),
                Node.build(TypeNode.EQ, pos_j, pos_i_plus_1),
            )
        )

        # If i is present and pos_j = pos_i + 1, then next_idx = j
        if interval.optional:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, pres_i, 0),
                    Node.build(TypeNode.NE, pos_j, pos_i_plus_1),
                    Node.build(TypeNode.EQ, next_idx, j),
                )
            )
        else:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.NE, pos_j, pos_i_plus_1),
                    Node.build(TypeNode.EQ, next_idx, j),
                )
            )

    return result_var


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
) -> Any:
    """
    Return a variable representing the type of the previous interval in the sequence.

    Requires a SequenceVar with types defined.

    Semantics:
    - If the interval is present and not first: returns the type of the previous interval
    - If the interval is present and first: returns first_value
    - If the interval is absent: returns absent_value

    Args:
        sequence: SequenceVar with types defined.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        A pycsp3 variable representing the type of the previous interval.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("type_of_prev requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("type_of_prev requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)
    
    # Check cache
    cache_key = (sequence._id, interval._id)
    if cache_key in _type_of_prev_vars:
        return _type_of_prev_vars[cache_key]
    
    # Build the type_of_prev variable and constraints
    var = _build_type_of_prev_var(sequence, interval, idx, first_value, absent_value)
    _type_of_prev_vars[cache_key] = var
    return var


def _build_type_of_prev_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
    first_value: int,
    absent_value: int,
) -> Any:
    """
    Build a pycsp3 variable for type_of_prev with appropriate constraints.
    """
    try:
        from pycsp3 import Var, satisfy
        from pycsp3.classes.nodes import Node, TypeNode
    except ImportError:
        raise ImportError("pycsp3 is required for type_of_prev")
    
    from pycsp3_scheduling.constraints._pycsp3 import (
        presence_var,
    )
    from pycsp3_scheduling.expressions.element import element
    
    intervals = sequence.intervals
    types = sequence.types
    n = len(intervals)
    
    # Build extended types array: [type_0, ..., type_{n-1}, first_value, absent_value]
    first_idx = n
    absent_idx = n + 1
    types_extended = list(types) + [first_value, absent_value]

    # Predecessor index variable (interval index, first, absent)
    prev_idx_domain = set(range(n)) - {idx}
    prev_idx_domain.add(first_idx)
    if interval.optional:
        prev_idx_domain.add(absent_idx)

    prev_idx = Var(dom=prev_idx_domain, id=f"pred{sequence._id}_{interval._id}")

    # Result variable mapped from predecessor index
    result_domain = set(types_extended[j] for j in prev_idx_domain)
    result_var = Var(dom=result_domain, id=f"toprev{sequence._id}_{interval._id}")
    satisfy(result_var == element(types_extended, prev_idx))

    # Position-based predecessor channeling
    positions, _count_var = _ensure_sequence_positions(sequence)
    pos_i = positions[idx]
    pres_i = presence_var(interval) if interval.optional else 1
    pos_i_minus_1 = Node.build(TypeNode.ADD, pos_i, -1)

    if interval.optional:
        # Absent <-> predecessor is absent marker
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 1),
                Node.build(TypeNode.EQ, prev_idx, absent_idx),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, prev_idx, absent_idx),
                Node.build(TypeNode.EQ, pres_i, 0),
            )
        )

    # First position <-> predecessor is first marker
    if interval.optional:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 0),
                Node.build(TypeNode.NE, pos_i, 1),
                Node.build(TypeNode.EQ, prev_idx, first_idx),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, prev_idx, first_idx),
                Node.build(TypeNode.EQ, pres_i, 1),
            )
        )
    else:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, pos_i, 1),
                Node.build(TypeNode.EQ, prev_idx, first_idx),
            )
        )

    satisfy(
        Node.build(
            TypeNode.OR,
            Node.build(TypeNode.NE, prev_idx, first_idx),
            Node.build(TypeNode.EQ, pos_i, 1),
        )
    )

    # Predecessor mapping: pos_j == pos_i - 1 <-> prev_idx = j
    for j in range(n):
        if j == idx:
            continue
        pos_j = positions[j]

        # prev_idx = j => pos_j = pos_i - 1
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, prev_idx, j),
                Node.build(TypeNode.EQ, pos_j, pos_i_minus_1),
            )
        )

        # If i is present and pos_j = pos_i - 1, then prev_idx = j
        if interval.optional:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, pres_i, 0),
                    Node.build(TypeNode.NE, pos_j, pos_i_minus_1),
                    Node.build(TypeNode.EQ, prev_idx, j),
                )
            )
        else:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.NE, pos_j, pos_i_minus_1),
                    Node.build(TypeNode.EQ, prev_idx, j),
                )
            )

    return result_var
