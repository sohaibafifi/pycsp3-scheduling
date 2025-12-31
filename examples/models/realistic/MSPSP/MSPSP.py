"""
Multi-Skilled Project Scheduling Problem (MSPSP)

This model uses pycsp3-scheduling's IntervalVar and SeqCumulative constraint
to model MSPSP where workers have skills and tasks require specific skills.

## Data Example
  easy-01.json

## Model
  variables: IntervalVar
  constraints: end_before_start, SeqCumulative, Cumulative

## Execution
  python MSPSP.py -data=<datafile.json>

## Links
  - https://www.minizinc.org/challenge/2012/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/MSPSP/MSPSP.py

## Tags
  realistic, scheduling, mzn12
"""

import json
import os
from itertools import combinations

from pycsp3 import (
    Var,
    VarArray,
    Cumulative,
    Sum,
    satisfy,
    minimize,
    solve,
    SAT,
    OPTIMUM,
    value,
)
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    start_time,
    end_time,
    SeqCumulative,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "easy-01.json")) as f:
    _data = json.load(f)

skills = _data["skills"]
durations = _data["durations"]
requirements = _data["requirements"]
successors = _data["successors"]

nWorkers, nTasks, nSkills = len(skills), len(durations), len(requirements)

# Resource capacity: count of workers per skill
rc = [len([j for j in range(nWorkers) if i in skills[j]]) for i in range(nSkills)]

# Possible workers for each task (workers with at least one required skill)
possibleWorkers = [
    [j for j in range(nWorkers) if len([k for k in skills[j] if requirements[k][i] > 0]) > 0]
    for i in range(nTasks)
]

# Tasks per worker
WTasks = [
    [i for i in range(nTasks) if len([k for k in skills[j] if requirements[k][i] > 0]) > 0]
    for j in range(nWorkers)
]

# Tasks per skill
RTasks = [[i for i in range(nTasks) if requirements[k][i] > 0] for k in range(nSkills)]

# Pairs of tasks that might conflict due to resource scarcity
overlap_attention = [
    (i, j)
    for i, j in combinations(nTasks, 2)
    if j not in successors[i]
    and i not in successors[j]
    and len([k for k in range(nSkills) if requirements[k][i] + requirements[k][j] > rc[k]]) > 0
]

horizon = sum(durations)

# task_intervals[i] is the interval for task i
task_intervals = [
    IntervalVar(
        start=(0, horizon),
        size=durations[i],
        name=f"task_{i}",
    )
    for i in range(nTasks)
]

# w[j][i] is 1 if worker j is assigned to task i
w = VarArray(size=[nWorkers, nTasks], dom={0, 1})

# z is the project duration
z = Var(dom=range(horizon + 1))

satisfy(
    # precedence constraints
    [
        end_before_start(task_intervals[i], task_intervals[j])
        for i in range(nTasks)
        for j in successors[i]
    ],
    # skill requirements must be met
    [
        Sum(w[j][i] for j in possibleWorkers[i] if k in skills[j]) >= R
        for i in range(nTasks)
        for k in range(nSkills)
        if (R := requirements[k][i]) > 0
    ],
    # discard impossible worker assignments
    [w[j][i] == 0 for i in range(nTasks) for j in range(nWorkers) if j not in possibleWorkers[i]],
    # workers cannot work on overlapping tasks (cumulative per worker, using pycsp3's Cumulative)
    [
        Cumulative(
            origins=[start_time(task_intervals[i]) for i in WTasks[j]],
            lengths=[durations[i] for i in WTasks[j]],
            heights=[w[j][i] for i in WTasks[j]],
        ) <= 1
        for j in range(nWorkers)
        if len(WTasks[j]) > 1
    ],
    # tasks that cannot overlap due to resource constraints
    [
        (end_time(task_intervals[i]) <= start_time(task_intervals[j]))
        | (end_time(task_intervals[j]) <= start_time(task_intervals[i]))
        for i, j in overlap_attention
    ],
    # cumulative skill constraints
    [
        SeqCumulative(
            [task_intervals[i] for i in RTasks[k]],
            heights=[requirements[k][i] for i in RTasks[k]],
            capacity=rc[k],
        )
        for k in range(nSkills)
        if len(RTasks[k]) > 1 and sum(requirements[k][i] for i in RTasks[k]) > rc[k]
    ],
    # project duration constraint
    [end_time(task_intervals[i]) <= z for i in range(nTasks) if len(successors[i]) == 0],
)

minimize(z)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Project Duration: {value(z)}")
        print("\nSchedule:")
        for i in range(nTasks):
            v = interval_value(task_intervals[i])
            assigned = [j for j in range(nWorkers) if value(w[j][i]) == 1]
            print(f"  Task {i:2d}: [{v['start']:3d}, {v['end']:3d}) workers={assigned}")
