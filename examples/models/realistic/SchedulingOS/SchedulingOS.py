"""
Open-shop Scheduling

This model uses pycsp3's native NoOverlap constraint for the Open Shop
Scheduling problem, since open-shop requires variable durations that depend
on machine assignment (not a fixed size per operation).

In an open shop, each job has operations on each machine, but the order
of machines for each job is flexible (to be determined by the solver).

## Data Example
  GP-os-01.json

## Model
  variables: Var (integer)
  constraints: NoOverlap, AllDifferent, Table

## Execution
  python SchedulingOS.py -data=<datafile.json>
  python SchedulingOS.py  (uses default data)

## Links
  - https://en.wikipedia.org/wiki/Open-shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingOS/SchedulingOS.py

## Tags
  realistic, scheduling, xcsp25
"""

import json
import os

from pycsp3 import (
    Var, VarArray, satisfy, minimize, solve, SAT, OPTIMUM, value,
    AllDifferent, Table, NoOverlap
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "GP-os-01.json")) as f:
    durations = json.load(f)

horizon = sum(sum(t) for t in durations) + 1

n, m = len(durations), len(durations[0])
N, M = range(n), range(m)

# s[i][j] is the start time of the jth operation of job i
s = VarArray(size=[n, m], dom=range(horizon))

# mc[i][j] is the machine used for the jth operation of job i
mc = VarArray(size=[n, m], dom=range(m))

# d[i][j] is the duration of the jth operation of job i
d = VarArray(size=[n, m], dom=lambda i, j: durations[i])

# sd[i][k] is the start time when machine k is used for job i
sd = VarArray(size=[n, m], dom=range(horizon))

# makespan is the objective
makespan = Var(dom=range(horizon + 1))

satisfy(
    # operations must be non-overlapping within each job (sequential)
    [s[i][j] + d[i][j] <= s[i][j + 1] for i in N for j in range(m - 1)],

    # each machine must be used exactly once per job
    [AllDifferent(mc[i]) for i in N],

    # link machine choice to duration via Table constraint
    [
        Table(
            scope=(mc[i][j], d[i][j]),
            supports=enumerate(durations[i]),
        )
        for j in M
        for i in N
    ],

    # channeling: sd[i][mc[i][j]] == start of operation
    [sd[i][mc[i][j]] == s[i][j] for j in M for i in N],

    # no overlap on each machine across all jobs
    [
        NoOverlap(
            origins=[sd[i][k] for i in N],
            lengths=durations[:, k],
        )
        for k in M
    ],

    # redundant: minimum completion time
    [s[i][-1] + d[i][-1] >= sum(durations[i]) for i in N],

    # makespan is the maximum end time
    [makespan >= s[i][-1] + d[i][-1] for i in N],
)

minimize(makespan)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Makespan: {value(makespan)}")
        for i in N:
            print(f"Job {i}:")
            for j in M:
                start = value(s[i][j])
                machine = value(mc[i][j])
                dur = value(d[i][j])
                print(f"  Op {j} on M{machine} (dur={dur}): [{start}, {start + dur})")
