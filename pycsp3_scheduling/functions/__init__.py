"""
Scheduling function types.

This module provides:
- CumulFunction: Cumulative function for resource consumption
- pulse, step_at, step_at_start, step_at_end: Elementary cumul functions
- cumul_range, always_in: Cumulative constraints
- height_at_start, height_at_end: Cumulative accessors
- StateFunction: State function for resource states
- TransitionMatrix: Transition costs/times between states
- always_equal, always_constant, always_no_state: State constraints
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
    always_in as cumul_always_in,
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

from pycsp3_scheduling.functions.state_functions import (
    StateFunction,
    StateConstraint,
    StateConstraintType,
    TransitionMatrix,
    always_constant,
    always_equal,
    always_in as state_always_in,
    always_no_state,
    clear_state_function_registry,
    get_registered_state_functions,
)

# Re-export always_in with smart dispatch
def always_in(resource, interval_or_range, min_val, max_val=None, **kwargs):
    """
    Constrain a cumulative or state function within bounds.
    
    For CumulFunction: always_in(cumul, interval_or_range, min, max)
    For StateFunction: always_in(state_func, interval, min, max)
    """
    if isinstance(resource, CumulFunction):
        return cumul_always_in(resource, interval_or_range, min_val, max_val)
    elif isinstance(resource, StateFunction):
        return state_always_in(resource, interval_or_range, min_val, max_val, **kwargs)
    else:
        raise TypeError(
            f"always_in expects CumulFunction or StateFunction, got {type(resource).__name__}"
        )


# To be implemented:
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
    # Cumul accessors
    "height_at_start",
    "height_at_end",
    # Cumul registry
    "register_cumul",
    "get_registered_cumuls",
    "clear_cumul_registry",
    # State function types
    "StateFunction",
    "StateConstraint",
    "StateConstraintType",
    "TransitionMatrix",
    # State constraints
    "always_equal",
    "always_constant",
    "always_no_state",
    # State registry
    "get_registered_state_functions",
    "clear_state_function_registry",
    # Shared
    "always_in",
    # Future
    # "StepFunction",
]
