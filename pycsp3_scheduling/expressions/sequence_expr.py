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


def clear_sequence_expr_cache() -> None:
    """Clear cached sequence expression variables."""
    _type_of_next_vars.clear()
    _type_of_prev_vars.clear()


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
    
    Strategy: Use biconditional channeling.
    For each candidate j (j != idx), we express:
        result = types[j]  <=>  (j is the immediate successor of interval)
    And for the special "last" case:
        result = last_value  <=>  (no interval comes after interval)
    And for optional intervals:
        result = absent_value  <=>  (interval is absent)
    """
    try:
        from pycsp3 import Var, satisfy
        from pycsp3.classes.nodes import Node, TypeNode
    except ImportError:
        raise ImportError("pycsp3 is required for type_of_next")
    
    from pycsp3_scheduling.constraints._pycsp3 import (
        start_var,
        length_value,
        presence_var,
    )
    
    intervals = sequence.intervals
    types = sequence.types
    n = len(intervals)
    
    # Determine valid domain values for result
    # For mandatory intervals: can be any type of other intervals, or last_value
    # For optional interval: also absent_value
    valid_values = set()
    other_indices = [j for j in range(n) if j != idx]
    for j in other_indices:
        valid_values.add(types[j])
    valid_values.add(last_value)
    if interval.optional:
        valid_values.add(absent_value)
    
    # Note: XCSP3 IDs must start with a letter, not underscore
    var_id = f"tonext{sequence._id}_{interval._id}"
    result_var = Var(dom=valid_values, id=var_id)
    
    # Get presence and timing for reference interval
    my_start = start_var(interval)
    my_length = length_value(interval)
    if isinstance(my_length, int):
        my_end = Node.build(TypeNode.ADD, my_start, my_length) if my_length > 0 else my_start
    else:
        my_end = Node.build(TypeNode.ADD, my_start, my_length)
    
    # Special case: only one other interval, both mandatory
    if len(other_indices) == 1 and not interval.optional:
        j = other_indices[0]
        other = intervals[j]
        if not other.optional:
            other_type = types[j]
            other_start = start_var(other)
            
            # j_after_me: my_end <= other_start
            j_after_me = Node.build(TypeNode.LE, my_end, other_start)
            
            # Biconditional: result = other_type <=> j_after_me
            # = (j_after_me => result = other_type) AND (result = other_type => j_after_me)
            # = (NOT j_after_me OR result = other_type) AND (result != other_type OR j_after_me)
            
            # For the second part, since domain is {other_type, last_value}:
            # result != other_type  means  result = last_value
            
            # Constraint 1: NOT j_after_me OR result = other_type
            satisfy(
                Node.build(TypeNode.OR, 
                    Node.build(TypeNode.NOT, j_after_me), 
                    Node.build(TypeNode.EQ, result_var, other_type))
            )
            # Constraint 2: result = last_value OR j_after_me
            satisfy(
                Node.build(TypeNode.OR, 
                    Node.build(TypeNode.EQ, result_var, last_value),
                    j_after_me)
            )
            return result_var
    
    # General case: multiple candidates or optional intervals
    my_pres = presence_var(interval) if interval.optional else None
    
    # Handle optional interval: if absent, result = absent_value
    if interval.optional:
        # my_pres = 1 OR result = absent_value
        satisfy(
            Node.build(TypeNode.OR,
                Node.build(TypeNode.EQ, my_pres, 1),
                Node.build(TypeNode.EQ, result_var, absent_value))
        )
        # Also: my_pres = 0 => result = absent_value
        # which is: my_pres = 1 OR result = absent_value (same as above)
        
        # And: result = absent_value => my_pres = 0
        # which is: result != absent_value OR my_pres = 0
        satisfy(
            Node.build(TypeNode.OR,
                Node.build(TypeNode.NE, result_var, absent_value),
                Node.build(TypeNode.EQ, my_pres, 0))
        )
    
    # For each candidate j, build the condition "j is immediate successor"
    for j in other_indices:
        other = intervals[j]
        other_type = types[j]
        other_start = start_var(other)
        other_pres = presence_var(other) if other.optional else None
        other_length = length_value(other)
        if isinstance(other_length, int):
            other_end = Node.build(TypeNode.ADD, other_start, other_length) if other_length > 0 else other_start
        else:
            other_end = Node.build(TypeNode.ADD, other_start, other_length)
        
        # Base condition: j comes after me
        j_after_me = Node.build(TypeNode.LE, my_end, other_start)
        
        # Build "no one between me and j" conditions
        no_between_parts = []
        for k in other_indices:
            if k == j:
                continue
            third = intervals[k]
            third_start = start_var(third)
            third_pres = presence_var(third) if third.optional else None
            third_length = length_value(third)
            if isinstance(third_length, int):
                third_end = Node.build(TypeNode.ADD, third_start, third_length) if third_length > 0 else third_start
            else:
                third_end = Node.build(TypeNode.ADD, third_start, third_length)
            
            # k is NOT between me and j means:
            # k absent OR k ends before/at me ends OR k starts at/after j starts
            # = k absent OR NOT(my_end <= k_start AND k_end <= other_start)
            # = k absent OR my_end > k_start OR k_end > other_start
            k_not_after_me = Node.build(TypeNode.GT, my_end, third_start)
            k_not_before_j = Node.build(TypeNode.GT, third_end, other_start)
            
            if third.optional:
                k_absent = Node.build(TypeNode.EQ, third_pres, 0)
                no_k_between = Node.build(TypeNode.OR, k_absent, k_not_after_me, k_not_before_j)
            else:
                no_k_between = Node.build(TypeNode.OR, k_not_after_me, k_not_before_j)
            no_between_parts.append(no_k_between)
        
        # Full condition: j is immediate successor
        # = j present (if optional) AND j after me AND no one between
        cond_parts = [j_after_me]
        if other.optional:
            cond_parts.append(Node.build(TypeNode.EQ, other_pres, 1))
        if no_between_parts:
            if len(no_between_parts) == 1:
                cond_parts.append(no_between_parts[0])
            else:
                cond_parts.append(Node.build(TypeNode.AND, *no_between_parts))
        
        if len(cond_parts) == 1:
            j_is_next = cond_parts[0]
        else:
            j_is_next = Node.build(TypeNode.AND, *cond_parts)
        
        # Add presence of current interval if optional
        if interval.optional:
            j_is_next = Node.build(TypeNode.AND, Node.build(TypeNode.EQ, my_pres, 1), j_is_next)
        
        # Biconditional channeling: j_is_next <=> result = other_type
        # = (j_is_next => result = other_type) AND (result = other_type => j_is_next)
        
        # Part 1: j_is_next => result = other_type
        # = NOT j_is_next OR result = other_type
        satisfy(
            Node.build(TypeNode.OR,
                Node.build(TypeNode.NOT, j_is_next),
                Node.build(TypeNode.EQ, result_var, other_type))
        )
        
        # Part 2: result = other_type => j_is_next
        # = result != other_type OR j_is_next
        satisfy(
            Node.build(TypeNode.OR,
                Node.build(TypeNode.NE, result_var, other_type),
                j_is_next)
        )
    
    # Handle "is_last" case: if no one comes after me, result = last_value
    # "no one after me" = AND for all j: (j absent OR j not after me)
    no_one_after_parts = []
    for j in other_indices:
        other = intervals[j]
        other_start = start_var(other)
        other_pres = presence_var(other) if other.optional else None
        
        # j not after me: my_end > other_start
        j_not_after = Node.build(TypeNode.GT, my_end, other_start)
        
        if other.optional:
            j_absent = Node.build(TypeNode.EQ, other_pres, 0)
            no_j_after = Node.build(TypeNode.OR, j_absent, j_not_after)
        else:
            no_j_after = j_not_after
        no_one_after_parts.append(no_j_after)
    
    if len(no_one_after_parts) == 1:
        no_one_after = no_one_after_parts[0]
    else:
        no_one_after = Node.build(TypeNode.AND, *no_one_after_parts)
    
    # Add presence condition if optional
    is_last_cond = no_one_after
    if interval.optional:
        is_last_cond = Node.build(TypeNode.AND, Node.build(TypeNode.EQ, my_pres, 1), is_last_cond)
    
    # Biconditional: is_last_cond <=> result = last_value
    # Part 1: is_last_cond => result = last_value
    satisfy(
        Node.build(TypeNode.OR,
            Node.build(TypeNode.NOT, is_last_cond),
            Node.build(TypeNode.EQ, result_var, last_value))
    )
    # Part 2: result = last_value => is_last_cond
    satisfy(
        Node.build(TypeNode.OR,
            Node.build(TypeNode.NE, result_var, last_value),
            is_last_cond)
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
        start_var,
        length_value,
        presence_var,
    )
    
    intervals = sequence.intervals
    types = sequence.types
    n = len(intervals)
    
    # Build domain: all possible types + first_value + absent_value
    all_types = set(types)
    all_types.add(first_value)
    all_types.add(absent_value)
    
    # Create the variable
    # Note: XCSP3 IDs must start with a letter, not underscore
    var_id = f"toprev{sequence._id}_{interval._id}"
    result_var = Var(dom=all_types, id=var_id)
    
    # Get presence and timing for reference interval
    my_pres = presence_var(interval)
    my_start = start_var(interval)
    
    # Constraint 1: If interval is absent, result = absent_value
    # NOT(present) implies result == absent_value
    # = present OR (result == absent_value)
    if interval.optional:
        satisfy(
            Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, my_pres, 1),
                Node.build(TypeNode.EQ, result_var, absent_value)
            )
        )
    
    # For each other interval j:
    # If j is present AND j comes before interval AND j is the immediate predecessor,
    # then result_var == types[j]
    
    for j, other in enumerate(intervals):
        if j == idx:
            continue
        
        other_type = types[j]
        other_pres = presence_var(other)
        other_start = start_var(other)
        other_length = length_value(other)
        if isinstance(other_length, int):
            other_end = Node.build(TypeNode.ADD, other_start, other_length) if other_length > 0 else other_start
        else:
            other_end = Node.build(TypeNode.ADD, other_start, other_length)
        
        # Condition: j is present AND comes before interval (other_end <= my_start)
        j_before_me = Node.build(TypeNode.LE, other_end, my_start)
        
        # Condition: no other interval k is between j and me
        no_one_between_conditions = []
        for k, third in enumerate(intervals):
            if k == idx or k == j:
                continue
            
            k_pres = presence_var(third)
            k_start = start_var(third)
            k_length = length_value(third)
            if isinstance(k_length, int):
                k_end = Node.build(TypeNode.ADD, k_start, k_length) if k_length > 0 else k_start
            else:
                k_end = Node.build(TypeNode.ADD, k_start, k_length)
            
            # k is NOT between j and me: k absent OR k ends after me starts OR k starts before j ends
            k_absent = Node.build(TypeNode.EQ, k_pres, 0) if third.optional else None
            k_after_me = Node.build(TypeNode.LT, my_start, k_start)  # k starts after me
            k_before_j = Node.build(TypeNode.LT, k_end, other_end)  # k ends before j ends
            
            if k_absent:
                no_k_between = Node.build(TypeNode.OR, k_absent, k_after_me, k_before_j)
            else:
                no_k_between = Node.build(TypeNode.OR, k_after_me, k_before_j)
            
            no_one_between_conditions.append(no_k_between)
        
        # j_is_prev = j_present AND j_before_me AND no_one_between
        if other.optional:
            j_present_cond = Node.build(TypeNode.EQ, other_pres, 1)
            base_cond = Node.build(TypeNode.AND, j_present_cond, j_before_me)
        else:
            base_cond = j_before_me
        
        if no_one_between_conditions:
            all_no_between = Node.build(TypeNode.AND, *no_one_between_conditions) if len(no_one_between_conditions) > 1 else no_one_between_conditions[0]
            j_is_prev = Node.build(TypeNode.AND, base_cond, all_no_between)
        else:
            j_is_prev = base_cond
        
        # Add interval's presence to condition
        if interval.optional:
            my_present = Node.build(TypeNode.EQ, my_pres, 1)
            full_cond = Node.build(TypeNode.AND, my_present, j_is_prev)
        else:
            full_cond = j_is_prev
        
        # IF full_cond THEN result_var == other_type
        result_eq_type = Node.build(TypeNode.EQ, result_var, other_type)
        satisfy(
            Node.build(TypeNode.OR, Node.build(TypeNode.NOT, full_cond), result_eq_type)
        )
    
    # Constraint: If interval is present and is first (no one before), result = first_value
    not_first_conditions = []
    for j, other in enumerate(intervals):
        if j == idx:
            continue
        other_pres = presence_var(other)
        other_start = start_var(other)
        other_length = length_value(other)
        if isinstance(other_length, int):
            other_end = Node.build(TypeNode.ADD, other_start, other_length) if other_length > 0 else other_start
        else:
            other_end = Node.build(TypeNode.ADD, other_start, other_length)
        
        # j before me: other_end <= my_start AND j present
        j_before = Node.build(TypeNode.LE, other_end, my_start)
        if other.optional:
            j_present_and_before = Node.build(TypeNode.AND, Node.build(TypeNode.EQ, other_pres, 1), j_before)
        else:
            j_present_and_before = j_before
        not_first_conditions.append(j_present_and_before)
    
    if not_first_conditions:
        someone_before = Node.build(TypeNode.OR, *not_first_conditions) if len(not_first_conditions) > 1 else not_first_conditions[0]
        no_one_before = Node.build(TypeNode.NOT, someone_before)
        
        if interval.optional:
            my_present = Node.build(TypeNode.EQ, my_pres, 1)
            present_and_first = Node.build(TypeNode.AND, my_present, no_one_before)
        else:
            present_and_first = no_one_before
        
        result_eq_first = Node.build(TypeNode.EQ, result_var, first_value)
        satisfy(
            Node.build(TypeNode.OR, Node.build(TypeNode.NOT, present_and_first), result_eq_first)
        )
    
    return result_var
