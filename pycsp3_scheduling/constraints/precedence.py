"""
Precedence constraints for interval variables.

This module provides two families of precedence constraints:

1. **Exact timing constraints** (equality):
   - start_at_start(a, b, delay): start(b) == start(a) + delay
   - start_at_end(a, b, delay): start(b) == end(a) + delay
   - end_at_start(a, b, delay): end(a) == start(b) + delay
   - end_at_end(a, b, delay): end(b) == end(a) + delay

2. **Before constraints** (inequality):
   - start_before_start(a, b, delay): start(b) >= start(a) + delay
   - start_before_end(a, b, delay): end(b) >= start(a) + delay
   - end_before_start(a, b, delay): start(b) >= end(a) + delay
   - end_before_end(a, b, delay): end(b) >= end(a) + delay

All constraints return pycsp3 Node objects that can be used with satisfy().

Absent interval semantics:
- When both intervals are present: constraint is enforced
- When either interval is absent: constraint is trivially satisfied
  (Note: optional intervals not yet implemented)
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import length_value, start_var
from pycsp3_scheduling.variables.interval import IntervalVar


def _validate_precedence_args(
    a: IntervalVar, b: IntervalVar, delay: int, func_name: str
) -> None:
    """Validate arguments for precedence constraint functions."""
    if not isinstance(a, IntervalVar) or not isinstance(b, IntervalVar):
        raise TypeError(f"{func_name} expects IntervalVar inputs")
    if not isinstance(delay, int):
        raise TypeError("delay must be an int")


def _get_node_builders():
    """Import and return pycsp3 Node building utilities."""
    from pycsp3.classes.nodes import Node, TypeNode

    return Node, TypeNode


# =============================================================================
# Exact Timing Constraints (Equality)
# =============================================================================


def start_at_start(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b starts exactly when interval a starts (plus delay).

    Semantics (when both present):
        start(b) == start(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Time delay between start of a and start of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(start_at_start(task1, task2))  # Start together
        >>> satisfy(start_at_start(task1, task2, delay=5))  # task2 starts 5 after task1
    """
    _validate_precedence_args(a, b, delay, "start_at_start")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)

    # start(b) == start(a) + delay
    if delay:
        rhs = Node.build(TypeNode.ADD, start_a, delay)
    else:
        rhs = start_a
    return Node.build(TypeNode.EQ, start_b, rhs)


def start_at_end(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b starts exactly when interval a ends (plus delay).

    Semantics (when both present):
        start(b) == end(a) + delay
        start(b) == start(a) + length(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Time delay between end of a and start of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(start_at_end(task1, task2))  # task2 starts exactly when task1 ends
    """
    _validate_precedence_args(a, b, delay, "start_at_end")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_a = length_value(a)

    # start(b) == start(a) + length(a) + delay
    rhs = Node.build(TypeNode.ADD, start_a, length_a)
    if delay:
        rhs = Node.build(TypeNode.ADD, rhs, delay)
    return Node.build(TypeNode.EQ, start_b, rhs)


def end_at_start(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval a ends exactly when interval b starts (plus delay).

    Semantics (when both present):
        end(a) == start(b) + delay
        start(a) + length(a) == start(b) + delay

    Note: This is equivalent to start_at_end(b, a, -delay) but expressed
    from a's perspective.

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Time delay between end of a and start of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(end_at_start(task1, task2))  # task1 ends exactly when task2 starts
    """
    _validate_precedence_args(a, b, delay, "end_at_start")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_a = length_value(a)

    # end(a) == start(b) + delay
    # start(a) + length(a) == start(b) + delay
    lhs = Node.build(TypeNode.ADD, start_a, length_a)
    if delay:
        rhs = Node.build(TypeNode.ADD, start_b, delay)
    else:
        rhs = start_b
    return Node.build(TypeNode.EQ, lhs, rhs)


def end_at_end(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b ends exactly when interval a ends (plus delay).

    Semantics (when both present):
        end(b) == end(a) + delay
        start(b) + length(b) == start(a) + length(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Time delay between end of a and end of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(end_at_end(task1, task2))  # Both end at the same time
    """
    _validate_precedence_args(a, b, delay, "end_at_end")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_a = length_value(a)
    length_b = length_value(b)

    # end(b) == end(a) + delay
    # start(b) + length(b) == start(a) + length(a) + delay
    lhs = Node.build(TypeNode.ADD, start_b, length_b)
    rhs = Node.build(TypeNode.ADD, start_a, length_a)
    if delay:
        rhs = Node.build(TypeNode.ADD, rhs, delay)
    return Node.build(TypeNode.EQ, lhs, rhs)


# =============================================================================
# Before Constraints (Inequality)
# =============================================================================


def start_before_start(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b cannot start before interval a starts (plus delay).

    Semantics (when both present):
        start(b) >= start(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Minimum time between start of a and start of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(start_before_start(task1, task2))  # task2 starts after task1 starts
    """
    _validate_precedence_args(a, b, delay, "start_before_start")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)

    # start(b) >= start(a) + delay  =>  start(a) + delay <= start(b)
    if delay:
        lhs = Node.build(TypeNode.ADD, start_a, delay)
    else:
        lhs = start_a
    return Node.build(TypeNode.LE, lhs, start_b)


def start_before_end(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b cannot end before interval a starts (plus delay).

    Semantics (when both present):
        end(b) >= start(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Minimum time between start of a and end of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(start_before_end(task1, task2))  # task2 ends after task1 starts
    """
    _validate_precedence_args(a, b, delay, "start_before_end")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_b = length_value(b)

    # end(b) >= start(a) + delay
    # start(b) + length(b) >= start(a) + delay
    # start(a) + delay <= start(b) + length(b)
    if delay:
        lhs = Node.build(TypeNode.ADD, start_a, delay)
    else:
        lhs = start_a
    rhs = Node.build(TypeNode.ADD, start_b, length_b)
    return Node.build(TypeNode.LE, lhs, rhs)


def end_before_start(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval a ends before interval b starts.

    This is the classic precedence constraint used in job-shop scheduling.

    Semantics (when both present):
        start(b) >= end(a) + delay
        start(b) >= start(a) + length(a) + delay

    Args:
        a: First interval variable (predecessor).
        b: Second interval variable (successor).
        delay: Minimum time between end of a and start of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(end_before_start(task1, task2))  # task2 starts after task1 ends
    """
    _validate_precedence_args(a, b, delay, "end_before_start")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_a = length_value(a)

    # start(b) >= start(a) + length(a) + delay
    lhs = Node.build(TypeNode.ADD, start_a, length_a)
    if delay:
        lhs = Node.build(TypeNode.ADD, lhs, delay)
    return Node.build(TypeNode.LE, lhs, start_b)


def end_before_end(a: IntervalVar, b: IntervalVar, delay: int = 0):
    """
    Enforce that interval b cannot end before interval a ends (plus delay).

    Semantics (when both present):
        end(b) >= end(a) + delay
        start(b) + length(b) >= start(a) + length(a) + delay

    Args:
        a: First interval variable.
        b: Second interval variable.
        delay: Minimum time between end of a and end of b. Default 0.

    Returns:
        A pycsp3 Node representing the constraint.

    Raises:
        TypeError: If inputs are not IntervalVar or delay is not int.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=5, name="task2")
        >>> satisfy(end_before_end(task1, task2))  # task2 ends after task1 ends
    """
    _validate_precedence_args(a, b, delay, "end_before_end")
    Node, TypeNode = _get_node_builders()

    start_a = start_var(a)
    start_b = start_var(b)
    length_a = length_value(a)
    length_b = length_value(b)

    # end(b) >= end(a) + delay
    # start(b) + length(b) >= start(a) + length(a) + delay
    lhs = Node.build(TypeNode.ADD, start_a, length_a)
    if delay:
        lhs = Node.build(TypeNode.ADD, lhs, delay)
    rhs = Node.build(TypeNode.ADD, start_b, length_b)
    return Node.build(TypeNode.LE, lhs, rhs)
