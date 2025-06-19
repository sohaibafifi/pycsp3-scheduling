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

# Variables
from pycsp3_scheduling.variables import (
    INTERVAL_MAX,
    INTERVAL_MIN,
    IntervalVar,
    IntervalVarArray,
    IntervalVarDict,
    SequenceVar,
    SequenceVarArray,
)

# Expressions
from pycsp3_scheduling.expressions import (
    IntervalExpr,
    end_of,
    expr_max,
    expr_min,
    length_of,
    overlap_length,
    presence_of,
    size_of,
    start_of,
)

# Interop
from pycsp3_scheduling.interop import end_time, start_time

# Constraints
from pycsp3_scheduling.constraints import (
    SeqNoOverlap,
    alternative,
    end_at_end,
    end_at_start,
    end_before_end,
    end_before_start,
    span,
    start_at_end,
    start_at_start,
    start_before_end,
    start_before_start,
    synchronize,
)

# Functions (to be implemented)
# from pycsp3_scheduling.functions import (
#     pulse, step_at, step_at_start, step_at_end,
#     CumulFunction, StateFunction, TransitionMatrix, StepFunction,
# )

__all__ = [
    "__version__",
    # Variables
    "IntervalVar",
    "IntervalVarArray",
    "IntervalVarDict",
    "SequenceVar",
    "SequenceVarArray",
    "INTERVAL_MIN",
    "INTERVAL_MAX",
    # Expressions
    "IntervalExpr",
    "start_of",
    "end_of",
    "size_of",
    "length_of",
    "presence_of",
    "overlap_length",
    "expr_min",
    "expr_max",
    # Interop
    "start_time",
    "end_time",
    # Constraints - Exact timing
    "start_at_start",
    "start_at_end",
    "end_at_start",
    "end_at_end",
    # Constraints - Before
    "start_before_start",
    "start_before_end",
    "end_before_start",
    "end_before_end",
    # Constraints - Grouping
    "span",
    "alternative",
    "synchronize",
    # Constraints - Sequence
    "SeqNoOverlap",
]
