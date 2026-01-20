"""
Forbidden time constraints for interval variables.

This module provides constraints that prevent intervals from starting, ending,
or spanning during specific time periods:

1. **forbid_start(interval, forbidden_periods)**: Cannot start during forbidden periods
2. **forbid_end(interval, forbidden_periods)**: Cannot end during forbidden periods
3. **forbid_extent(interval, forbidden_periods)**: Cannot overlap forbidden periods

All constraints return pycsp3 Node objects that can be used with satisfy().

Absent interval semantics:
- When interval is present: constraint is enforced
- When interval is absent: constraint is trivially satisfied
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Sequence

from pycsp3_scheduling.constraints._pycsp3 import (
    _get_node_builders,
    _validate_interval,
    length_value,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar


def _validate_periods(
    periods: Sequence[tuple[int, int]] | Iterable[tuple[int, int]], func_name: str
) -> list[tuple[int, int]]:
    """Validate and normalize forbidden periods."""
    result = []
    for i, period in enumerate(periods):
        if not isinstance(period, (list, tuple)) or len(period) != 2:
            raise TypeError(
                f"{func_name}: forbidden_periods[{i}] must be a (start, end) tuple"
            )
        start, end = period
        if not isinstance(start, int) or not isinstance(end, int):
            raise TypeError(
                f"{func_name}: forbidden_periods[{i}] must contain integers"
            )
        if start >= end:
            raise ValueError(
                f"{func_name}: forbidden_periods[{i}] must have start < end, "
                f"got ({start}, {end})"
            )
        result.append((start, end))
    return result


def _build_end_expr(interval: IntervalVar, Node, TypeNode):
    """Build end expression: start + length."""
    start = start_var(interval)
    length = length_value(interval)
    if isinstance(length, int) and length == 0:
        return start
    return Node.build(TypeNode.ADD, start, length)


# =============================================================================
# Forbidden Time Constraints
# =============================================================================


def forbid_start(
    interval: IntervalVar,
    forbidden_periods: Sequence[tuple[int, int]],
) -> list:
    """
    Constrain the interval to not start during any of the forbidden time periods.

    For each forbidden period (s, e), the interval's start time must not be
    in the range [s, e). That is: NOT (s <= start < e).

    Args:
        interval: The interval variable to constrain.
        forbidden_periods: List of (start, end) tuples defining forbidden periods.
            Each period is a half-open interval [start, end).

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar or periods are malformed.
        ValueError: If any period has start >= end.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # Cannot start during lunch break (12-13) or after hours (17-24)
        >>> satisfy(forbid_start(task, [(12, 13), (17, 24)]))
    """
    _validate_interval(interval, "forbid_start")
    periods = _validate_periods(forbidden_periods, "forbid_start")

    if not periods:
        return []

    Node, TypeNode = _get_node_builders()
    constraints = []

    start = start_var(interval)
    is_optional = interval.optional

    for period_start, period_end in periods:
        # NOT (period_start <= start < period_end)
        # = (start < period_start) OR (start >= period_end)
        before_period = Node.build(TypeNode.LT, start, period_start)
        after_period = Node.build(TypeNode.GE, start, period_end)

        if is_optional:
            # (presence == 0) OR (start < period_start) OR (start >= period_end)
            pres = presence_var(interval)
            absent = Node.build(TypeNode.EQ, pres, 0)
            constraint = Node.build(TypeNode.OR, absent, before_period, after_period)
        else:
            constraint = Node.build(TypeNode.OR, before_period, after_period)

        constraints.append(constraint)

    return constraints


def forbid_end(
    interval: IntervalVar,
    forbidden_periods: Sequence[tuple[int, int]],
) -> list:
    """
    Constrain the interval to not end during any of the forbidden time periods.

    For each forbidden period (s, e), the interval's end time must not be
    in the range (s, e]. That is: NOT (s < end <= e).

    Args:
        interval: The interval variable to constrain.
        forbidden_periods: List of (start, end) tuples defining forbidden periods.
            Each period is a half-open interval (start, end].

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar or periods are malformed.
        ValueError: If any period has start >= end.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # Cannot end during maintenance window
        >>> satisfy(forbid_end(task, [(6, 8)]))
    """
    _validate_interval(interval, "forbid_end")
    periods = _validate_periods(forbidden_periods, "forbid_end")

    if not periods:
        return []

    Node, TypeNode = _get_node_builders()
    constraints = []

    end = _build_end_expr(interval, Node, TypeNode)
    is_optional = interval.optional

    for period_start, period_end in periods:
        # NOT (period_start < end <= period_end)
        # = (end <= period_start) OR (end > period_end)
        before_or_at_start = Node.build(TypeNode.LE, end, period_start)
        after_period = Node.build(TypeNode.GT, end, period_end)

        if is_optional:
            pres = presence_var(interval)
            absent = Node.build(TypeNode.EQ, pres, 0)
            constraint = Node.build(TypeNode.OR, absent, before_or_at_start, after_period)
        else:
            constraint = Node.build(TypeNode.OR, before_or_at_start, after_period)

        constraints.append(constraint)

    return constraints


def forbid_extent(
    interval: IntervalVar,
    forbidden_periods: Sequence[tuple[int, int]],
) -> list:
    """
    Constrain the interval to not overlap any of the forbidden time periods.

    For each forbidden period (s, e), the interval must be completely before
    or completely after. That is: (end <= s) OR (start >= e).

    Args:
        interval: The interval variable to constrain.
        forbidden_periods: List of (start, end) tuples defining forbidden periods.
            The interval cannot span across any of these periods.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar or periods are malformed.
        ValueError: If any period has start >= end.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # Task cannot span across lunch break - must be entirely before or after
        >>> satisfy(forbid_extent(task, [(12, 13)]))
    """
    _validate_interval(interval, "forbid_extent")
    periods = _validate_periods(forbidden_periods, "forbid_extent")

    if not periods:
        return []

    Node, TypeNode = _get_node_builders()
    constraints = []

    start = start_var(interval)
    end = _build_end_expr(interval, Node, TypeNode)
    is_optional = interval.optional

    for period_start, period_end in periods:
        # No overlap: (end <= period_start) OR (start >= period_end)
        ends_before = Node.build(TypeNode.LE, end, period_start)
        starts_after = Node.build(TypeNode.GE, start, period_end)

        if is_optional:
            pres = presence_var(interval)
            absent = Node.build(TypeNode.EQ, pres, 0)
            constraint = Node.build(TypeNode.OR, absent, ends_before, starts_after)
        else:
            constraint = Node.build(TypeNode.OR, ends_before, starts_after)

        constraints.append(constraint)

    return constraints
