"""
Scheduling constraints.

This module provides:
- Precedence constraints: end_before_start, start_at_start, etc.
- Grouping constraints: span, alternative, synchronize
- Sequence constraints: SeqNoOverlap, first, last, before, previous
- Sequence consistency: same_sequence, same_common_subsequence
- Cumulative constraints: Cumulative (capacity constraint)
- State constraints: always_equal, always_constant, always_no_state (future)
- Forbidden region constraints: forbid_start, forbid_end, forbid_extent (future)
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

# To be implemented:
# from pycsp3_scheduling.constraints.state import (
#     always_in, always_equal, always_constant, always_no_state,
# )
# from pycsp3_scheduling.constraints.forbidden import (
#     forbid_start, forbid_end, forbid_extent,
# )

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
]
