"""
Bounds constraints for interval variables.

This module provides convenience constraints for setting time bounds on intervals:

1. **release_date(interval, time)**: Interval cannot start before given time
2. **deadline(interval, time)**: Interval must complete by given time
3. **time_window(interval, earliest_start, latest_end)**: Combined release + deadline

All constraints return pycsp3 Node objects that can be used with satisfy().
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import (
    _build_end_expr,
    _get_node_builders,
    _validate_interval,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar


# =============================================================================
# Bounds Constraints
# =============================================================================


def release_date(interval: IntervalVar, time: int) -> list:
    """
    Constrain an interval to not start before a given time.

    The interval's start time must be >= the release date.

    Args:
        interval: The interval variable to constrain.
        time: The earliest allowed start time (release date).

    Returns:
        List of pycsp3 constraint nodes.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> satisfy(release_date(task, 8))  # Cannot start before time 8
    """
    _validate_interval(interval, "release_date")
    if not isinstance(time, int):
        raise TypeError(f"release_date: time must be an integer, got {type(time).__name__}")

    Node, TypeNode = _get_node_builders()

    start = start_var(interval)
    constraint = Node.build(TypeNode.GE, start, time)

    # Handle optional intervals
    if interval.optional:
        pres = presence_var(interval)
        # (presence == 0) OR (start >= time)
        not_present = Node.build(TypeNode.EQ, pres, 0)
        constraint = Node.build(TypeNode.OR, not_present, constraint)

    return [constraint]


def deadline(interval: IntervalVar, time: int) -> list:
    """
    Constrain an interval to complete by a given time.

    The interval's end time must be <= the deadline.

    Args:
        interval: The interval variable to constrain.
        time: The latest allowed end time (deadline).

    Returns:
        List of pycsp3 constraint nodes.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> satisfy(deadline(task, 50))  # Must finish by time 50
    """
    _validate_interval(interval, "deadline")
    if not isinstance(time, int):
        raise TypeError(f"deadline: time must be an integer, got {type(time).__name__}")

    Node, TypeNode = _get_node_builders()

    end = _build_end_expr(interval, Node, TypeNode)
    constraint = Node.build(TypeNode.LE, end, time)

    # Handle optional intervals
    if interval.optional:
        pres = presence_var(interval)
        # (presence == 0) OR (end <= time)
        not_present = Node.build(TypeNode.EQ, pres, 0)
        constraint = Node.build(TypeNode.OR, not_present, constraint)

    return [constraint]


def time_window(interval: IntervalVar, earliest_start: int, latest_end: int) -> list:
    """
    Constrain an interval to execute within a time window.

    Combines release_date and deadline constraints.

    Args:
        interval: The interval variable to constrain.
        earliest_start: The earliest allowed start time.
        latest_end: The latest allowed end time.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        ValueError: If earliest_start > latest_end.

    Example:
        >>> delivery = IntervalVar(size=30, name="delivery")
        >>> # Delivery must occur during business hours (9am-5pm as minutes)
        >>> satisfy(time_window(delivery, earliest_start=9*60, latest_end=17*60))
    """
    _validate_interval(interval, "time_window")
    if not isinstance(earliest_start, int):
        raise TypeError(
            f"time_window: earliest_start must be an integer, got {type(earliest_start).__name__}"
        )
    if not isinstance(latest_end, int):
        raise TypeError(
            f"time_window: latest_end must be an integer, got {type(latest_end).__name__}"
        )
    if earliest_start > latest_end:
        raise ValueError(
            f"time_window: earliest_start ({earliest_start}) must be <= latest_end ({latest_end})"
        )

    # Combine release_date and deadline constraints
    return release_date(interval, earliest_start) + deadline(interval, latest_end)
