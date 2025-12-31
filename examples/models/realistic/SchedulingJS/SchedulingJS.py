"""
Job-shop Scheduling

This model uses pycsp3-scheduling's IntervalVar and scheduling constraints
to model the classic Job Shop Scheduling problem.

## Data Example
  e0ddr1-0.json

## Model
  variables: IntervalVar
  constraints: end_before_start, NoOverlap

## Execution
  python SchedulingJS.py -data=<datafile.json>
  python SchedulingJS.py  (uses default data)

## Links
  - https://en.wikipedia.org/wiki/Job_shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingJS/SchedulingJS.py

## Tags
  realistic, scheduling
"""

import json
import os

from pycsp3 import Var, satisfy, minimize, solve, SAT, OPTIMUM, value
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
with open(os.path.join(_data_dir, "e0ddr1-0.json")) as f:
    jobs = json.load(f)

durations, resources, release_dates, due_dates = zip(*jobs)
assert all(len(t) == len(durations[0]) for t in durations) and all(
    len(t) == len(durations[0]) for t in resources
)

n, m = len(jobs), len(durations[0])

horizon = (
    max(due_dates)
    if all(v != -1 for v in due_dates)
    else sum(sum(t) for t in durations)
)

# ops[i][j] is the interval for the jth operation of the ith job
ops = [
    [
        IntervalVar(
            start=(release_dates[i], horizon),
            end=(0, due_dates[i] if due_dates[i] != -1 else horizon),
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
        intervals=[ops[i][resources[i].index(k)] for i in range(n)],
        name=f"machine_{k}",
    )
    for k in range(m)
]

# makespan is the objective interval
makespan = Var(dom=range(horizon + 1))

satisfy(
    # operations must be ordered on each job (precedence)
    [
        end_before_start(ops[i][j], ops[i][j + 1])
        for i in range(n)
        for j in range(m - 1)
    ],
    # no overlap on resources (machines)
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
                machine = resources[i][j]
                print(f"  Op {j} on M{machine}: [{v['start']}, {v['end']})")
