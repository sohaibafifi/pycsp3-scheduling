"""
Chain constraint for interval variables.

This module provides the chain constraint that enforces sequential execution
of intervals:

1. **chain(intervals, delays)**: Enforce intervals execute in sequence order

The chain constraint is equivalent to multiple end_before_start constraints
but provides a cleaner, more semantic API for common sequential patterns.

All constraints return pycsp3 Node objects that can be used with satisfy().
"""

from __future__ import annotations

from typing import Sequence

from pycsp3_scheduling.constraints._pycsp3 import (
    _get_node_builders,
    _validate_intervals as _validate_intervals_base,
    length_value,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar


def _validate_intervals(intervals: Sequence[IntervalVar], func_name: str) -> list[IntervalVar]:
    """Validate intervals for chain constraint (requires at least 2)."""
    result = _validate_intervals_base(intervals, func_name)
    if len(result) < 2:
        raise ValueError(f"{func_name} requires at least 2 intervals")
    return result


def _validate_delays(
    delays: int | Sequence[int] | None,
    num_intervals: int,
    func_name: str
) -> list[int]:
    """Validate and normalize delays to a list."""
    num_pairs = num_intervals - 1

    if delays is None:
        return [0] * num_pairs

    if isinstance(delays, int):
        return [delays] * num_pairs

    delays_list = list(delays)
    if len(delays_list) != num_pairs:
        raise ValueError(
            f"{func_name}: delays list must have length {num_pairs} "
            f"(number of interval pairs), got {len(delays_list)}"
        )

    for i, d in enumerate(delays_list):
        if not isinstance(d, int):
            raise TypeError(f"{func_name}: delays[{i}] must be an integer")

    return delays_list


def _build_end_expr(interval: IntervalVar, Node, TypeNode):
    """Build end expression: start + length."""
    start = start_var(interval)
    length = length_value(interval)
    if isinstance(length, int) and length == 0:
        return start
    return Node.build(TypeNode.ADD, start, length)


# =============================================================================
# Chain Constraint
# =============================================================================


def chain(
    intervals: Sequence[IntervalVar],
    delays: int | Sequence[int] | None = None,
) -> list:
    """
    Enforce that intervals execute in sequence order with optional minimum delays.

    For each consecutive pair (i, i+1):
        end(intervals[i]) + delays[i] <= start(intervals[i+1])

    This is equivalent to multiple end_before_start constraints but provides
    a cleaner, more semantic API for sequential workflows.

    Args:
        intervals: Ordered list of intervals to chain. Must have at least 2.
        delays: Minimum delays between consecutive intervals.
            - If None: all delays are 0 (immediate succession allowed)
            - If int: same delay between all pairs
            - If list[int]: delays[i] is delay between intervals[i] and intervals[i+1]
              Must have length = len(intervals) - 1

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If intervals are not IntervalVar or delays are not int.
        ValueError: If fewer than 2 intervals or delays list has wrong length.

    Optional Intervals Handling:
        If any interval is optional, the constraint between it and its neighbors
        is only enforced when both intervals are present. The chain "skips"
        absent intervals.

    Example:
        >>> steps = [IntervalVar(size=d, name=f"step_{i}") for i, d in enumerate([5, 10, 3, 8])]
        >>> # Execute steps in order with no gaps allowed
        >>> satisfy(chain(steps))

        >>> # With cleaning time of 2 between all steps
        >>> satisfy(chain(steps, delays=2))

        >>> # With variable delays between steps
        >>> satisfy(chain(steps, delays=[1, 2, 1]))
    """
    intervals = _validate_intervals(intervals, "chain")
    delays_list = _validate_delays(delays, len(intervals), "chain")

    Node, TypeNode = _get_node_builders()
    constraints = []

    for i in range(len(intervals) - 1):
        iv_a = intervals[i]
        iv_b = intervals[i + 1]
        delay = delays_list[i]

        # end(a) + delay <= start(b)
        end_a = _build_end_expr(iv_a, Node, TypeNode)
        start_b = start_var(iv_b)

        if delay > 0:
            lhs = Node.build(TypeNode.ADD, end_a, delay)
        else:
            lhs = end_a

        precedence = Node.build(TypeNode.LE, lhs, start_b)

        # Handle optional intervals
        opt_a = iv_a.optional
        opt_b = iv_b.optional

        if opt_a or opt_b:
            # (a absent) OR (b absent) OR (end(a) + delay <= start(b))
            disjuncts = [precedence]

            if opt_a:
                pres_a = presence_var(iv_a)
                disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

            if opt_b:
                pres_b = presence_var(iv_b)
                disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

            constraints.append(Node.build(TypeNode.OR, *disjuncts))
        else:
            constraints.append(precedence)

    return constraints


def strict_chain(
    intervals: Sequence[IntervalVar],
    delays: int | Sequence[int] | None = None,
) -> list:
    """
    Enforce strict sequential execution: each interval starts exactly when previous ends.

    For each consecutive pair (i, i+1):
        end(intervals[i]) + delays[i] == start(intervals[i+1])

    Unlike chain(), this enforces equality (no gaps between intervals).

    Args:
        intervals: Ordered list of intervals to chain. Must have at least 2.
        delays: Fixed delays between consecutive intervals.
            - If None: all delays are 0 (no gap)
            - If int: same delay between all pairs
            - If list[int]: delays[i] is delay between intervals[i] and intervals[i+1]

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If intervals are not IntervalVar or delays are not int.
        ValueError: If fewer than 2 intervals or delays list has wrong length.

    Example:
        >>> tasks = [IntervalVar(size=d, name=f"task_{i}") for i, d in enumerate([5, 10, 3])]
        >>> # Tasks execute back-to-back with no gaps
        >>> satisfy(strict_chain(tasks))

        >>> # With fixed 2-unit break between tasks
        >>> satisfy(strict_chain(tasks, delays=2))
    """
    intervals = _validate_intervals(intervals, "strict_chain")
    delays_list = _validate_delays(delays, len(intervals), "strict_chain")

    Node, TypeNode = _get_node_builders()
    constraints = []

    for i in range(len(intervals) - 1):
        iv_a = intervals[i]
        iv_b = intervals[i + 1]
        delay = delays_list[i]

        # end(a) + delay == start(b)
        end_a = _build_end_expr(iv_a, Node, TypeNode)
        start_b = start_var(iv_b)

        if delay > 0:
            lhs = Node.build(TypeNode.ADD, end_a, delay)
        else:
            lhs = end_a

        equality = Node.build(TypeNode.EQ, lhs, start_b)

        # Handle optional intervals
        opt_a = iv_a.optional
        opt_b = iv_b.optional

        if opt_a or opt_b:
            # (a absent) OR (b absent) OR (end(a) + delay == start(b))
            disjuncts = [equality]

            if opt_a:
                pres_a = presence_var(iv_a)
                disjuncts.insert(0, Node.build(TypeNode.EQ, pres_a, 0))

            if opt_b:
                pres_b = presence_var(iv_b)
                disjuncts.insert(0, Node.build(TypeNode.EQ, pres_b, 0))

            constraints.append(Node.build(TypeNode.OR, *disjuncts))
        else:
            constraints.append(equality)

    return constraints
