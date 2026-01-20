"""
Aggregate expressions for collections of interval variables.

This module provides expressions that compute aggregate values over
collections of intervals:

1. **count_present(intervals)**: Count how many intervals are present
2. **earliest_start(intervals)**: Minimum start time among present intervals
3. **latest_end(intervals)**: Maximum end time among present intervals
4. **span_length(intervals)**: Total span from earliest start to latest end

These expressions return pycsp3 Node objects that can be used in constraints
or objectives.
"""

from __future__ import annotations

from typing import Sequence

from pycsp3_scheduling.constraints._pycsp3 import (
    _build_end_expr,
    _get_node_builders,
    _validate_intervals as _validate_intervals_base,
    length_value,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import INTERVAL_MAX, INTERVAL_MIN, IntervalVar


def _validate_intervals(intervals: Sequence[IntervalVar], func_name: str) -> list[IntervalVar]:
    """Validate intervals for aggregate expressions (requires at least 1)."""
    result = _validate_intervals_base(intervals, func_name)
    if not result:
        raise ValueError(f"{func_name} requires at least one interval")
    return result


# =============================================================================
# Aggregate Expressions
# =============================================================================


def count_present(intervals: Sequence[IntervalVar]) -> "Node":
    """
    Expression counting how many intervals are present.

    Args:
        intervals: List of interval variables (can be optional or mandatory).

    Returns:
        A pycsp3 Node representing the sum of presence values.

    Raises:
        TypeError: If any element is not an IntervalVar.
        ValueError: If intervals list is empty.

    Semantics:
        - Returns `sum(presence(i) for i in intervals)`
        - Mandatory intervals contribute 1
        - Optional absent intervals contribute 0

    Example:
        >>> tasks = [IntervalVar(size=10, optional=True, name=f"t_{i}") for i in range(10)]
        >>> # Must complete at least 5 tasks
        >>> satisfy(count_present(tasks) >= 5)
        >>> # Maximize number of completed tasks
        >>> maximize(count_present(tasks))
    """
    intervals = _validate_intervals(intervals, "count_present")

    Node, TypeNode = _get_node_builders()

    # Collect presence values
    presence_values = [presence_var(iv) for iv in intervals]

    if len(presence_values) == 1:
        return presence_values[0]

    return Node.build(TypeNode.ADD, *presence_values)


def earliest_start(
    intervals: Sequence[IntervalVar],
    absent_value: int = INTERVAL_MAX,
) -> "Node":
    """
    Expression for the earliest start time among present intervals.

    Args:
        intervals: List of interval variables.
        absent_value: Value to use for absent optional intervals.
            Defaults to INTERVAL_MAX so absent intervals don't affect the minimum.

    Returns:
        A pycsp3 Node representing min(start(i) for present i).

    Raises:
        TypeError: If any element is not an IntervalVar.
        ValueError: If intervals list is empty.

    Semantics:
        - Returns the minimum start time among all present intervals
        - Absent intervals use absent_value (default: very large, so ignored in min)

    Example:
        >>> tasks = [IntervalVar(size=10, name=f"t_{i}") for i in range(5)]
        >>> # All tasks must start after time 10
        >>> satisfy(earliest_start(tasks) >= 10)
    """
    intervals = _validate_intervals(intervals, "earliest_start")

    Node, TypeNode = _get_node_builders()

    # Build start expressions with conditional for optional intervals
    start_exprs = []
    for iv in intervals:
        start = start_var(iv)
        if iv.optional:
            # If absent, use absent_value; if present, use actual start
            pres = presence_var(iv)
            # start_if_present = if pres then start else absent_value
            # Using: pres * start + (1 - pres) * absent_value
            # But simpler: use IF node if available, or decompose
            # For now, use: (1 - pres) * absent_value + pres * start
            # = absent_value - pres * absent_value + pres * start
            # = absent_value + pres * (start - absent_value)
            diff = Node.build(TypeNode.SUB, start, absent_value)
            scaled = Node.build(TypeNode.MUL, pres, diff)
            expr = Node.build(TypeNode.ADD, absent_value, scaled)
            start_exprs.append(expr)
        else:
            start_exprs.append(start)

    if len(start_exprs) == 1:
        return start_exprs[0]

    return Node.build(TypeNode.MIN, *start_exprs)


def latest_end(
    intervals: Sequence[IntervalVar],
    absent_value: int = INTERVAL_MIN,
) -> "Node":
    """
    Expression for the latest end time among present intervals.

    Args:
        intervals: List of interval variables.
        absent_value: Value to use for absent optional intervals.
            Defaults to INTERVAL_MIN so absent intervals don't affect the maximum.

    Returns:
        A pycsp3 Node representing max(end(i) for present i).

    Raises:
        TypeError: If any element is not an IntervalVar.
        ValueError: If intervals list is empty.

    Semantics:
        - Returns the maximum end time among all present intervals
        - Absent intervals use absent_value (default: very small, so ignored in max)

    Example:
        >>> tasks = [IntervalVar(size=10, name=f"t_{i}") for i in range(5)]
        >>> # Minimize makespan
        >>> minimize(latest_end(tasks))
    """
    intervals = _validate_intervals(intervals, "latest_end")

    Node, TypeNode = _get_node_builders()

    # Build end expressions with conditional for optional intervals
    end_exprs = []
    for iv in intervals:
        end = _build_end_expr(iv, Node, TypeNode)
        if iv.optional:
            # If absent, use absent_value; if present, use actual end
            pres = presence_var(iv)
            # end_if_present = absent_value + pres * (end - absent_value)
            diff = Node.build(TypeNode.SUB, end, absent_value)
            scaled = Node.build(TypeNode.MUL, pres, diff)
            expr = Node.build(TypeNode.ADD, absent_value, scaled)
            end_exprs.append(expr)
        else:
            end_exprs.append(end)

    if len(end_exprs) == 1:
        return end_exprs[0]

    return Node.build(TypeNode.MAX, *end_exprs)


def span_length(
    intervals: Sequence[IntervalVar],
    absent_value: int = 0,
) -> "Node":
    """
    Expression for the total span from earliest start to latest end.

    Args:
        intervals: List of interval variables.
        absent_value: Value to return if all intervals are absent.

    Returns:
        A pycsp3 Node representing latest_end - earliest_start.

    Raises:
        TypeError: If any element is not an IntervalVar.
        ValueError: If intervals list is empty.

    Semantics:
        - Returns `max(end(i)) - min(start(i))` for present intervals
        - This is the makespan if all intervals must be scheduled

    Example:
        >>> tasks = [IntervalVar(size=10, name=f"t_{i}") for i in range(5)]
        >>> # Minimize total span
        >>> minimize(span_length(tasks))
    """
    intervals = _validate_intervals(intervals, "span_length")

    Node, TypeNode = _get_node_builders()

    # Get earliest start and latest end
    earliest = earliest_start(intervals, absent_value=INTERVAL_MAX)
    latest = latest_end(intervals, absent_value=INTERVAL_MIN)

    # Span = latest - earliest
    return Node.build(TypeNode.SUB, latest, earliest)


def makespan(intervals: Sequence[IntervalVar]) -> "Node":
    """
    Expression for the makespan (latest end time) of a set of intervals.

    This is a convenience alias for latest_end() commonly used in scheduling.

    Args:
        intervals: List of interval variables.

    Returns:
        A pycsp3 Node representing max(end(i) for all i).

    Example:
        >>> tasks = [IntervalVar(size=d, name=f"t_{i}") for i, d in enumerate(durations)]
        >>> minimize(makespan(tasks))
    """
    return latest_end(intervals, absent_value=INTERVAL_MIN)
