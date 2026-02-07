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
  python SchedulingOS.py -data=<datafile.json> -solve

## Links
  - https://en.wikipedia.org/wiki/Open-shop_scheduling
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/SchedulingOS/SchedulingOS.py

## Tags
  realistic, scheduling, xcsp25
"""

from pycsp3 import *

# Load data - uses pycsp3's -data= argument or falls back to default file
durations = data or load_json_data("GP-os-01.json")

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

satisfy(
    # operations must be ordered on each job
    [Increasing(s[i], lengths=d[i]) for i in N],

    # each machine must be used exactly once per job
    [AllDifferent(mc[i]) for i in N],

    # link machine choice to duration via Table constraint
    [
        Table(
            scope=(mc[i][j], d[i][j]),
            supports=list(enumerate(durations[i])),
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

)

minimize(Maximum(s[i][-1] + d[i][-1] for i in N))
