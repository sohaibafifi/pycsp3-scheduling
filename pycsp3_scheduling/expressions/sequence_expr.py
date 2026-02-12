"""
Sequence accessor expressions for scheduling models.

These functions return expressions that access properties of neighboring
intervals in a sequence relative to a given interval.

The key functions for building transition-based objectives are:
- next_arg(sequence, interval, last_value, absent_value)
- prev_arg(sequence, interval, first_value, absent_value)

These return pycsp3 variables that can be used to index into transition matrices.
Similar to pycsp3's maximum_arg/minimum_arg pattern.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pycsp3_scheduling.expressions.interval_expr import ExprType, IntervalExpr

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3_scheduling.variables.sequence import SequenceVar


# Cache for next_arg/prev_arg variables to avoid duplication
# Core index variables are independent from marker values and can be reused.
_next_arg_index_vars: dict[tuple[int, int], Any] = {}
_prev_arg_index_vars: dict[tuple[int, int], Any] = {}
# Public next_arg/prev_arg results depend on marker values.
_next_arg_vars: dict[tuple[int, int, int, int], Any] = {}
_prev_arg_vars: dict[tuple[int, int, int, int], Any] = {}
_sequence_position_vars: dict[int, list[Any]] = {}
_sequence_present_count_vars: dict[int, Any] = {}


def clear_sequence_expr_cache() -> None:
    """Clear cached sequence expression variables."""
    _next_arg_index_vars.clear()
    _prev_arg_index_vars.clear()
    _next_arg_vars.clear()
    _prev_arg_vars.clear()
    _sequence_position_vars.clear()
    _sequence_present_count_vars.clear()


def _marker_suffix(a: int, b: int) -> str:
    """Return a stable, identifier-safe suffix for marker pairs."""
    def _one(v: int) -> str:
        return f"m{-v}" if v < 0 else f"p{v}"

    return f"{_one(a)}_{_one(b)}"


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
    """
    Create (or reuse) position variables and ordering constraints for a sequence.

    This function creates position variables that track the order of intervals
    in a sequence. For optional intervals, position 0 indicates absence.
    """
    if sequence._id in _sequence_position_vars:
        return (
            _sequence_position_vars[sequence._id],
            _sequence_present_count_vars[sequence._id],
        )

    from pycsp3 import AllDifferent, Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    from pycsp3_scheduling.constraints._pycsp3 import (
        start_var,
        length_value,
        presence_var,
    )

    intervals = sequence.intervals
    n = len(intervals)

    if n == 0:
        # Empty sequence - no constraints needed
        _sequence_position_vars[sequence._id] = []
        _sequence_present_count_vars[sequence._id] = 0
        return [], 0

    positions: list[Any] = []
    presences: list[Any] = []
    has_optional = False

    for interval in intervals:
        pres = presence_var(interval) if interval.optional else 1
        presences.append(pres)

        if interval.optional:
            has_optional = True
            pos_dom = range(0, n + 1)  # 0 = absent
        else:
            pos_dom = range(1, n + 1)

        pos_var = Var(dom=pos_dom, id=f"seqpos{sequence._id}_{interval._id}")
        positions.append(pos_var)

        if interval.optional:
            # Presence <-> position != 0 (bidirectional channeling)
            # present=1 => pos != 0, and pos != 0 => present=1
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

    # Count of present intervals.
    # For all-mandatory sequences, this is the constant n and no extra
    # variable/constraints are needed.
    if has_optional:
        count_var: Any = Var(dom=range(0, n + 1), id=f"seqcount{sequence._id}")
        if len(presences) == 1:
            sum_presences = presences[0]
        else:
            sum_presences = Node.build(TypeNode.ADD, *presences)
        satisfy(Node.build(TypeNode.EQ, count_var, sum_presences))

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
    else:
        count_var = n

    # All-different positions for present intervals
    # Use native AllDifferent constraint instead of O(n²) pairwise decomposition
    # excepting=0 allows multiple intervals to have position 0 (absent)
    if has_optional:
        # With optional intervals, use AllDifferent with excepting=0
        # This allows multiple absent intervals (position=0) while ensuring
        # all present intervals have unique positions
        satisfy(AllDifferent(positions, excepting=0))
    else:
        # All mandatory: simple AllDifferent
        satisfy(AllDifferent(positions))

    # Link temporal order to positions
    # Pre-compute start and end expressions once
    starts = [start_var(interval) for interval in intervals]
    ends: list[Any] = []
    for interval, start in zip(intervals, starts):
        length = length_value(interval)
        if isinstance(length, int):
            end = Node.build(TypeNode.ADD, start, length) if length > 0 else start
        else:
            end = Node.build(TypeNode.ADD, start, length)
        ends.append(end)

    # Temporal ordering constraint: if i ends before j starts, then pos[i] < pos[j]
    # Formulated as: (start[j] < end[i]) OR (pos[i] < pos[j]) OR absent conditions
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


def next_arg(
    sequence,
    interval: IntervalVar,
    last_value: int = 0,
    absent_value: int = 0,
) -> Any:
    """
    Return a variable representing the ID of the next interval in the sequence.

    Similar to pycsp3's maximum_arg pattern, this returns the argument (ID)
    of the successor interval. Used for building transition-based objectives.

    Requires a SequenceVar with types (IDs) defined.

    Semantics:
    - If the interval is present and not last: returns the ID of the next interval
    - If the interval is present and last: returns last_value
    - If the interval is absent: returns absent_value

    Args:
        sequence: SequenceVar with types (IDs) defined.
        interval: The reference interval.
        last_value: Value when interval is last (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        A pycsp3 variable representing the ID of the next interval.
        This variable can be used to index into arrays/matrices.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.

    Example:
        >>> seq = SequenceVar(intervals=[t1, t2, t3], types=[0, 1, 2], name="machine")
        >>> next_id = next_arg(seq, t1, last_value=3, absent_value=4)
        >>> # If t2 follows t1 in the schedule, next_id == 1
        >>> # If t1 is last, next_id == 3
        >>> # If t1 is absent, next_id == 4
        >>>
        >>> # Use with ElementMatrix for distance objective:
        >>> M = ElementMatrix(travel_times, last_value=depot_return)
        >>> cost = M[current_id, next_id]
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("next_arg requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("next_arg requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)

    # Value cache (depends on marker values)
    cache_key = (sequence._id, interval._id, last_value, absent_value)
    if cache_key in _next_arg_vars:
        return _next_arg_vars[cache_key]

    if len(set(sequence.types)) < len(sequence.types):
        # Repeated types: encode successor type directly (lighter than
        # successor-index + value mapping).
        var = _build_next_arg_direct_var(sequence, interval, idx, last_value, absent_value)
    else:
        # Core successor index cache (independent from marker values)
        index_cache_key = (sequence._id, interval._id)
        if index_cache_key in _next_arg_index_vars:
            next_idx = _next_arg_index_vars[index_cache_key]
        else:
            next_idx = _build_next_arg_index_var(sequence, interval, idx)
            _next_arg_index_vars[index_cache_key] = next_idx

        var = _build_next_arg_value_var(
            sequence, interval, idx, next_idx, last_value, absent_value
        )
    _next_arg_vars[cache_key] = var
    return var


# Backward compatibility alias
type_of_next = next_arg


def _is_identity_next_mapping(
    sequence: SequenceVar, interval: IntervalVar, last_value: int, absent_value: int
) -> bool:
    """Return True when next_idx already equals the desired next_arg value."""
    n = len(sequence.intervals)
    if any(t != i for i, t in enumerate(sequence.types)):
        return False
    if last_value != n:
        return False
    if interval.optional and absent_value != n + 1:
        return False
    return True


def _build_next_arg_value_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
    next_idx: Any,
    last_value: int,
    absent_value: int,
) -> Any:
    """Map successor index to user-facing type/marker values."""
    from pycsp3 import Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    if _is_identity_next_mapping(sequence, interval, last_value, absent_value):
        # Common fast path: sequence types are [0..n-1] and markers are n/n+1.
        return next_idx

    types = sequence.types
    n = len(sequence.intervals)
    last_idx = n
    absent_idx = n + 1
    types_extended = list(types) + [last_value, absent_value]

    next_idx_domain = set(range(n)) - {idx}
    next_idx_domain.add(last_idx)
    if interval.optional:
        next_idx_domain.add(absent_idx)

    result_domain = set(types_extended[j] for j in next_idx_domain)
    suffix = _marker_suffix(last_value, absent_value)
    if suffix == "p0_p0":
        result_id = f"tonext{sequence._id}_{interval._id}"
    else:
        result_id = f"tonext{sequence._id}_{interval._id}_{suffix}"

    result_var = Var(dom=result_domain, id=result_id)
    value_to_indices: dict[int, list[int]] = {}
    for j in next_idx_domain:
        value = types_extended[j]
        value_to_indices.setdefault(value, []).append(j)
        # next_idx = j => result_var = value
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, next_idx, j),
                Node.build(TypeNode.EQ, result_var, value),
            )
        )

    # result_var = value => next_idx is one of the corresponding indices
    for value, indices in value_to_indices.items():
        disjuncts = [Node.build(TypeNode.NE, result_var, value)]
        disjuncts.extend(Node.build(TypeNode.EQ, next_idx, j) for j in indices)
        satisfy(Node.build(TypeNode.OR, *disjuncts))
    return result_var


def _build_next_arg_index_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
) -> Any:
    """
    Build a core successor index variable for next_arg.

    Successor-variable encoding using position variables:
    - Each interval has a position (0 if absent, otherwise 1..m).
    - The successor index is the interval at position +1, or a last/absent marker.
    """
    from pycsp3 import Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    from pycsp3_scheduling.constraints._pycsp3 import (
        presence_var,
    )
    intervals = sequence.intervals
    n = len(intervals)

    last_idx = n
    absent_idx = n + 1

    # Successor index variable (interval index, last, absent)
    next_idx_domain = set(range(n)) - {idx}
    next_idx_domain.add(last_idx)
    if interval.optional:
        next_idx_domain.add(absent_idx)

    next_idx = Var(dom=next_idx_domain, id=f"succ{sequence._id}_{interval._id}")

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

    return next_idx


def _build_next_arg_direct_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
    last_value: int,
    absent_value: int,
) -> Any:
    """
    Build next_arg directly on successor type values (no successor-index variable).

    This is especially beneficial when sequence types are repeated, as it avoids
    the extra index-to-value channeling layer.
    """
    from pycsp3 import Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    from pycsp3_scheduling.constraints._pycsp3 import presence_var

    types = sequence.types
    n = len(sequence.intervals)

    result_domain = {types[j] for j in range(n) if j != idx}
    result_domain.add(last_value)
    if interval.optional:
        result_domain.add(absent_value)

    suffix = _marker_suffix(last_value, absent_value)
    if suffix == "p0_p0":
        result_id = f"tonext{sequence._id}_{interval._id}"
    else:
        result_id = f"tonext{sequence._id}_{interval._id}_{suffix}"
    result_var = Var(dom=result_domain, id=result_id)

    positions, count_var = _ensure_sequence_positions(sequence)
    pos_i = positions[idx]
    pos_i_plus_1 = Node.build(TypeNode.ADD, pos_i, 1)
    pres_i = presence_var(interval) if interval.optional else 1

    if interval.optional:
        # Absent <-> absent marker
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 1),
                Node.build(TypeNode.EQ, result_var, absent_value),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, result_var, absent_value),
                Node.build(TypeNode.EQ, pres_i, 0),
            )
        )

    # Last position <-> last marker
    if interval.optional:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, pres_i, 0),
                Node.build(TypeNode.NE, pos_i, count_var),
                Node.build(TypeNode.EQ, result_var, last_value),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, result_var, last_value),
                Node.build(TypeNode.EQ, pres_i, 0),
                Node.build(TypeNode.EQ, pos_i, count_var),
            )
        )
    else:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, pos_i, count_var),
                Node.build(TypeNode.EQ, result_var, last_value),
            )
        )
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, result_var, last_value),
                Node.build(TypeNode.EQ, pos_i, count_var),
            )
        )

    # Successor typing: if j is right after i, result is type(j)
    for j in range(n):
        if j == idx:
            continue
        pos_j = positions[j]
        if interval.optional:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, pres_i, 0),
                    Node.build(TypeNode.NE, pos_j, pos_i_plus_1),
                    Node.build(TypeNode.EQ, result_var, types[j]),
                )
            )
        else:
            satisfy(
                Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.NE, pos_j, pos_i_plus_1),
                    Node.build(TypeNode.EQ, result_var, types[j]),
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


def prev_arg(
    sequence,
    interval: IntervalVar,
    first_value: int = 0,
    absent_value: int = 0,
) -> Any:
    """
    Return a variable representing the ID of the previous interval in the sequence.

    Similar to pycsp3's maximum_arg pattern, this returns the argument (ID)
    of the predecessor interval. Used for building transition-based objectives.

    Requires a SequenceVar with types (IDs) defined.

    Semantics:
    - If the interval is present and not first: returns the ID of the previous interval
    - If the interval is present and first: returns first_value
    - If the interval is absent: returns absent_value

    Args:
        sequence: SequenceVar with types (IDs) defined.
        interval: The reference interval.
        first_value: Value when interval is first (default: 0).
        absent_value: Value when interval is absent (default: 0).

    Returns:
        A pycsp3 variable representing the ID of the previous interval.

    Raises:
        TypeError: If sequence is not a SequenceVar or has no types.
    """
    from pycsp3_scheduling.variables.sequence import SequenceVar

    if not isinstance(sequence, SequenceVar):
        raise TypeError("prev_arg requires a SequenceVar")
    if not sequence.has_types:
        raise ValueError("prev_arg requires sequence with types defined")

    intervals, idx = _validate_sequence_and_interval(sequence, interval)

    # Value cache (depends on marker values)
    cache_key = (sequence._id, interval._id, first_value, absent_value)
    if cache_key in _prev_arg_vars:
        return _prev_arg_vars[cache_key]

    # Core predecessor index cache (independent from marker values)
    index_cache_key = (sequence._id, interval._id)
    if index_cache_key in _prev_arg_index_vars:
        prev_idx = _prev_arg_index_vars[index_cache_key]
    else:
        prev_idx = _build_prev_arg_index_var(sequence, interval, idx)
        _prev_arg_index_vars[index_cache_key] = prev_idx

    var = _build_prev_arg_value_var(
        sequence, interval, idx, prev_idx, first_value, absent_value
    )
    _prev_arg_vars[cache_key] = var
    return var


# Backward compatibility alias
type_of_prev = prev_arg


def _is_identity_prev_mapping(
    sequence: SequenceVar, interval: IntervalVar, first_value: int, absent_value: int
) -> bool:
    """Return True when prev_idx already equals the desired prev_arg value."""
    n = len(sequence.intervals)
    if any(t != i for i, t in enumerate(sequence.types)):
        return False
    if first_value != n:
        return False
    if interval.optional and absent_value != n + 1:
        return False
    return True


def _build_prev_arg_value_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
    prev_idx: Any,
    first_value: int,
    absent_value: int,
) -> Any:
    """Map predecessor index to user-facing type/marker values."""
    from pycsp3 import Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    if _is_identity_prev_mapping(sequence, interval, first_value, absent_value):
        # Common fast path: sequence types are [0..n-1] and markers are n/n+1.
        return prev_idx

    types = sequence.types
    n = len(sequence.intervals)
    first_idx = n
    absent_idx = n + 1
    types_extended = list(types) + [first_value, absent_value]

    prev_idx_domain = set(range(n)) - {idx}
    prev_idx_domain.add(first_idx)
    if interval.optional:
        prev_idx_domain.add(absent_idx)

    result_domain = set(types_extended[j] for j in prev_idx_domain)
    suffix = _marker_suffix(first_value, absent_value)
    if suffix == "p0_p0":
        result_id = f"toprev{sequence._id}_{interval._id}"
    else:
        result_id = f"toprev{sequence._id}_{interval._id}_{suffix}"

    result_var = Var(dom=result_domain, id=result_id)
    value_to_indices: dict[int, list[int]] = {}
    for j in prev_idx_domain:
        value = types_extended[j]
        value_to_indices.setdefault(value, []).append(j)
        # prev_idx = j => result_var = value
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.NE, prev_idx, j),
                Node.build(TypeNode.EQ, result_var, value),
            )
        )

    # result_var = value => prev_idx is one of the corresponding indices
    for value, indices in value_to_indices.items():
        disjuncts = [Node.build(TypeNode.NE, result_var, value)]
        disjuncts.extend(Node.build(TypeNode.EQ, prev_idx, j) for j in indices)
        satisfy(Node.build(TypeNode.OR, *disjuncts))
    return result_var


def _build_prev_arg_index_var(
    sequence: SequenceVar,
    interval: IntervalVar,
    idx: int,
) -> Any:
    """
    Build a core predecessor index variable for prev_arg.
    """
    from pycsp3 import Var, satisfy
    from pycsp3.classes.nodes import Node, TypeNode

    from pycsp3_scheduling.constraints._pycsp3 import (
        presence_var,
    )
    intervals = sequence.intervals
    n = len(intervals)

    first_idx = n
    absent_idx = n + 1

    # Predecessor index variable (interval index, first, absent)
    prev_idx_domain = set(range(n)) - {idx}
    prev_idx_domain.add(first_idx)
    if interval.optional:
        prev_idx_domain.add(absent_idx)

    prev_idx = Var(dom=prev_idx_domain, id=f"pred{sequence._id}_{interval._id}")

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

    return prev_idx
