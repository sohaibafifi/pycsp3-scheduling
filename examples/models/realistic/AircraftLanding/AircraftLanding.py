"""
Aircraft Landing Problem

This model uses pycsp3-scheduling's IntervalVar and pycsp3's NoOverlap constraint
to schedule aircraft landings while respecting separation requirements.

## Data Example
  airland01.json

## Model
  variables: IntervalVar
  constraints: NoOverlap (pycsp3)

## Execution
  python AircraftLanding.py -data=<datafile.json>

## Links
  - http://people.brunel.ac.uk/~mastjjb/jeb/orlib/airlandinfo.html
  - https://www.jstor.org/stable/25768908
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/AircraftLanding/AircraftLanding.py

## Tags
  realistic, scheduling, xcsp22
"""

import json
import os
from itertools import combinations

from pycsp3 import (
    Var,
    VarArray,
    AllDifferent,
    NoOverlap,
    satisfy,
    minimize,
    solve,
    SAT,
    OPTIMUM,
    value,
)
from pycsp3_scheduling import (
    IntervalVar,
    start_time,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "airland01.json")) as f:
    _data = json.load(f)

nPlanes = _data["nPlanes"]
times = [(t["earliest"], t["target"], t["latest"]) for t in _data["times"]]
costs = [(c["early_penalty"], c["late_penalty"]) for c in _data["costs"]]
separations = _data["separations"]

earliest, target, latest = zip(*times)
early_penalties, late_penalties = zip(*costs)

P = range(nPlanes)

# landing[i] is the interval for plane i's landing (size=1 represents the landing event)
landing = [
    IntervalVar(
        start=(earliest[i], latest[i]),
        size=1,  # Landing is a point event with size 1
        name=f"plane_{i}",
    )
    for i in P
]

# x[i] is the landing time of plane i (for easier access)
x = VarArray(size=nPlanes, dom=lambda i: range(earliest[i], latest[i] + 1))

# erl[i] is the earliness of plane i
erl = VarArray(size=nPlanes, dom=lambda i: range(target[i] - earliest[i] + 1))

# trd[i] is the tardiness of plane i
trd = VarArray(size=nPlanes, dom=lambda i: range(latest[i] - target[i] + 1))

satisfy(
    # link landing interval to x variable
    [start_time(landing[i]) == x[i] for i in P],
    # planes must land at different times
    AllDifferent(x),
    # separation constraints using NoOverlap
    [
        NoOverlap(
            origins=[x[i], x[j]],
            lengths=[separations[i][j], separations[j][i]],
        )
        for i, j in combinations(P, 2)
    ],
    # computing earliness of planes
    [erl[i] == max(0, target[i] - x[i]) for i in P],
    # computing tardiness of planes
    [trd[i] == max(0, x[i] - target[i]) for i in P],
)

minimize(
    # minimizing the deviation cost
    erl * early_penalties + trd * late_penalties
)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        total_cost = sum(
            value(erl[i]) * early_penalties[i] + value(trd[i]) * late_penalties[i]
            for i in P
        )
        print(f"Total deviation cost: {total_cost}")
        print("\nLanding schedule:")
        for i in P:
            v = interval_value(landing[i])
            early = value(erl[i])
            late = value(trd[i])
            status = f"early={early}" if early > 0 else (f"late={late}" if late > 0 else "on-time")
            print(
                f"  Plane {i}: land at {v['start']} (target={target[i]}, window=[{earliest[i]},{latest[i]}]) {status}"
            )
