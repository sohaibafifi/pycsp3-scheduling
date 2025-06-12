"""
Scheduling constraints.

This module provides:
- Precedence constraints: end_before_start, start_at_start, etc.
- Grouping constraints: span, alternative, synchronize
- Sequence constraints: SeqNoOverlap, first, last, before, previous
- Cumulative constraints: cumul_range, always_in
- State constraints: always_equal, always_constant, always_no_state
- Forbidden region constraints: forbid_start, forbid_end, forbid_extent
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

# Sequence constraints
from pycsp3_scheduling.constraints.sequence import SeqNoOverlap

# To be implemented:
# from pycsp3_scheduling.constraints.grouping import (
#     span, alternative, synchronize, isomorphism,
# )
# from pycsp3_scheduling.constraints.cumulative import (
#     cumul_range,
# )
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
    # Sequence constraints
    "SeqNoOverlap",
]
