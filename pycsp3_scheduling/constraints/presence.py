"""
Presence implication constraints for optional interval variables.

This module provides constraints that express logical relationships between
the presence of optional intervals:

1. **presence_implies(a, b)**: If a is present, then b must be present
2. **presence_or(a, b)**: At least one must be present
3. **presence_xor(a, b)**: Exactly one must be present
4. **all_present_or_all_absent(intervals)**: All-or-nothing group
5. **if_present_then(interval, constraint)**: Apply constraint only when present
6. **at_least_k_present(intervals, k)**: At least k intervals must be present
7. **at_most_k_present(intervals, k)**: At most k intervals can be present
8. **exactly_k_present(intervals, k)**: Exactly k intervals must be present

All constraints return pycsp3 Node objects that can be used with satisfy().
"""

from __future__ import annotations

from pycsp3_scheduling.constraints._pycsp3 import (
    _get_node_builders,
    _validate_interval,
    _validate_intervals,
    presence_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar


# =============================================================================
# Binary Presence Constraints
# =============================================================================


def presence_implies(a: IntervalVar, b: IntervalVar) -> list:
    """
    Constrain that if interval a is present, then interval b must also be present.

    Implements the logical implication: presence(a) => presence(b)
    Equivalent to: NOT presence(a) OR presence(b)

    Args:
        a: The antecedent interval (if this is present...).
        b: The consequent interval (...then this must be present).

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either argument is not an IntervalVar.

    Notes:
        - If a is mandatory (not optional), b must be present (mandatory behavior).
        - If b is mandatory (not optional), constraint is always satisfied.

    Example:
        >>> setup = IntervalVar(size=5, optional=True, name="setup")
        >>> main_task = IntervalVar(size=20, optional=True, name="main")
        >>> # If we do the main task, we must do setup
        >>> satisfy(presence_implies(main_task, setup))
    """
    _validate_interval(a, "presence_implies")
    _validate_interval(b, "presence_implies")

    # If b is mandatory, constraint is always satisfied
    if not b.optional:
        return []

    Node, TypeNode = _get_node_builders()

    pres_a = presence_var(a)
    pres_b = presence_var(b)

    # presence(a) => presence(b)
    # NOT presence(a) OR presence(b)
    # (pres_a == 0) OR (pres_b == 1)

    if not a.optional:
        # a is mandatory (always present), so b must be present
        return [Node.build(TypeNode.EQ, pres_b, 1)]

    a_absent = Node.build(TypeNode.EQ, pres_a, 0)
    b_present = Node.build(TypeNode.EQ, pres_b, 1)

    return [Node.build(TypeNode.OR, a_absent, b_present)]


def presence_or(a: IntervalVar, b: IntervalVar) -> list:
    """
    Constrain that at least one of the intervals must be present.

    Implements: presence(a) OR presence(b)

    Args:
        a: First interval.
        b: Second interval.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either argument is not an IntervalVar.

    Notes:
        - If either interval is mandatory, constraint is always satisfied.

    Example:
        >>> option_a = IntervalVar(size=10, optional=True, name="option_a")
        >>> option_b = IntervalVar(size=15, optional=True, name="option_b")
        >>> # Must choose at least one option
        >>> satisfy(presence_or(option_a, option_b))
    """
    _validate_interval(a, "presence_or")
    _validate_interval(b, "presence_or")

    # If either is mandatory, constraint is always satisfied
    if not a.optional or not b.optional:
        return []

    Node, TypeNode = _get_node_builders()

    pres_a = presence_var(a)
    pres_b = presence_var(b)

    # (pres_a == 1) OR (pres_b == 1)
    a_present = Node.build(TypeNode.EQ, pres_a, 1)
    b_present = Node.build(TypeNode.EQ, pres_b, 1)

    return [Node.build(TypeNode.OR, a_present, b_present)]


def presence_xor(a: IntervalVar, b: IntervalVar) -> list:
    """
    Constrain that exactly one of the intervals must be present (exclusive or).

    Implements: presence(a) XOR presence(b)
    Equivalent to: (presence(a) OR presence(b)) AND NOT (presence(a) AND presence(b))

    Args:
        a: First interval.
        b: Second interval.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If either argument is not an IntervalVar.

    Notes:
        - Both intervals should be optional for meaningful behavior.
        - If either is mandatory, this may result in infeasibility or forced absence.

    Example:
        >>> route_a = IntervalVar(size=30, optional=True, name="route_a")
        >>> route_b = IntervalVar(size=45, optional=True, name="route_b")
        >>> # Must take exactly one route
        >>> satisfy(presence_xor(route_a, route_b))
    """
    _validate_interval(a, "presence_xor")
    _validate_interval(b, "presence_xor")

    Node, TypeNode = _get_node_builders()

    pres_a = presence_var(a)
    pres_b = presence_var(b)

    if not a.optional and not b.optional:
        # Both mandatory - XOR is impossible (infeasible)
        return [Node.build(TypeNode.EQ, 0, 1)]  # False constraint

    if not a.optional:
        # a is mandatory (always present), so b must be absent
        return [Node.build(TypeNode.EQ, pres_b, 0)]

    if not b.optional:
        # b is mandatory (always present), so a must be absent
        return [Node.build(TypeNode.EQ, pres_a, 0)]

    # Both optional: pres_a + pres_b == 1
    # This is XOR: exactly one must be 1
    sum_pres = Node.build(TypeNode.ADD, pres_a, pres_b)
    return [Node.build(TypeNode.EQ, sum_pres, 1)]


# =============================================================================
# Group Presence Constraints
# =============================================================================


def all_present_or_all_absent(intervals: Sequence[IntervalVar]) -> list:
    """
    Constrain that either all intervals are present, or all are absent.

    All presence values must be equal: either all 0 or all 1.

    Args:
        intervals: List of optional interval variables.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar.

    Notes:
        - All intervals should be optional for meaningful behavior.
        - If any interval is mandatory, all must be present.

    Example:
        >>> subtasks = [IntervalVar(size=5, optional=True, name=f"sub_{i}") for i in range(3)]
        >>> # Either do all subtasks or none
        >>> satisfy(all_present_or_all_absent(subtasks))
    """
    intervals = _validate_intervals(intervals, "all_present_or_all_absent")

    if len(intervals) < 2:
        return []

    Node, TypeNode = _get_node_builders()
    constraints = []

    # Check if any interval is mandatory
    has_mandatory = any(not iv.optional for iv in intervals)

    if has_mandatory:
        # If any is mandatory, all optional ones must be present
        for iv in intervals:
            if iv.optional:
                pres = presence_var(iv)
                constraints.append(Node.build(TypeNode.EQ, pres, 1))
        return constraints

    # All optional: all presence values must be equal
    first_pres = presence_var(intervals[0])
    for iv in intervals[1:]:
        pres = presence_var(iv)
        constraints.append(Node.build(TypeNode.EQ, first_pres, pres))

    return constraints


def presence_or_all(*intervals: IntervalVar) -> list:
    """
    Constrain that at least one of the intervals must be present.

    Variadic version of presence_or for multiple intervals.

    Args:
        *intervals: Variable number of interval variables.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any argument is not an IntervalVar.

    Example:
        >>> options = [IntervalVar(size=10, optional=True, name=f"opt_{i}") for i in range(5)]
        >>> # At least one option must be selected
        >>> satisfy(presence_or_all(*options))
    """
    intervals_list = _validate_intervals(intervals, "presence_or_all")

    if not intervals_list:
        return []

    # If any is mandatory, constraint is always satisfied
    if any(not iv.optional for iv in intervals_list):
        return []

    Node, TypeNode = _get_node_builders()

    # Build OR of all presence conditions
    conditions = []
    for iv in intervals_list:
        pres = presence_var(iv)
        conditions.append(Node.build(TypeNode.EQ, pres, 1))

    if len(conditions) == 1:
        return conditions

    return [Node.build(TypeNode.OR, *conditions)]


# =============================================================================
# Conditional Constraints
# =============================================================================


def if_present_then(interval: IntervalVar, constraint) -> list:
    """
    Apply a constraint only when the interval is present.

    Implements: presence(interval) => constraint
    The constraint is only enforced if the interval is present.

    Args:
        interval: The interval whose presence gates the constraint.
        constraint: A pycsp3 Node constraint to apply when present.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If interval is not an IntervalVar.

    Notes:
        - If interval is mandatory, constraint is always enforced.
        - The constraint argument should be a pycsp3 Node object.

    Example:
        >>> from pycsp3.classes.nodes import Node, TypeNode
        >>> task = IntervalVar(size=10, optional=True, name="task")
        >>> start = start_var(task)
        >>> # If task is present, it must start after time 5
        >>> min_start = Node.build(TypeNode.GE, start, 5)
        >>> satisfy(if_present_then(task, min_start))
    """
    _validate_interval(interval, "if_present_then")

    if not interval.optional:
        # Mandatory interval - always apply constraint
        if isinstance(constraint, list):
            return constraint
        return [constraint]

    Node, TypeNode = _get_node_builders()

    pres = presence_var(interval)
    absent = Node.build(TypeNode.EQ, pres, 0)

    # (presence == 0) OR constraint
    if isinstance(constraint, list):
        # Multiple constraints - apply to each
        result = []
        for c in constraint:
            result.append(Node.build(TypeNode.OR, absent, c))
        return result

    return [Node.build(TypeNode.OR, absent, constraint)]


# =============================================================================
# Cardinality Constraints
# =============================================================================


def at_least_k_present(intervals: Sequence[IntervalVar], k: int) -> list:
    """
    Constrain that at least k intervals must be present.

    Args:
        intervals: List of interval variables.
        k: Minimum number of intervals that must be present.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar or k is not int.
        ValueError: If k is negative.

    Example:
        >>> tasks = [IntervalVar(size=10, optional=True, name=f"t_{i}") for i in range(10)]
        >>> # Must complete at least 5 tasks
        >>> satisfy(at_least_k_present(tasks, 5))
    """
    intervals = _validate_intervals(intervals, "at_least_k_present")

    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    if k == 0:
        return []  # Always satisfied

    # Count mandatory intervals
    mandatory_count = sum(1 for iv in intervals if not iv.optional)

    if mandatory_count >= k:
        return []  # Already satisfied by mandatory intervals

    if k > len(intervals):
        # Infeasible
        Node, TypeNode = _get_node_builders()
        return [Node.build(TypeNode.EQ, 0, 1)]

    Node, TypeNode = _get_node_builders()

    # Sum of presence values >= k
    presence_vars = [presence_var(iv) for iv in intervals]

    if len(presence_vars) == 1:
        return [Node.build(TypeNode.GE, presence_vars[0], k)]

    sum_pres = Node.build(TypeNode.ADD, *presence_vars)
    return [Node.build(TypeNode.GE, sum_pres, k)]


def at_most_k_present(intervals: Sequence[IntervalVar], k: int) -> list:
    """
    Constrain that at most k intervals can be present.

    Args:
        intervals: List of interval variables.
        k: Maximum number of intervals that can be present.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar or k is not int.
        ValueError: If k is negative.

    Example:
        >>> features = [IntervalVar(size=10, optional=True, name=f"f_{i}") for i in range(10)]
        >>> # Can implement at most 3 features
        >>> satisfy(at_most_k_present(features, 3))
    """
    intervals = _validate_intervals(intervals, "at_most_k_present")

    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    if k >= len(intervals):
        return []  # Always satisfied

    # Count mandatory intervals
    mandatory_count = sum(1 for iv in intervals if not iv.optional)

    if mandatory_count > k:
        # Infeasible - too many mandatory intervals
        Node, TypeNode = _get_node_builders()
        return [Node.build(TypeNode.EQ, 0, 1)]

    Node, TypeNode = _get_node_builders()

    # Sum of presence values <= k
    presence_vars = [presence_var(iv) for iv in intervals]

    if len(presence_vars) == 1:
        return [Node.build(TypeNode.LE, presence_vars[0], k)]

    sum_pres = Node.build(TypeNode.ADD, *presence_vars)
    return [Node.build(TypeNode.LE, sum_pres, k)]


def exactly_k_present(intervals: Sequence[IntervalVar], k: int) -> list:
    """
    Constrain that exactly k intervals must be present.

    Args:
        intervals: List of interval variables.
        k: Exact number of intervals that must be present.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If any element is not an IntervalVar or k is not int.
        ValueError: If k is negative.

    Example:
        >>> shifts = [IntervalVar(size=480, optional=True, name=f"shift_{i}") for i in range(7)]
        >>> # Exactly 5 shifts must be worked
        >>> satisfy(exactly_k_present(shifts, 5))
    """
    intervals = _validate_intervals(intervals, "exactly_k_present")

    if not isinstance(k, int):
        raise TypeError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non-negative")

    Node, TypeNode = _get_node_builders()

    if k > len(intervals):
        # Infeasible
        return [Node.build(TypeNode.EQ, 0, 1)]

    # Count mandatory intervals
    mandatory_count = sum(1 for iv in intervals if not iv.optional)

    if mandatory_count > k:
        # Infeasible - too many mandatory intervals
        return [Node.build(TypeNode.EQ, 0, 1)]

    if mandatory_count == k:
        # All optional must be absent
        constraints = []
        for iv in intervals:
            if iv.optional:
                pres = presence_var(iv)
                constraints.append(Node.build(TypeNode.EQ, pres, 0))
        return constraints

    # Sum of presence values == k
    presence_vars = [presence_var(iv) for iv in intervals]

    if len(presence_vars) == 1:
        return [Node.build(TypeNode.EQ, presence_vars[0], k)]

    sum_pres = Node.build(TypeNode.ADD, *presence_vars)
    return [Node.build(TypeNode.EQ, sum_pres, k)]
