"""
pycsp3-scheduling: Scheduling extension for pycsp3.

This package extends pycsp3 with comprehensive scheduling support including:
- Interval variables (IntervalVar)
- Sequence variables (SequenceVar)
- Precedence constraints (end_before_start, start_at_start, etc.)
- Grouping constraints (span, alternative, synchronize)
- Sequence constraints (SeqNoOverlap, first, last, before, previous)
- Sequence consistency constraints (same_sequence, same_common_subsequence)
- Sequence accessor expressions (start_of_next, start_of_prev, etc.)
- Cumulative functions (pulse, step_at_start, step_at_end) [future]
- State functions and constraints [future]
- XCSP3 scheduling extension output [future]

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
    end_of_next,
    end_of_prev,
    expr_max,
    expr_min,
    length_of,
    length_of_next,
    length_of_prev,
    overlap_length,
    presence_of,
    size_of,
    size_of_next,
    size_of_prev,
    start_of,
    start_of_next,
    start_of_prev,
    type_of_next,
    type_of_prev,
)

# Interop
from pycsp3_scheduling.interop import end_time, start_time

# Constraints
from pycsp3_scheduling.constraints import (
    SeqNoOverlap,
    alternative,
    before,
    end_at_end,
    end_at_start,
    end_before_end,
    end_before_start,
    first,
    last,
    previous,
    same_common_subsequence,
    same_sequence,
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
    # Expressions - Basic
    "IntervalExpr",
    "start_of",
    "end_of",
    "size_of",
    "length_of",
    "presence_of",
    "overlap_length",
    "expr_min",
    "expr_max",
    # Expressions - Sequence Next
    "start_of_next",
    "end_of_next",
    "size_of_next",
    "length_of_next",
    "type_of_next",
    # Expressions - Sequence Prev
    "start_of_prev",
    "end_of_prev",
    "size_of_prev",
    "length_of_prev",
    "type_of_prev",
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
    "first",
    "last",
    "before",
    "previous",
    # Constraints - Sequence Consistency
    "same_sequence",
    "same_common_subsequence",
]
