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
  python SchedulingJS.py -data=<datafile.json> -solve

## Links
  - https://en.wikipedia.org/wiki/Job_shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingJS/SchedulingJS.py

## Tags
  realistic, scheduling
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
jobs = data or load_json_data("e0ddr1-0.json")

durations, resources, release_dates, due_dates = zip(*jobs)
assert all(len(t) == len(durations[0]) for t in durations) and all(len(t) == len(durations[0]) for t in resources)


n, m = len(jobs), len(durations[0])

horizon = max(due_dates) if all(v != -1 for v in due_dates) else sum(sum(t) for t in durations)


# ops[i][j] is the interval for the jth operation of the ith job
ops = [[IntervalVar(
            start=(release_dates[i], horizon),
            end=(0, due_dates[i] if due_dates[i] != -1 else horizon),
            size=durations[i][j],
            name=f"op_{i}_{j}",
        ) for j in range(m)]
    for i in range(n)]

# Sequences for each machine
sequences = [SequenceVar(intervals=[ops[i][resources[i].index(k)] for i in range(n)], name=f"machine_{k}") for k in range(m)]

satisfy(
    # operations must be ordered on each job
    [
        Increasing(
            [start_time(ops[i][j]) for j in range(m)],
            lengths=durations[i],
        )
        for i in range(n)
    ],
    # respecting release dates
    [start_time(ops[i][0]) > release_dates[i] for i in range(n) if release_dates[i] > 0],
    # respecting due dates
    [
        start_time(ops[i][-1]) <= due_dates[i] - durations[i][-1]
        for i in range(n)
        if 0 <= due_dates[i] < horizon - 1
    ],
    # no overlap on resources (machines)
    [SeqNoOverlap(seq) for seq in sequences],
)

minimize(Maximum(end_time(ops[i][-1]) for i in range(n)))
