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
  python RCPSP.py -data=<datafile.json> -solve

## Links
  - https://www.om-db.wi.tum.de/psplib/data.html
  - https://www.csplib.org/Problems/prob061/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/RCPSP/RCPSP.py

## Tags
  realistic, scheduling, csplib, xcsp22
"""

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    start_time,
    SeqCumulative,
)

# Load data - uses pycsp3's -data= argument or falls back to default file
_data = data or load_json_data("j030-01-01.json")

# pycsp3's data converts JSON to named tuples - use attribute access
jobs = [(j.duration, j.successors, j.usages) for j in _data.jobs]
horizon, capacities  = _data.horizon, _data.capacities

durations, successors, quantities = zip(*jobs)
nJobs, nResources = len(jobs), len(capacities)

# task_intervals[i] is the interval for job i
task_intervals = [IntervalVar(start=(0, 0) if i == 0 else (0, horizon), size=durations[i], name=f"job_{i}") for i in range(nJobs)]

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
