"""
Multi-mode Resource-constrained Project Scheduling (MRCPSP)

This model uses pycsp3-scheduling's IntervalVar with optional intervals
and alternative constraints to model MRCPSP where each task can be
executed in different modes (different durations and resource requirements).

## Data Example
  j30-15-05.json

## Model
  variables: IntervalVar (optional for modes)
  constraints: end_before_start, alternative, Cumulative (pycsp3)

## Execution
  python MRCPSP.py -data=<datafile.json>

## Links
  - https://www.minizinc.org/challenge/2023/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/MRCPSP/MRCPSP.py

## Tags
  realistic, scheduling, mzn16, mzn23
"""

import json
import os

from pycsp3 import (
    Var,
    VarArray,
    Cumulative,
    Table,
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
    end_time,
    start_time,
    alternative,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "j30-15-05.json")) as f:
    _data = json.load(f)

capacities = _data["resources"]["capacities"]
types = _data["resources"]["types"]
mode_durations = _data["mode_durations"]
modes = _data["tasks"]["modes"]
successors = _data["tasks"]["successors"]
requirements_raw = _data["tasks"]["requirements"]

nResources, nTasks, nModes = len(capacities), len(modes), len(mode_durations)


# Helper function for requirements indexing (k=resource, m=mode)
def requirements(k, m):
    return requirements_raw[k][m]

renewable = [k for k in range(nResources) if types[k] == 1]
non_renewable = [k for k in range(nResources) if types[k] == 2]

UB = sum(max(mode_durations[m] for m in modes[i]) for i in range(nTasks))

# task_intervals[i] is the main interval for task i
task_intervals = [
    IntervalVar(
        start=(0, UB),
        size=(
            min(mode_durations[m] for m in modes[i]),
            max(mode_durations[m] for m in modes[i]),
        ),
        name=f"task_{i}",
    )
    for i in range(nTasks)
]

# mode_intervals[m] is the optional interval for mode m
mode_intervals = [
    IntervalVar(
        start=(0, UB),
        size=mode_durations[m],
        optional=True,
        name=f"mode_{m}",
    )
    for m in range(nModes)
]

# tm[i] is the mode selected for task i
tm = VarArray(size=nTasks, dom=lambda i: modes[i])

# dur[i] is the duration of task i (linked to selected mode)
dur = VarArray(size=nTasks, dom=lambda i: {mode_durations[m] for m in modes[i]})

# r[k][i] is the resource requirement for resource k and task i
r = VarArray(
    size=[nResources, nTasks],
    dom=lambda k, i: {requirements(k, m) for m in modes[i]},
)

# makespan variable
makespan = Var(dom=range(UB + 1))

satisfy(
    # each task uses exactly one mode (alternative constraint)
    [alternative(task_intervals[i], [mode_intervals[m] for m in modes[i]]) for i in range(nTasks)],
    # link tm to duration via Table
    [
        Table(
            scope=(tm[i], dur[i]),
            supports=[(m, mode_durations[m]) for m in modes[i]],
        )
        for i in range(nTasks)
    ],
    # link resource requirements to selected mode
    [
        Table(
            scope=(tm[i], r[k][i]),
            supports=[(m, requirements(k, m)) for m in modes[i]],
        )
        for k in range(nResources)
        for i in range(nTasks)
    ],
    # precedence constraints
    [
        end_before_start(task_intervals[i], task_intervals[j])
        for i in range(nTasks)
        for j in successors[i]
    ],
    # cumulative constraints for renewable resources (using pycsp3's native Cumulative)
    [
        Cumulative(
            origins=[start_time(task_intervals[i]) for i in range(nTasks)],
            lengths=dur,
            heights=r[k],
        ) <= capacities[k]
        for k in renewable
    ],
    # non-renewable resource constraints (total usage)
    [Sum(r[k]) <= capacities[k] for k in non_renewable],
    # makespan is the max end time of tasks with no successors
    [makespan >= end_time(task_intervals[i]) for i in range(nTasks) if len(successors[i]) == 0],
)

minimize(makespan)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Makespan: {value(makespan)}")
        print("\nSchedule:")
        for i in range(nTasks):
            v = interval_value(task_intervals[i])
            mode = value(tm[i])
            res_usage = ", ".join(
                f"R{k}={value(r[k][i])}" for k in range(nResources) if value(r[k][i]) > 0
            )
            print(f"  Task {i:2d} (mode {mode}): [{v.start:3d}, {v.end:3d}) {res_usage}")
