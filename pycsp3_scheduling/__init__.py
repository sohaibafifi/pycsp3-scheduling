"""
pycsp3-scheduling: Scheduling extension for pycsp3.

This package extends pycsp3 with comprehensive scheduling support including:
- Interval variables (IntervalVar)
- Sequence variables (SequenceVar)
- Precedence constraints (end_before_start, start_at_start, etc.)
- Grouping constraints (span, alternative, synchronize)
- Cumulative functions (pulse, step_at_start, step_at_end)
- State functions and constraints
- XCSP3 scheduling extension output

"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Sohaib AFIFI"

# Variables (to be implemented)
# from pycsp3_scheduling.variables import IntervalVar, SequenceVar, IntervalVarArray

# Expressions (to be implemented)
# from pycsp3_scheduling.expressions import (
#     start_of, end_of, size_of, length_of, presence_of,
#     overlap_length, start_eval, end_eval, size_eval, length_eval,
# )

# Constraints (to be implemented)
# from pycsp3_scheduling.constraints import (
#     # Precedence
#     start_at_start, start_at_end, end_at_start, end_at_end,
#     start_before_start, start_before_end, end_before_start, end_before_end,
#     # Grouping
#     span, alternative, synchronize,
#     # Sequence
#     no_overlap, first, last, before, previous,
#     same_sequence, same_common_subsequence,
#     # Cumulative
#     cumul_range, always_in,
#     # State
#     always_equal, always_constant, always_no_state,
#     # Forbidden
#     forbid_start, forbid_end, forbid_extent,
# )

# Functions (to be implemented)
# from pycsp3_scheduling.functions import (
#     pulse, step_at, step_at_start, step_at_end,
#     CumulFunction, StateFunction, TransitionMatrix, StepFunction,
# )

__all__ = [
    "__version__",
    # Variables
    # "IntervalVar",
    # "SequenceVar",
    # "IntervalVarArray",
    # Expressions
    # "start_of",
    # "end_of",
    # "size_of",
    # "length_of",
    # "presence_of",
    # ... more to come
]
