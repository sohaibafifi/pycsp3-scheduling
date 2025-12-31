"""
Scheduling function types.

This module provides:
- CumulFunction: Cumulative function for resource consumption
- pulse, step_at, step_at_start, step_at_end: Elementary cumul functions
- cumul_range, always_in: Cumulative constraints
- height_at_start, height_at_end: Cumulative accessors
- StateFunction: State function for resource states (future)
- TransitionMatrix: Transition costs/times between states (future)
- StepFunction: Piecewise step function for forbidden regions (future)
"""

from __future__ import annotations

from pycsp3_scheduling.functions.cumul_functions import (
    CumulExpr,
    CumulExprType,
    CumulFunction,
    CumulConstraint,
    CumulConstraintType,
    CumulHeightExpr,
    CumulHeightType,
    always_in,
    cumul_range,
    height_at_end,
    height_at_start,
    pulse,
    step_at,
    step_at_end,
    step_at_start,
    clear_cumul_registry,
    get_registered_cumuls,
    register_cumul,
)

# To be implemented:
# from pycsp3_scheduling.functions.state_functions import StateFunction
# from pycsp3_scheduling.functions.transition_matrix import TransitionMatrix
# from pycsp3_scheduling.functions.step_function import StepFunction

__all__ = [
    # Cumulative function types
    "CumulExpr",
    "CumulExprType",
    "CumulFunction",
    "CumulConstraint",
    "CumulConstraintType",
    "CumulHeightExpr",
    "CumulHeightType",
    # Elementary cumul functions
    "pulse",
    "step_at",
    "step_at_start",
    "step_at_end",
    # Cumul constraints
    "cumul_range",
    "always_in",
    # Cumul accessors
    "height_at_start",
    "height_at_end",
    # Registry
    "register_cumul",
    "get_registered_cumuls",
    "clear_cumul_registry",
    # Future
    # "StateFunction",
    # "TransitionMatrix",
    # "StepFunction",
]
