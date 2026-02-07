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
  python SchedulingFS.py -data=<datafile.json> -solve

## Links
  - https://en.wikipedia.org/wiki/Flow_shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingFS/SchedulingFS.py

## Tags
  realistic, scheduling, notebook
"""

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    SequenceVar,
    SeqNoOverlap,
    start_time,
    end_time,
)

# Load data - uses pycsp3's -data= argument or falls back to default file
durations = data or load_json_data("04-04-0.json")

horizon = sum(sum(t) for t in durations) + 1
n, m = len(durations), len(durations[0])

# ops[i][j] is the interval for machine j of job i
ops = [
    [IntervalVar(start=(0, horizon),size=durations[i][j], name=f"op_{i}_{j}") for j in range(m)]
    for i in range(n)
]

# Sequences for each machine
sequences = [SequenceVar(intervals=[ops[i][j] for i in range(n)], name=f"machine_{j}") for j in range(m)]

satisfy(
    # operations must be ordered on each job (flow shop: same route for all jobs)
    [
        Increasing(
            [start_time(ops[i][j]) for j in range(m)],
            lengths=durations[i],
        )
        for i in range(n)
    ],
    # no overlap on each machine
    [SeqNoOverlap(seq) for seq in sequences],
)

minimize(Maximum(end_time(ops[i][-1]) for i in range(n)))
