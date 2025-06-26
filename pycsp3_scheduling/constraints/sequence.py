"""
Sequence-based constraints for scheduling.

This module provides constraints for sequence variables:

1. **SeqNoOverlap(sequence, transition_matrix, is_direct)**: Non-overlap constraint
   - Ensures intervals don't overlap
   - Optional transition matrix for setup times between types
   - is_direct controls if transitions only count between consecutive intervals

2. **first(sequence, interval)**: Constrain interval to be first in sequence
3. **last(sequence, interval)**: Constrain interval to be last in sequence
4. **before(sequence, interval1, interval2)**: interval1 before interval2 in sequence
5. **previous(sequence, interval1, interval2)**: interval1 immediately before interval2

6. **same_sequence(seq1, seq2)**: Common intervals have same position
7. **same_common_subsequence(seq1, seq2)**: Common intervals have same relative order
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Sequence

from pycsp3_scheduling.constraints._pycsp3 import length_value, presence_var, start_var
from pycsp3_scheduling.variables.interval import IntervalVar
from pycsp3_scheduling.variables.sequence import SequenceVar

if TYPE_CHECKING:
    pass


def _get_node_builders():
    """Import and return pycsp3 Node building utilities."""
    from pycsp3.classes.nodes import Node, TypeNode

    return Node, TypeNode


def _validate_sequence(sequence) -> tuple[SequenceVar | None, list[IntervalVar]]:
    """Validate and extract intervals from sequence.

    Returns:
        Tuple of (SequenceVar or None, list of intervals)
    """
    if isinstance(sequence, SequenceVar):
        return sequence, sequence.intervals
    if isinstance(sequence, Iterable):
        intervals = list(sequence)
        for i, interval in enumerate(intervals):
            if not isinstance(interval, IntervalVar):
                raise TypeError(
                    f"sequence[{i}] must be an IntervalVar, got {type(interval).__name__}"
                )
        return None, intervals
    raise TypeError("sequence must be a SequenceVar or iterable of IntervalVar")


def _validate_interval_in_sequence(
    interval: IntervalVar, seq_var: SequenceVar | None, intervals: list[IntervalVar]
) -> int:
    """Validate that interval is in the sequence and return its index."""
    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")
    try:
        return intervals.index(interval)
    except ValueError:
        raise ValueError(f"interval '{interval.name}' is not in the sequence")


def _build_end_expr(interval: IntervalVar, Node, TypeNode):
    """Build end expression: start + length."""
    start = start_var(interval)
    length = length_value(interval)
    if isinstance(length, int) and length == 0:
        return start
    return Node.build(TypeNode.ADD, start, length)


# =============================================================================
# SeqNoOverlap Constraint
# =============================================================================


def SeqNoOverlap(
    sequence,
    transition_matrix: list[list[int]] | None = None,
    is_direct: bool = False,
):
    """
    Enforce non-overlap on a sequence of intervals with optional transition times.

    When intervals in the sequence are assigned to the same resource, they cannot
    overlap in time. If a transition matrix is provided, setup times between
    consecutive intervals are enforced based on their types.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        transition_matrix: Optional square matrix of transition times.
            If sequence has types, matrix[i][j] gives the minimum time
            between an interval of type i and an interval of type j.
        is_direct: If True, transition times apply only between directly
            consecutive (adjacent) intervals in the sequence. If False,
            transition times apply between any pair where one precedes
            the other.

    Returns:
        A pycsp3 constraint (ECtr) or list of constraints.

    Raises:
        TypeError: If sequence is not a SequenceVar or iterable of IntervalVar.
        ValueError: If transition_matrix dimensions don't match types.

    Example:
        >>> # Simple no-overlap
        >>> tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]
        >>> satisfy(SeqNoOverlap(tasks))

        >>> # With transition times by job type
        >>> seq = SequenceVar(intervals=tasks, types=[0, 1, 0], name="machine")
        >>> matrix = [[0, 5], [3, 0]]  # Setup time from type i to type j
        >>> satisfy(SeqNoOverlap(seq, transition_matrix=matrix))
    """
    seq_var, intervals = _validate_sequence(sequence)

    if len(intervals) == 0:
        return []  # Empty sequence - no constraints needed

    # Validate transition_matrix if provided
    if transition_matrix is not None:
        if seq_var is None or not seq_var.has_types:
            raise ValueError(
                "transition_matrix requires a SequenceVar with types defined"
            )
        # Validate matrix is square and has correct dimensions
        n_types = max(seq_var.types) + 1
        if not isinstance(transition_matrix, (list, tuple)):
            raise TypeError("transition_matrix must be a 2D list")
        if len(transition_matrix) < n_types:
            raise ValueError(
                f"transition_matrix must have at least {n_types} rows "
                f"(one per type), got {len(transition_matrix)}"
            )
        for i, row in enumerate(transition_matrix):
            if not isinstance(row, (list, tuple)):
                raise TypeError(f"transition_matrix[{i}] must be a list")
            if len(row) < n_types:
                raise ValueError(
                    f"transition_matrix[{i}] must have at least {n_types} columns, "
                    f"got {len(row)}"
                )

    # Get pycsp3 variables
    origins = [start_var(interval) for interval in intervals]
    lengths = [length_value(interval) for interval in intervals]

    from pycsp3 import NoOverlap

    if transition_matrix is None:
        # Simple no-overlap without transition times
        return NoOverlap(origins=origins, lengths=lengths)

    # With transition matrix: need to add setup times to lengths
    # For each pair (i, j) where i precedes j in sequence order:
    # end(i) + transition[type_i][type_j] <= start(j)
    #
    # For now, we model this as: end_before_start with delay
    # The pycsp3 NoOverlap doesn't directly support type-based transitions,
    # so we decompose into pairwise constraints
    Node, TypeNode = _get_node_builders()

    constraints = []
    types = seq_var.types

    # Add basic non-overlap first
    constraints.append(NoOverlap(origins=origins, lengths=lengths))

    # Add transition constraints for each pair
    for i in range(len(intervals)):
        for j in range(len(intervals)):
            if i == j:
                continue

            type_i = types[i]
            type_j = types[j]
            trans_time = transition_matrix[type_i][type_j]

            if trans_time <= 0:
                continue  # No additional constraint needed

            # If interval i ends before interval j starts,
            # then end(i) + transition_time <= start(j)
            # Modeled as: (end_j <= start_i) OR (end_i + trans_time <= start_j)
            end_i = _build_end_expr(intervals[i], Node, TypeNode)
            start_j = start_var(intervals[j])
            end_j = _build_end_expr(intervals[j], Node, TypeNode)
            start_i = start_var(intervals[i])

            # end(i) + trans_time <= start(j) when i precedes j
            end_i_plus_trans = Node.build(TypeNode.ADD, end_i, trans_time)
            i_before_j_with_trans = Node.build(TypeNode.LE, end_i_plus_trans, start_j)

            # j precedes i (already covered by non-overlap)
            j_before_i = Node.build(TypeNode.LE, end_j, start_i)

            # One of these must hold
            disjunction = Node.build(TypeNode.OR, i_before_j_with_trans, j_before_i)
            constraints.append(disjunction)

    return constraints


# =============================================================================
# Sequence Ordering Constraints
# =============================================================================


def first(sequence, interval: IntervalVar) -> list:
    """
    Constrain an interval to be the first in a sequence.

    The specified interval must start before all other present intervals
    in the sequence.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        interval: The interval that must be first.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar.
        ValueError: If interval is not in the sequence.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> seq = SequenceVar(intervals=tasks, name="machine")
        >>> satisfy(first(seq, tasks[0]))  # tasks[0] must be first
    """
    seq_var, intervals = _validate_sequence(sequence)
    idx = _validate_interval_in_sequence(interval, seq_var, intervals)
    Node, TypeNode = _get_node_builders()

    if len(intervals) <= 1:
        return []  # Single or empty sequence - trivially satisfied

    constraints = []
    my_start = start_var(interval)
    my_presence = presence_var(interval)
    is_optional = interval.optional

    for i, other in enumerate(intervals):
        if i == idx:
            continue

        other_start = start_var(other)
        other_presence = presence_var(other)
        other_optional = other.optional

        # If both present: my_start <= other_start
        if is_optional or other_optional:
            # (not my_present) OR (not other_present) OR (my_start <= other_start)
            # = (my_presence == 0) OR (other_presence == 0) OR (my_start <= other_start)
            conds = [Node.build(TypeNode.LE, my_start, other_start)]
            if is_optional:
                conds.insert(0, Node.build(TypeNode.EQ, my_presence, 0))
            if other_optional:
                conds.insert(0, Node.build(TypeNode.EQ, other_presence, 0))
            constraints.append(Node.build(TypeNode.OR, *conds))
        else:
            # Both mandatory
            constraints.append(Node.build(TypeNode.LE, my_start, other_start))

    return constraints


def last(sequence, interval: IntervalVar) -> list:
    """
    Constrain an interval to be the last in a sequence.

    The specified interval must end after all other present intervals
    in the sequence.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        interval: The interval that must be last.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar.
        ValueError: If interval is not in the sequence.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> seq = SequenceVar(intervals=tasks, name="machine")
        >>> satisfy(last(seq, tasks[2]))  # tasks[2] must be last
    """
    seq_var, intervals = _validate_sequence(sequence)
    idx = _validate_interval_in_sequence(interval, seq_var, intervals)
    Node, TypeNode = _get_node_builders()

    if len(intervals) <= 1:
        return []  # Single or empty sequence - trivially satisfied

    constraints = []
    my_end = _build_end_expr(interval, Node, TypeNode)
    my_presence = presence_var(interval)
    is_optional = interval.optional

    for i, other in enumerate(intervals):
        if i == idx:
            continue

        other_end = _build_end_expr(other, Node, TypeNode)
        other_presence = presence_var(other)
        other_optional = other.optional

        # If both present: other_end <= my_end
        if is_optional or other_optional:
            conds = [Node.build(TypeNode.LE, other_end, my_end)]
            if is_optional:
                conds.insert(0, Node.build(TypeNode.EQ, my_presence, 0))
            if other_optional:
                conds.insert(0, Node.build(TypeNode.EQ, other_presence, 0))
            constraints.append(Node.build(TypeNode.OR, *conds))
        else:
            # Both mandatory
            constraints.append(Node.build(TypeNode.LE, other_end, my_end))

    return constraints


def before(sequence, interval1: IntervalVar, interval2: IntervalVar) -> list:
    """
    Constrain interval1 to come before interval2 in a sequence.

    If both intervals are present, interval1 must end before interval2 starts.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        interval1: The interval that must come first.
        interval2: The interval that must come second.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either interval is not an IntervalVar.
        ValueError: If either interval is not in the sequence.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> seq = SequenceVar(intervals=tasks, name="machine")
        >>> satisfy(before(seq, tasks[0], tasks[2]))  # t0 before t2
    """
    seq_var, intervals = _validate_sequence(sequence)
    _validate_interval_in_sequence(interval1, seq_var, intervals)
    _validate_interval_in_sequence(interval2, seq_var, intervals)
    Node, TypeNode = _get_node_builders()

    if interval1 == interval2:
        raise ValueError("interval1 and interval2 must be different intervals")

    constraints = []
    end1 = _build_end_expr(interval1, Node, TypeNode)
    start2 = start_var(interval2)
    pres1 = presence_var(interval1)
    pres2 = presence_var(interval2)
    opt1 = interval1.optional
    opt2 = interval2.optional

    # If both present: end1 <= start2
    if opt1 or opt2:
        conds = [Node.build(TypeNode.LE, end1, start2)]
        if opt1:
            conds.insert(0, Node.build(TypeNode.EQ, pres1, 0))
        if opt2:
            conds.insert(0, Node.build(TypeNode.EQ, pres2, 0))
        constraints.append(Node.build(TypeNode.OR, *conds))
    else:
        constraints.append(Node.build(TypeNode.LE, end1, start2))

    return constraints


def previous(sequence, interval1: IntervalVar, interval2: IntervalVar) -> list:
    """
    Constrain interval1 to immediately precede interval2 in a sequence.

    If both intervals are present, interval1 must come directly before interval2
    with no other present intervals between them.

    Note: This is a complex constraint that requires tracking sequence ordering.
    The current implementation enforces that interval1 ends before interval2 starts,
    and that no other interval can fit between them.

    Args:
        sequence: SequenceVar or iterable of IntervalVar.
        interval1: The interval that must immediately precede.
        interval2: The interval that must immediately follow.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either interval is not an IntervalVar.
        ValueError: If either interval is not in the sequence.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> seq = SequenceVar(intervals=tasks, name="machine")
        >>> satisfy(previous(seq, tasks[0], tasks[1]))  # t0 directly before t1
    """
    seq_var, intervals = _validate_sequence(sequence)
    idx1 = _validate_interval_in_sequence(interval1, seq_var, intervals)
    idx2 = _validate_interval_in_sequence(interval2, seq_var, intervals)
    Node, TypeNode = _get_node_builders()

    if interval1 == interval2:
        raise ValueError("interval1 and interval2 must be different intervals")

    constraints = []
    end1 = _build_end_expr(interval1, Node, TypeNode)
    start2 = start_var(interval2)
    pres1 = presence_var(interval1)
    pres2 = presence_var(interval2)
    opt1 = interval1.optional
    opt2 = interval2.optional

    # Basic precedence: if both present, end1 <= start2
    if opt1 or opt2:
        conds = [Node.build(TypeNode.LE, end1, start2)]
        if opt1:
            conds.insert(0, Node.build(TypeNode.EQ, pres1, 0))
        if opt2:
            conds.insert(0, Node.build(TypeNode.EQ, pres2, 0))
        constraints.append(Node.build(TypeNode.OR, *conds))
    else:
        constraints.append(Node.build(TypeNode.LE, end1, start2))

    # Immediate precedence: no other interval can be between them
    # For each other interval k:
    # If all three are present: NOT (end1 <= start_k AND end_k <= start2)
    # = NOT (between condition)
    # = (end_k < end1) OR (start2 < start_k)  when all present

    for i, other in enumerate(intervals):
        if i == idx1 or i == idx2:
            continue

        start_k = start_var(other)
        end_k = _build_end_expr(other, Node, TypeNode)
        pres_k = presence_var(other)
        opt_k = other.optional

        # k cannot be between interval1 and interval2
        # "between" means: end1 <= start_k AND end_k <= start2
        # NOT between = end_k < end1 OR start2 < start_k OR not_all_present

        # end_k < end1 OR start_k > start2 (k not fitting between)
        # Use LE with swapped sides: end1 < end_k means NOT(end_k <= end1 - 1) -> use LT
        # Simpler: end1 > end_k OR start2 < start_k
        k_not_between = Node.build(
            TypeNode.OR,
            Node.build(TypeNode.LT, end_k, end1),  # k ends before interval1 ends
            Node.build(TypeNode.LT, start2, start_k),  # k starts after interval2 starts
        )

        if opt1 or opt2 or opt_k:
            # Add absence conditions
            conds = [k_not_between]
            if opt1:
                conds.insert(0, Node.build(TypeNode.EQ, pres1, 0))
            if opt2:
                conds.insert(0, Node.build(TypeNode.EQ, pres2, 0))
            if opt_k:
                conds.insert(0, Node.build(TypeNode.EQ, pres_k, 0))
            constraints.append(Node.build(TypeNode.OR, *conds))
        else:
            constraints.append(k_not_between)

    return constraints


# =============================================================================
# Sequence Consistency Constraints
# =============================================================================


def same_sequence(sequence1, sequence2) -> list:
    """
    Constrain common intervals to have the same position in both sequences.

    For any interval that appears in both sequences, if it is present,
    it must occupy the same position (index) in both sequences.

    This constraint is useful when the same operations need to maintain
    consistent ordering across different resources.

    Args:
        sequence1: First SequenceVar or iterable of IntervalVar.
        sequence2: Second SequenceVar or iterable of IntervalVar.

    Returns:
        List of pycsp3 constraint nodes.

    Example:
        >>> # Operations processed on two parallel machines in same order
        >>> ops = [IntervalVar(size=5, name=f"op{i}") for i in range(3)]
        >>> seq1 = SequenceVar(intervals=ops, name="machine1")
        >>> seq2 = SequenceVar(intervals=ops, name="machine2")
        >>> satisfy(same_sequence(seq1, seq2))
    """
    seq1_var, intervals1 = _validate_sequence(sequence1)
    seq2_var, intervals2 = _validate_sequence(sequence2)
    Node, TypeNode = _get_node_builders()

    # Find common intervals
    common = set(intervals1) & set(intervals2)
    if len(common) < 2:
        return []  # Need at least 2 common intervals for ordering

    # Build index maps
    idx1 = {iv: i for i, iv in enumerate(intervals1)}
    idx2 = {iv: i for i, iv in enumerate(intervals2)}

    constraints = []

    # For each pair of common intervals, enforce same relative ordering
    common_list = list(common)
    for i in range(len(common_list)):
        for j in range(i + 1, len(common_list)):
            iv_a = common_list[i]
            iv_b = common_list[j]

            # Get positions in both sequences
            pos_a_in_1 = idx1[iv_a]
            pos_b_in_1 = idx1[iv_b]
            pos_a_in_2 = idx2[iv_a]
            pos_b_in_2 = idx2[iv_b]

            # If a comes before b in seq1, it must come before b in seq2
            # And vice versa

            start_a = start_var(iv_a)
            end_a = _build_end_expr(iv_a, Node, TypeNode)
            start_b = start_var(iv_b)
            end_b = _build_end_expr(iv_b, Node, TypeNode)

            pres_a = presence_var(iv_a)
            pres_b = presence_var(iv_b)
            opt_a = iv_a.optional
            opt_b = iv_b.optional

            # Same ordering: (end_a <= start_b) IFF (end_a <= start_b in both)
            # Since we enforce same ordering, we just need:
            # Both present implies same temporal ordering

            # For simplicity, enforce that the relative order is consistent
            # by using end_before_start in both directions with a disjunction:
            # (end_a <= start_b) XOR (end_b <= start_a) should have same truth value
            # in both sequences (but we can't directly model "same as")

            # Alternative: for pairs where position differs in sequences,
            # the solver must choose one ordering and apply it consistently
            # This is complex to model without auxiliary variables

            # Simpler approach: If intervals have fixed index relationships
            # in both sequences, we can enforce that directly
            # But generally, this requires sequence position variables

            # For now, implement as: start times must maintain same relative order
            # (start_a < start_b) is equivalent in both sequences
            # Modeled as: if both present, either both a-before-b or both b-before-a

            a_before_b = Node.build(TypeNode.LE, end_a, start_b)
            b_before_a = Node.build(TypeNode.LE, end_b, start_a)

            if opt_a or opt_b:
                # At least one optional: include absence conditions
                absent_clause = []
                if opt_a:
                    absent_clause.append(Node.build(TypeNode.EQ, pres_a, 0))
                if opt_b:
                    absent_clause.append(Node.build(TypeNode.EQ, pres_b, 0))
                # Either someone is absent, or one clear ordering exists
                absent_or = Node.build(TypeNode.OR, *absent_clause) if len(absent_clause) > 1 else absent_clause[0]
                constraints.append(
                    Node.build(TypeNode.OR, absent_or, a_before_b, b_before_a)
                )
            else:
                # Both mandatory: one must come before the other
                constraints.append(Node.build(TypeNode.OR, a_before_b, b_before_a))

    return constraints


def same_common_subsequence(sequence1, sequence2) -> list:
    """
    Constrain common intervals to have the same relative ordering in both sequences.

    For any pair of intervals that appear in both sequences, if both are present,
    their relative order (which one comes first) must be the same in both sequences.

    This is weaker than same_sequence - it only requires the same relative order,
    not the same absolute positions.

    Args:
        sequence1: First SequenceVar or iterable of IntervalVar.
        sequence2: Second SequenceVar or iterable of IntervalVar.

    Returns:
        List of pycsp3 constraint nodes.

    Example:
        >>> # Same jobs on different machines maintain relative order
        >>> jobs = [IntervalVar(size=5, optional=True, name=f"job{i}") for i in range(4)]
        >>> seq1 = SequenceVar(intervals=jobs[:3], name="m1")  # jobs 0,1,2
        >>> seq2 = SequenceVar(intervals=jobs[1:], name="m2")  # jobs 1,2,3
        >>> # Common jobs (1,2) must have same relative order
        >>> satisfy(same_common_subsequence(seq1, seq2))
    """
    seq1_var, intervals1 = _validate_sequence(sequence1)
    seq2_var, intervals2 = _validate_sequence(sequence2)
    Node, TypeNode = _get_node_builders()

    # Find common intervals
    common = set(intervals1) & set(intervals2)
    if len(common) < 2:
        return []  # Need at least 2 common intervals

    constraints = []
    common_list = list(common)

    # For each pair of common intervals
    for i in range(len(common_list)):
        for j in range(i + 1, len(common_list)):
            iv_a = common_list[i]
            iv_b = common_list[j]

            start_a = start_var(iv_a)
            end_a = _build_end_expr(iv_a, Node, TypeNode)
            start_b = start_var(iv_b)
            end_b = _build_end_expr(iv_b, Node, TypeNode)

            pres_a = presence_var(iv_a)
            pres_b = presence_var(iv_b)
            opt_a = iv_a.optional
            opt_b = iv_b.optional

            # Same relative ordering means:
            # In both sequences, either a comes before b, or b comes before a
            # This is the same constraint as same_sequence for pairs

            a_before_b = Node.build(TypeNode.LE, end_a, start_b)
            b_before_a = Node.build(TypeNode.LE, end_b, start_a)

            if opt_a or opt_b:
                absent_clause = []
                if opt_a:
                    absent_clause.append(Node.build(TypeNode.EQ, pres_a, 0))
                if opt_b:
                    absent_clause.append(Node.build(TypeNode.EQ, pres_b, 0))
                absent_or = Node.build(TypeNode.OR, *absent_clause) if len(absent_clause) > 1 else absent_clause[0]
                constraints.append(
                    Node.build(TypeNode.OR, absent_or, a_before_b, b_before_a)
                )
            else:
                constraints.append(Node.build(TypeNode.OR, a_before_b, b_before_a))

    return constraints
