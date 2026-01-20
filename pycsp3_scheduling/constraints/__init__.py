"""
Scheduling constraints.

This module provides:
- Precedence constraints: end_before_start, start_at_start, etc.
- Grouping constraints: span, alternative, synchronize
- Sequence constraints: SeqNoOverlap, first, last, before, previous
- Sequence consistency: same_sequence, same_common_subsequence
- Cumulative constraints: Cumulative (capacity constraint)
- Forbidden time constraints: forbid_start, forbid_end, forbid_extent
- Presence constraints: presence_implies, presence_or, presence_xor, etc.
- Chain constraints: chain, strict_chain
- Overlap constraints: must_overlap, overlap_at_least, disjunctive
"""

from __future__ import annotations

# Precedence constraints (exact timing + before)
from pycsp3_scheduling.constraints.precedence import (
    end_at_end,
    end_at_start,
    end_before_end,
    end_before_start,
    start_at_end,
    start_at_start,
    start_before_end,
    start_before_start,
)

# Grouping constraints
from pycsp3_scheduling.constraints.grouping import (
    alternative,
    span,
    synchronize,
)

# Sequence constraints
from pycsp3_scheduling.constraints.sequence import (
    SeqNoOverlap,
    before,
    first,
    last,
    previous,
    same_common_subsequence,
    same_sequence,
)

# Cumulative constraints
from pycsp3_scheduling.constraints.cumulative import (
    SeqCumulative,
    build_cumul_constraint,
)

# Forbidden time constraints
from pycsp3_scheduling.constraints.forbidden import (
    forbid_end,
    forbid_extent,
    forbid_start,
)

# Presence constraints
from pycsp3_scheduling.constraints.presence import (
    all_present_or_all_absent,
    at_least_k_present,
    at_most_k_present,
    exactly_k_present,
    if_present_then,
    presence_implies,
    presence_or,
    presence_or_all,
    presence_xor,
)

# Chain constraints
from pycsp3_scheduling.constraints.chain import (
    chain,
    strict_chain,
)

# Overlap constraints
from pycsp3_scheduling.constraints.overlap import (
    disjunctive,
    must_overlap,
    no_overlap_pairwise,
    overlap_at_least,
)

__all__ = [
    # Exact timing constraints
    "start_at_start",
    "start_at_end",
    "end_at_start",
    "end_at_end",
    # Before constraints
    "start_before_start",
    "start_before_end",
    "end_before_start",
    "end_before_end",
    # Grouping constraints
    "span",
    "alternative",
    "synchronize",
    # Sequence constraints
    "SeqNoOverlap",
    "first",
    "last",
    "before",
    "previous",
    # Sequence consistency
    "same_sequence",
    "same_common_subsequence",
    # Cumulative constraints
    "SeqCumulative",
    "build_cumul_constraint",
    # Forbidden time constraints
    "forbid_start",
    "forbid_end",
    "forbid_extent",
    # Presence constraints
    "presence_implies",
    "presence_or",
    "presence_or_all",
    "presence_xor",
    "all_present_or_all_absent",
    "if_present_then",
    "at_least_k_present",
    "at_most_k_present",
    "exactly_k_present",
    # Chain constraints
    "chain",
    "strict_chain",
    # Overlap constraints
    "must_overlap",
    "overlap_at_least",
    "no_overlap_pairwise",
    "disjunctive",
]
