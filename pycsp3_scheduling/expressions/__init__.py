"""
Expression functions for interval variables.

This module provides accessor functions that return expressions from interval variables:
- start_of, end_of, size_of, length_of, presence_of
- overlap_length
- expr_min, expr_max
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
]
