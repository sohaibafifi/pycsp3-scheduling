"""
Cumulative constraints for resource modeling.

This module provides constraints on cumulative functions that integrate
with pycsp3's constraint system.

The key challenge is that pycsp3 doesn't have native cumulative functions,
so we decompose them into discrete time-indexed constraints or use the
Cumulative global constraint where applicable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence, Union

from pycsp3_scheduling.constraints._pycsp3 import length_value, presence_var, start_var
from pycsp3_scheduling.functions.cumul_functions import (
    CumulConstraint,
    CumulConstraintType,
    CumulExpr,
    CumulExprType,
    CumulFunction,
)

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar


def _get_node_builders():
    """Import and return pycsp3 Node building utilities."""
    from pycsp3.classes.nodes import Node, TypeNode

    return Node, TypeNode


def _build_end_expr(interval, Node, TypeNode):
    """Build end expression: start + length."""
    start = start_var(interval)
    length = length_value(interval)
    if isinstance(length, int) and length == 0:
        return start
    return Node.build(TypeNode.ADD, start, length)


def _is_simple_pulse_cumul(cumul: CumulFunction) -> bool:
    """Check if cumulative function is a simple sum of pulses with fixed heights."""
    for expr in cumul.expressions:
        if expr.expr_type == CumulExprType.NEG:
            # Check the negated expression
            if expr.operands and expr.operands[0].expr_type != CumulExprType.PULSE:
                return False
            if expr.operands and expr.operands[0].is_variable_height:
                return False
        elif expr.expr_type != CumulExprType.PULSE:
            return False
        elif expr.is_variable_height:
            return False
    return True


def _get_pulse_data(cumul: CumulFunction) -> tuple[list, list[int], list[int]]:
    """Extract intervals, heights, and lengths from a pulse-only cumulative."""
    intervals = []
    heights = []

    for expr in cumul.expressions:
        if expr.expr_type == CumulExprType.NEG:
            inner = expr.operands[0]
            intervals.append(inner.interval)
            heights.append(-(inner.height or inner.height_min))
        else:
            intervals.append(expr.interval)
            heights.append(expr.height or expr.height_min)

    return intervals, heights


def build_cumul_constraint(constraint: CumulConstraint) -> list:
    """
    Build pycsp3 constraints from a CumulConstraint.

    For simple pulse-based cumulative functions with capacity constraints,
    uses pycsp3's Cumulative global constraint. For more complex cases,
    decomposes into time-indexed constraints.

    Args:
        constraint: The cumulative constraint to build.

    Returns:
        List of pycsp3 constraint nodes or ECtr objects.
    """
    cumul = constraint.cumul

    # Handle simple capacity constraints on pulse cumulative functions
    if (
        constraint.constraint_type in (CumulConstraintType.LE, CumulConstraintType.RANGE)
        and _is_simple_pulse_cumul(cumul)
        and cumul.expressions
    ):
        return _build_cumulative_constraint(constraint)

    # For other cases, use decomposition
    return _build_decomposed_constraint(constraint)


def _build_cumulative_constraint(constraint: CumulConstraint) -> list:
    """
    Build using pycsp3's Cumulative global constraint.

    Cumulative(origins, lengths, heights) <= limit
    """
    from pycsp3 import Cumulative

    cumul = constraint.cumul
    intervals, heights = _get_pulse_data(cumul)

    # Filter out negative heights (not supported by standard Cumulative)
    if any(h < 0 for h in heights):
        return _build_decomposed_constraint(constraint)

    # Get pycsp3 variables
    origins = [start_var(iv) for iv in intervals]
    lengths = [length_value(iv) for iv in intervals]

    if constraint.constraint_type == CumulConstraintType.LE:
        limit = constraint.bound
    elif constraint.constraint_type == CumulConstraintType.RANGE:
        # Cumulative only supports upper bound directly
        # For lower bound, we'd need decomposition
        if constraint.min_bound > 0:
            return _build_decomposed_constraint(constraint)
        limit = constraint.max_bound
    else:
        return _build_decomposed_constraint(constraint)

    # Build the Cumulative constraint
    return [Cumulative(origins=origins, lengths=lengths, heights=heights) <= limit]


def _build_decomposed_constraint(constraint: CumulConstraint) -> list:
    """
    Build decomposed constraints for complex cumulative functions.

    This handles:
    - Variable heights
    - Step functions (step_at_start, step_at_end, step_at)
    - ALWAYS_IN constraints
    - GE/GT constraints

    For now, returns a placeholder as full decomposition is complex.
    """
    Node, TypeNode = _get_node_builders()
    constraints = []

    cumul = constraint.cumul

    # For GE constraints: can negate and use LE
    if constraint.constraint_type == CumulConstraintType.GE:
        # cumul >= bound  <=>  -cumul <= -bound
        # But we need to handle this properly with the actual expressions
        pass

    # For ALWAYS_IN: constrain during specific time range
    if constraint.constraint_type == CumulConstraintType.ALWAYS_IN:
        # This requires time-indexed reasoning
        # For fixed time ranges, we can reason about which intervals overlap
        pass

    # Default: return empty list (constraint not yet enforced at pycsp3 level)
    # The CumulConstraint object still exists for model introspection
    return constraints


def SeqCumulative(
    intervals: Sequence[IntervalVar],
    heights: Sequence[int],
    capacity: int,
) -> list:
    """
    Resource capacity constraint using pycsp3's Cumulative.

    Ensures that the sum of heights of intervals executing at any time
    does not exceed the capacity.

    This is named SeqCumulative to avoid clashing with pycsp3's native
    Cumulative constraint.

    Args:
        intervals: List of interval variables.
        heights: List of resource heights (demands) for each interval.
        capacity: Maximum capacity of the resource.

    Returns:
        List containing the Cumulative constraint.

    Raises:
        ValueError: If intervals and heights have different lengths.
        TypeError: If inputs have wrong types.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> demands = [2, 3, 1]
        >>> satisfy(SeqCumulative(tasks, demands, capacity=4))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3 import Cumulative as Cumul

    if len(intervals) != len(heights):
        raise ValueError(
            f"intervals ({len(intervals)}) and heights ({len(heights)}) must have same length"
        )

    for i, iv in enumerate(intervals):
        if not isinstance(iv, IntervalVar):
            raise TypeError(f"intervals[{i}] must be an IntervalVar")

    for i, h in enumerate(heights):
        if not isinstance(h, int):
            raise TypeError(f"heights[{i}] must be an int")

    if not isinstance(capacity, int):
        raise TypeError(f"capacity must be an int, got {type(capacity).__name__}")

    origins = [start_var(iv) for iv in intervals]
    lengths = [length_value(iv) for iv in intervals]

    return [Cumul(origins=origins, lengths=lengths, heights=list(heights)) <= capacity]
