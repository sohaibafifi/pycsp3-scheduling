"""
Expression functions for interval variables.

This module provides accessor functions that return expressions from interval variables:
- start_of, end_of, size_of, length_of, presence_of
- overlap_length
- expr_min, expr_max
- Sequence accessors: start_of_next, start_of_prev, etc.
- Element expressions for array indexing: element, element2d, TransitionMatrix
- Aggregate expressions: count_present, earliest_start, latest_end, makespan
"""

from __future__ import annotations

from pycsp3_scheduling.expressions.interval_expr import (
    ExprType,
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

from pycsp3_scheduling.expressions.sequence_expr import (
    start_of_next,
    start_of_prev,
    end_of_next,
    end_of_prev,
    size_of_next,
    size_of_prev,
    length_of_next,
    length_of_prev,
    type_of_next,
    type_of_prev,
    clear_sequence_expr_cache,
)

from pycsp3_scheduling.expressions.element import (
    ElementArray,
    ElementMatrix,
    element,
    element2d,
)

from pycsp3_scheduling.expressions.aggregate import (
    count_present,
    earliest_start,
    latest_end,
    makespan,
    span_length,
)

__all__ = [
    # Expression class
    "IntervalExpr",
    "ExprType",
    # Basic accessors
    "start_of",
    "end_of",
    "size_of",
    "length_of",
    "presence_of",
    # Overlap
    "overlap_length",
    # Utilities
    "expr_min",
    "expr_max",
    # Sequence accessors - Next
    "start_of_next",
    "end_of_next",
    "size_of_next",
    "length_of_next",
    "type_of_next",
    # Sequence accessors - Prev
    "start_of_prev",
    "end_of_prev",
    "size_of_prev",
    "length_of_prev",
    "type_of_prev",
    # Element expressions (array indexing with variables)
    "ElementArray",
    "ElementMatrix",
    "element",
    "element2d",
    # Cache management
    "clear_sequence_expr_cache",
    # Aggregate expressions
    "count_present",
    "earliest_start",
    "latest_end",
    "span_length",
    "makespan",
]
