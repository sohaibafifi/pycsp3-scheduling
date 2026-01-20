"""
Overlap constraints for interval variables.

This module provides constraints that enforce or prevent overlap between intervals:

1. **must_overlap(a, b)**: Two intervals must share some time
2. **overlap_at_least(a, b, min_overlap)**: Intervals must overlap by at least min_overlap
3. **no_overlap_pairwise(intervals)**: Simple pairwise no-overlap without sequence variable
4. **disjunctive(intervals, transition_times)**: At most one interval active at any time

All constraints return pycsp3 Node objects that can be used with satisfy().
"""

from __future__ import annotations

from typing import Sequence

from pycsp3_scheduling.constraints._pycsp3 import (
    _build_end_expr,
    _get_node_builders,
    _validate_interval,
    _validate_intervals,
    length_value,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar


# =============================================================================
# Overlap Constraints
# =============================================================================


def must_overlap(a: IntervalVar, b: IntervalVar) -> list:
    """
    Constrain two intervals to share at least some time (overlap).

    The intervals must have a non-zero overlap duration.

    Args:
        a: First interval.
        b: Second interval.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either argument is not an IntervalVar.

    Semantics:
        - `start(a) < end(b) AND start(b) < end(a)`
        - When either interval is optional and absent, the constraint behavior
          depends on the use case. By default, both must be present for the
          constraint to be meaningful.

    Example:
        >>> meeting = IntervalVar(size=60, name="meeting")
        >>> availability = IntervalVar(start=9*60, end=17*60, size=480, name="available")
        >>> # Meeting must occur during availability
        >>> satisfy(must_overlap(meeting, availability))
    """
    _validate_interval(a, "must_overlap")
    _validate_interval(b, "must_overlap")

    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    end_a = _build_end_expr(a, Node, TypeNode)
    start_b = start_var(b)
    end_b = _build_end_expr(b, Node, TypeNode)

    # Overlap: start(a) < end(b) AND start(b) < end(a)
    cond1 = Node.build(TypeNode.LT, start_a, end_b)
    cond2 = Node.build(TypeNode.LT, start_b, end_a)
    overlap_constraint = Node.build(TypeNode.AND, cond1, cond2)

    # Handle optional intervals
    opt_a = a.optional
    opt_b = b.optional

    if opt_a or opt_b:
        # When optional, require both to be present for overlap
        # (a absent) OR (b absent) OR (overlap)
        disjuncts = [overlap_constraint]

        if opt_a:
            pres_a = presence_var(a)
            disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

        if opt_b:
            pres_b = presence_var(b)
            disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

        return [Node.build(TypeNode.OR, *disjuncts)]

    return [overlap_constraint]


def overlap_at_least(a: IntervalVar, b: IntervalVar, min_overlap: int) -> list:
    """
    Constrain two intervals to overlap by at least a minimum duration.

    Args:
        a: First interval.
        b: Second interval.
        min_overlap: Minimum required overlap duration.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If intervals are not IntervalVar or min_overlap is not int.
        ValueError: If min_overlap is negative.

    Semantics:
        - `overlap_length(a, b) >= min_overlap`
        - Where overlap_length = max(0, min(end(a), end(b)) - max(start(a), start(b)))

    Example:
        >>> mentor = IntervalVar(size=120, name="mentor_shift")
        >>> trainee = IntervalVar(size=120, name="trainee_shift")
        >>> # Must overlap by at least 30 minutes for handoff
        >>> satisfy(overlap_at_least(mentor, trainee, 30))
    """
    _validate_interval(a, "overlap_at_least")
    _validate_interval(b, "overlap_at_least")

    if not isinstance(min_overlap, int):
        raise TypeError("min_overlap must be an integer")
    if min_overlap < 0:
        raise ValueError("min_overlap must be non-negative")

    if min_overlap == 0:
        return []  # Always satisfied

    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    end_a = _build_end_expr(a, Node, TypeNode)
    start_b = start_var(b)
    end_b = _build_end_expr(b, Node, TypeNode)

    # overlap_length = min(end_a, end_b) - max(start_a, start_b)
    # We need: overlap_length >= min_overlap
    # Which means: min(end_a, end_b) - max(start_a, start_b) >= min_overlap
    # Rearranged: min(end_a, end_b) >= max(start_a, start_b) + min_overlap

    min_end = Node.build(TypeNode.MIN, end_a, end_b)
    max_start = Node.build(TypeNode.MAX, start_a, start_b)
    rhs = Node.build(TypeNode.ADD, max_start, min_overlap)

    overlap_constraint = Node.build(TypeNode.GE, min_end, rhs)

    # Handle optional intervals
    opt_a = a.optional
    opt_b = b.optional

    if opt_a or opt_b:
        disjuncts = [overlap_constraint]

        if opt_a:
            pres_a = presence_var(a)
            disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

        if opt_b:
            pres_b = presence_var(b)
            disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

        return [Node.build(TypeNode.OR, *disjuncts)]

    return [overlap_constraint]


def no_overlap_pairwise(intervals: Sequence[IntervalVar]) -> list:
    """
    Constrain intervals to not overlap, using simple pairwise decomposition.

    This is a simpler alternative to SeqNoOverlap when you don't need
    sequence ordering or transition times.

    Args:
        intervals: List of intervals that cannot overlap.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar.

    Semantics:
        - For each pair (i, j): `end(i) <= start(j) OR end(j) <= start(i)`
        - O(n²) constraints for n intervals

    Example:
        >>> meetings = [IntervalVar(size=30, name=f"meeting_{i}") for i in range(5)]
        >>> # No two meetings can overlap
        >>> satisfy(no_overlap_pairwise(meetings))
    """
    intervals = _validate_intervals(intervals, "no_overlap_pairwise")

    if len(intervals) < 2:
        return []

    Node, TypeNode = _get_node_builders()
    constraints = []

    for i in range(len(intervals) - 1):
        for j in range(i + 1, len(intervals)):
            iv_a = intervals[i]
            iv_b = intervals[j]

            start_a = start_var(iv_a)
            end_a = _build_end_expr(iv_a, Node, TypeNode)
            start_b = start_var(iv_b)
            end_b = _build_end_expr(iv_b, Node, TypeNode)

            # No overlap: end(a) <= start(b) OR end(b) <= start(a)
            a_before_b = Node.build(TypeNode.LE, end_a, start_b)
            b_before_a = Node.build(TypeNode.LE, end_b, start_a)
            no_overlap = Node.build(TypeNode.OR, a_before_b, b_before_a)

            # Handle optional intervals
            opt_a = iv_a.optional
            opt_b = iv_b.optional

            if opt_a or opt_b:
                disjuncts = [no_overlap]

                if opt_a:
                    pres_a = presence_var(iv_a)
                    disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

                if opt_b:
                    pres_b = presence_var(iv_b)
                    disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

                constraints.append(Node.build(TypeNode.OR, *disjuncts))
            else:
                constraints.append(no_overlap)

    return constraints


def disjunctive(
    intervals: Sequence[IntervalVar],
    transition_times: Sequence[Sequence[int]] | None = None,
) -> list:
    """
    Constrain that at most one interval can be active at any time (unary resource).

    This is equivalent to SeqNoOverlap but without creating a SequenceVar.
    Use this when you don't need sequence ordering expressions.

    Args:
        intervals: List of intervals sharing the unary resource.
        transition_times: Optional transition time matrix. If provided,
            intervals must have types assigned and transition_times[i][j]
            is the minimum time between an interval of type i and type j.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar.
        ValueError: If transition_times provided but intervals don't have types.

    Semantics:
        - For any two intervals: they cannot overlap in time
        - With transition_times: additional setup time required between types

    Example:
        >>> tasks = [IntervalVar(size=d, name=f"task_{i}") for i, d in enumerate(durations)]
        >>> # Single machine - only one task at a time
        >>> satisfy(disjunctive(tasks))
    """
    intervals = _validate_intervals(intervals, "disjunctive")

    if len(intervals) < 2:
        return []

    # If no transition times, use simple pairwise no-overlap
    if transition_times is None:
        return no_overlap_pairwise(intervals)

    # With transition times, we need interval types
    # For now, assume intervals have a 'type' attribute or use index
    Node, TypeNode = _get_node_builders()
    constraints = []

    # Check if intervals have types
    types = []
    for i, iv in enumerate(intervals):
        if hasattr(iv, 'type') and iv.type is not None:
            types.append(iv.type)
        else:
            # Default to index if no type specified
            types.append(i)

    n_types = len(transition_times)
    for t in types:
        if t < 0 or t >= n_types:
            raise ValueError(
                f"disjunctive: interval type {t} is out of range for "
                f"transition_times matrix of size {n_types}"
            )

    for i in range(len(intervals) - 1):
        for j in range(i + 1, len(intervals)):
            iv_a = intervals[i]
            iv_b = intervals[j]
            type_a = types[i]
            type_b = types[j]

            start_a = start_var(iv_a)
            end_a = _build_end_expr(iv_a, Node, TypeNode)
            start_b = start_var(iv_b)
            end_b = _build_end_expr(iv_b, Node, TypeNode)

            # Transition times
            trans_a_to_b = transition_times[type_a][type_b]
            trans_b_to_a = transition_times[type_b][type_a]

            # No overlap with transitions:
            # end(a) + trans_a_to_b <= start(b) OR end(b) + trans_b_to_a <= start(a)
            if trans_a_to_b > 0:
                end_a_plus = Node.build(TypeNode.ADD, end_a, trans_a_to_b)
                a_before_b = Node.build(TypeNode.LE, end_a_plus, start_b)
            else:
                a_before_b = Node.build(TypeNode.LE, end_a, start_b)

            if trans_b_to_a > 0:
                end_b_plus = Node.build(TypeNode.ADD, end_b, trans_b_to_a)
                b_before_a = Node.build(TypeNode.LE, end_b_plus, start_a)
            else:
                b_before_a = Node.build(TypeNode.LE, end_b, start_a)

            no_overlap = Node.build(TypeNode.OR, a_before_b, b_before_a)

            # Handle optional intervals
            opt_a = iv_a.optional
            opt_b = iv_b.optional

            if opt_a or opt_b:
                disjuncts = [no_overlap]

                if opt_a:
                    pres_a = presence_var(iv_a)
                    disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

                if opt_b:
                    pres_b = presence_var(iv_b)
                    disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

                constraints.append(Node.build(TypeNode.OR, *disjuncts))
            else:
                constraints.append(no_overlap)

    return constraints
