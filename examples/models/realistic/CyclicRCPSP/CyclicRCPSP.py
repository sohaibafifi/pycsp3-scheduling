"""
Cyclic Resource-Constrained Project Scheduling (CyclicRCPSP)

This is a cyclic RCPSP with generalised precedence relations,
where tasks are repeated infinitely and the goal is to minimize
the cycle period.

## Data Example
  easy-4.json

## Model
  variables: IntervalVar
  constraints: SeqCumulative

## Execution
  python CyclicRCPSP.py -data=<datafile.json>

## Links
  - https://www.minizinc.org/challenge/2014/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/CyclicRCPSP/CyclicRCPSP.py

## Tags
  realistic, scheduling, mzn11, mzn14
"""

import json
import os
from itertools import combinations

from pycsp3 import (
    Var,
    VarArray,
    Maximum,
    Minimum,
    either,
    satisfy,
    minimize,
    solve,
    SAT,
    OPTIMUM,
    value,
)
from pycsp3_scheduling import (
    IntervalVar,
    SeqCumulative,
    start_time,
    end_time,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "easy-4.json")) as f:
    _data = json.load(f)

capacities = _data["capacities"]
requirements = _data["requirements"]
precedences = _data["precedences"]

nResources, nTasks, nPrecedences = len(capacities), len(requirements), len(precedences)

R, T = range(nResources), range(nTasks)

# Tasks have unit duration except artificial source/sink
d = [0] + [1] * (nTasks - 2) + [0]
horizon = sum(precedences[i][2] for i in range(nPrecedences))

# Resources per task (tasks that use resource r)
resources = [[i for i in T if requirements[i][r] > 0 and d[i] > 0] for r in R]

# task_intervals[i] is the interval for task i
task_intervals = [
    IntervalVar(
        start=(0, horizon),
        size=d[i],
        name=f"task_{i}",
    )
    for i in T
]

# k[i] is the iteration of the ith task
k = VarArray(size=nTasks, dom=range(nTasks + 1))

# b[j] is 1 if the jth precedence relation is respected (wrt latency)
b = VarArray(size=nPrecedences, dom={0, 1})

# z is the make-span of one iteration
z = Var(dom=range(horizon + 1))

# period is the cycle length
period = start_time(task_intervals[-1])

satisfy(
    # computing the make-span
    z == 1 + Maximum(start_time(task_intervals[i]) - k[i] * period for i in T[:-1])
        - Minimum(start_time(task_intervals[i]) - k[i] * period for i in T[:-1]),
    # generalised precedence constraints
    [
        (
            b[p] == (start_time(task_intervals[i]) + latency <= start_time(task_intervals[j])),
            k[i] + ~b[p] <= k[j] + distance,
        )
        for p, (i, j, latency, distance) in enumerate(precedences)
    ],
    # redundant non-overlapping constraints
    [
        either(
            end_time(task_intervals[i]) <= start_time(task_intervals[j]),
            end_time(task_intervals[j]) <= start_time(task_intervals[i]),
        )
        for i, j in combinations(T, 2)
        if any(requirements[i][r] + requirements[j][r] > capacities[r] for r in R)
    ],
    # cumulative resource constraints
    [
        SeqCumulative(
            [task_intervals[i] for i in resources[r]],
            heights=[requirements[i][r] for i in resources[r]],
            capacity=capacities[r],
        )
        for r in R
        if sum(requirements[i][r] for i in resources[r]) > capacities[r]
    ],
    # computing the value of the last iteration
    k[-1] == Maximum(k[:-1]),
    # ensuring the last task starts after all other ones
    [end_time(task_intervals[i]) <= period for i in T[:-1]],
    # symmetry-breaking
    start_time(task_intervals[0]) == 0,
    k[0] == 0,
)

minimize(
    # minimizing period * horizon + makespan
    period * horizon + z
)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        v_last = interval_value(task_intervals[-1])
        print(f"Period: {v_last['start']}")
        print(f"Makespan: {value(z)}")
        print("\nSchedule:")
        for i in T:
            v = interval_value(task_intervals[i])
            iter_val = value(k[i])
            print(f"  Task {i:2d}: start={v['start']:3d} iter={iter_val}")
