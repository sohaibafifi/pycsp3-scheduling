"""
Resource-Constrained Project Scheduling Problem (RCPSP)

This model uses pycsp3-scheduling's IntervalVar and SeqCumulative constraint
to model RCPSP - Problem 061 on CSPLib.

## Data Example
  j030-01-01.json

## Model
  variables: IntervalVar
  constraints: end_before_start, SeqCumulative

## Execution
  python RCPSP.py -data=<datafile.json>

## Links
  - https://www.om-db.wi.tum.de/psplib/data.html
  - https://www.csplib.org/Problems/prob061/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/RCPSP/RCPSP.py

## Tags
  realistic, scheduling, csplib, xcsp22
"""

import json
import os

from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    start_time,
    SeqCumulative,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "j030-01-01.json")) as f:
    _data = json.load(f)

jobs = [(j["duration"], j["successors"], j["usages"]) for j in _data["jobs"]]
horizon = _data["horizon"]
capacities = _data["renewable"]

durations, successors, quantities = zip(*jobs)
nJobs = len(jobs)
nResources = len(capacities)

# task_intervals[i] is the interval for job i
task_intervals = [
    IntervalVar(
        start=(0, 0) if i == 0 else (0, horizon),
        size=durations[i],
        name=f"job_{i}",
    )
    for i in range(nJobs)
]

satisfy(
    # precedence constraints
    [
        end_before_start(task_intervals[i], task_intervals[j])
        for i in range(nJobs)
        for j in successors[i]
    ],
    # resource constraints (cumulative)
    [
        SeqCumulative(
            [task_intervals[i] for i in range(nJobs) if quantities[i][k] > 0],
            heights=[quantities[i][k] for i in range(nJobs) if quantities[i][k] > 0],
            capacity=capacity,
        )
        for k, capacity in enumerate(capacities)
    ],
)

minimize(start_time(task_intervals[-1]))

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        v = interval_value(task_intervals[-1])
        print(f"Makespan: {v['start']}")
        print("\nSchedule:")
        for i in range(nJobs):
            v = interval_value(task_intervals[i])
            res_usage = ", ".join(
                f"R{k}={quantities[i][k]}"
                for k in range(nResources)
                if quantities[i][k] > 0
            )
            print(f"  Job {i:2d}: [{v['start']:3d}, {v['end']:3d}) dur={durations[i]:2d} {res_usage}")
