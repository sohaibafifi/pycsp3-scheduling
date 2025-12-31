"""
Flow-shop Scheduling

This model uses pycsp3-scheduling's IntervalVar and scheduling constraints
to model the classic Flow Shop Scheduling problem.

In a flow shop, all jobs follow the same route through the machines.

## Data Example
  04-04-0.json

## Model
  variables: IntervalVar
  constraints: end_before_start, SeqNoOverlap

## Execution
  python SchedulingFS.py -data=<datafile.json>
  python SchedulingFS.py  (uses default data)

## Links
  - https://en.wikipedia.org/wiki/Flow_shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingFS/SchedulingFS.py

## Tags
  realistic, scheduling, notebook
"""

import json
import os

from pycsp3 import Var, satisfy, minimize, solve, SAT, value, OPTIMUM
from pycsp3_scheduling import (
    IntervalVar,
    SequenceVar,
    SeqNoOverlap,
    end_before_start,
    end_time,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "04-04-0.json")) as f:
    durations = json.load(f)

horizon = sum(sum(t) for t in durations) + 1
n, m = len(durations), len(durations[0])

# ops[i][j] is the interval for machine j of job i
ops = [
    [
        IntervalVar(
            start=(0, horizon),
            size=durations[i][j],
            name=f"op_{i}_{j}",
        )
        for j in range(m)
    ]
    for i in range(n)
]

# Sequences for each machine
sequences = [
    SequenceVar(
        intervals=[ops[i][j] for i in range(n)],
        name=f"machine_{j}",
    )
    for j in range(m)
]

# makespan is the objective
makespan = Var(dom=range(horizon + 1))

satisfy(
    # operations must be ordered on each job (flow shop: same route for all jobs)
    [
        end_before_start(ops[i][j], ops[i][j + 1])
        for i in range(n)
        for j in range(m - 1)
    ],
    # no overlap on each machine
    [SeqNoOverlap(seq) for seq in sequences],
    # makespan is the maximum end time
    [makespan >= end_time(ops[i][-1]) for i in range(n)],
)

minimize(makespan)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Makespan: {value(makespan)}")
        for i in range(n):
            print(f"Job {i}:")
            for j in range(m):
                v = interval_value(ops[i][j])
                print(f"  Machine {j}: [{v['start']}, {v['end']})")
