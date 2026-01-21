"""
pycsp3-scheduling: Scheduling extension for pycsp3.

This package extends pycsp3 with comprehensive scheduling support including:
- **Interval Variables**: Represent tasks/activities with start, end, size, length, and optional presence
- **Intensity Functions**: Stepwise intensity metadata with granularity scaling for size/length
- **Sequence Variables**: Ordered sequences of intervals on disjunctive resources
- **Precedence Constraints**: `end_before_start`, `start_at_start`, etc.
- **Grouping Constraints**: `span`, `alternative`, `synchronize`
- **Sequence Constraints**: `SeqNoOverlap`, `first`, `last`, `before`, `previous`, `same_sequence`
- **Forbidden Time Constraints**: `forbid_start`, `forbid_end`, `forbid_extent`
- **Presence Constraints**: `presence_implies`, `presence_or`, `presence_xor`, `chain`
- **Overlap Constraints**: `must_overlap`, `overlap_at_least`, `disjunctive`
- **Aggregate Expressions**: `count_present`, `earliest_start`, `latest_end`, `makespan`
- **Cumulative Functions**: `pulse`, `step_at_start`, `step_at_end` for resource modeling
- **State Functions**: Model resource states with transitions
- **XCSP3 Extension**: Output scheduling models in extended XCSP3 format
- **Visualization**: Gantt charts and resource profiles

"""

from __future__ import annotations

__version__ = "0.3.1"
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
    ElementMatrix,
    IntervalExpr,
    clear_sequence_expr_cache,
    count_present,
    earliest_start,
    element,
    element2d,
    end_of,
    end_of_next,
    end_of_prev,
    expr_max,
    expr_min,
    latest_end,
    length_of,
    length_of_next,
    length_of_prev,
    makespan,
    overlap_length,
    presence_of,
    size_of,
    size_of_next,
    size_of_prev,
    span_length,
    start_of,
    start_of_next,
    start_of_prev,
    type_of_next,
    type_of_prev,
)

# Interop
from pycsp3_scheduling.interop import (
    IntervalValue,
    ModelStatistics,
    SolutionStatistics,
    end_time,
    interval_value,
    model_statistics,
    presence_time,
    solution_statistics,
    start_time,
)

# Constraints
from pycsp3_scheduling.constraints import (
    SeqCumulative,
    SeqNoOverlap,
    all_present_or_all_absent,
    alternative,
    at_least_k_present,
    at_most_k_present,
    before,
    chain,
    disjunctive,
    end_at_end,
    end_at_start,
    end_before_end,
    end_before_start,
    exactly_k_present,
    first,
    forbid_end,
    forbid_extent,
    forbid_start,
    if_present_then,
    last,
    must_overlap,
    no_overlap_pairwise,
    overlap_at_least,
    presence_implies,
    presence_or,
    presence_or_all,
    presence_xor,
    previous,
    same_common_subsequence,
    same_sequence,
    span,
    start_at_end,
    start_at_start,
    start_before_end,
    start_before_start,
    strict_chain,
    synchronize,
)

# Cumulative Functions
from pycsp3_scheduling.functions import (
    CumulExpr,
    CumulFunction,
    CumulConstraint,
    CumulHeightExpr,
    always_in,
    cumul_range,
    height_at_end,
    height_at_start,
    pulse,
    step_at,
    step_at_end,
    step_at_start,
)

# State Functions
from pycsp3_scheduling.functions import (
    StateFunction,
    StateConstraint,
    TransitionMatrix,
    always_constant,
    always_equal,
    always_no_state,
)

# Visualization (imported as submodule)
from pycsp3_scheduling import visu

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
    # Expressions - Element (array indexing)
    "ElementMatrix",
    "element",
    "element2d",
    "clear_sequence_expr_cache",
    # Expressions - Aggregate
    "count_present",
    "earliest_start",
    "latest_end",
    "span_length",
    "makespan",
    # Interop
    "start_time",
    "end_time",
    "presence_time",
    "interval_value",
    "IntervalValue",
    "model_statistics",
    "solution_statistics",
    "ModelStatistics",
    "SolutionStatistics",
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
    # Constraints - Cumulative
    "SeqCumulative",
    # Constraints - Forbidden Time
    "forbid_start",
    "forbid_end",
    "forbid_extent",
    # Constraints - Presence
    "presence_implies",
    "presence_or",
    "presence_or_all",
    "presence_xor",
    "all_present_or_all_absent",
    "if_present_then",
    "at_least_k_present",
    "at_most_k_present",
    "exactly_k_present",
    # Constraints - Chain
    "chain",
    "strict_chain",
    # Constraints - Overlap
    "must_overlap",
    "overlap_at_least",
    "no_overlap_pairwise",
    "disjunctive",
    # Cumulative Functions
    "CumulExpr",
    "CumulFunction",
    "CumulConstraint",
    "CumulHeightExpr",
    "pulse",
    "step_at",
    "step_at_start",
    "step_at_end",
    "cumul_range",
    "always_in",
    "height_at_start",
    "height_at_end",
    # State Functions
    "StateFunction",
    "StateConstraint",
    "TransitionMatrix",
    "always_equal",
    "always_constant",
    "always_no_state",
    # Visualization
    "visu",
]
