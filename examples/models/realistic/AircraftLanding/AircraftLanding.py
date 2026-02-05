"""
Aircraft Landing Problem - Clean Scheduling Model (v2)

This model uses pycsp3-scheduling's IntervalVar with minimal auxiliary variables.

## Improvements over v1:
1. Eliminates redundant x[] variables - uses start_time() directly
2. Simplifies earliness/tardiness computation using inequalities
3. Removes redundant AllDifferent (separations already enforce it)

## Execution
  python AircraftLanding.py -data=<datafile.json> -solve

## Links
  - http://people.brunel.ac.uk/~mastjjb/jeb/orlib/airlandinfo.html
"""

from itertools import combinations

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, start_time

# Load data
_data = data or load_json_data("airland01.json")

nPlanes = _data.P
times = [(t.earliest, t.target, t.latest) for t in _data.times]
costs = [(c.early_penalty, c.late_penalty) for c in _data.costs]
separations = _data.separations

earliest, target, latest = zip(*times)
early_penalties, late_penalties = zip(*costs)

P = range(nPlanes)

# =============================================================================
# Variables
# =============================================================================

# Landing interval for each plane
landing = [
    IntervalVar(
        start=(earliest[i], latest[i]),
        size=1,
        name=f"plane_{i}",
    )
    for i in P
]

# Earliness and tardiness (auxiliary for objective)
erl = VarArray(size=nPlanes, dom=lambda i: range(target[i] - earliest[i] + 1))
trd = VarArray(size=nPlanes, dom=lambda i: range(latest[i] - target[i] + 1))

# =============================================================================
# Constraints
# =============================================================================

satisfy(
    # Separation constraints between all pairs of planes
    [
        NoOverlap(
            origins=[start_time(landing[i]), start_time(landing[j])],
            lengths=[separations[i][j], separations[j][i]],
        )
        for i, j in combinations(P, 2)
    ],

    # Earliness: erl[i] >= target[i] - landing_time[i]
    # (minimization will set erl[i] = max(0, target - landing_time))
    [erl[i] >= target[i] - start_time(landing[i]) for i in P],

    # Tardiness: trd[i] >= landing_time[i] - target[i]
    [trd[i] >= start_time(landing[i]) - target[i] for i in P],
)

# =============================================================================
# Objective
# =============================================================================

minimize(erl * early_penalties + trd * late_penalties)
