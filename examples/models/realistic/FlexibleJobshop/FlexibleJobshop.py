"""
Flexible Job Shop Scheduling

This model uses pycsp3-scheduling's IntervalVar with optional intervals
and alternative constraints to model the Flexible Job Shop problem.

Each task can be executed on one of several alternative machines,
and the goal is to minimize the makespan.

## Data Example
  easy01.json

## Model
  variables: IntervalVar (optional)
  constraints: end_before_start, alternative, SeqCumulative

## Execution
  python FlexibleJobshop.py -data=<datafile.json>
  python FlexibleJobshop.py -data=<datafile.json> -solve
  python data/convert_dzn_to_json.py --input-dir=<folder-with-dzn> --output-dir=data

## Links
  - https://www.minizinc.org/challenge/2013/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/FlexibleJobshop/FlexibleJobshop.py

## Tags
  realistic, scheduling, mzn13
"""

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    end_time,
    alternative,
    SeqCumulative,
)

# Load data - uses pycsp3's -data= argument or falls back to default file
_data = data or load_json_data("easy01.json")

# pycsp3's data converts JSON to named tuples - use attribute access
nMachines = _data.nMachines
tasks = _data.tasks
options = _data.optionalTasks
option_machines = _data.machines
option_durations = _data.durations

nJobs, nTasks, nOptions = len(tasks), len(options), len(option_machines)
J, T, O, M = range(nJobs), range(nTasks), range(nOptions), range(nMachines)

# Compute auxiliary information
siblings = [next(tasks[j] for j in J if t in tasks[j]) for t in T]
minDurations = [min(option_durations[options[t]]) for t in T]
maxDurations = [max(option_durations[options[t]]) for t in T]
minStarts = [sum(minDurations[k] for k in siblings[t] if k < t) for t in T]
horizon = sum(option_durations)
maxStarts = [horizon - sum(minDurations[k] for k in siblings[t] if k >= t) for t in T]

taskForOption = [next(t for t in T if o in options[t]) for o in O]

# task_intervals[t] is the main interval for task t
task_intervals = [
    IntervalVar(
        start=(minStarts[t], maxStarts[t]),
        size=(minDurations[t], maxDurations[t]),
        name=f"task_{t}",
    )
    for t in T
]

# opt_intervals[o] is the optional interval for option o
opt_intervals = [
    IntervalVar(
        start=(minStarts[taskForOption[o]], maxStarts[taskForOption[o]]),
        size=option_durations[o],
        optional=True,
        name=f"opt_{o}",
    )
    for o in O
]

satisfy(
    # precedence: tasks within a job must be sequential
    [
        end_before_start(task_intervals[t], task_intervals[t + 1])
        for j in J
        for t in tasks[j][:-1]
    ],
    # alternative: each task is performed by exactly one option
    [alternative(task_intervals[t], [opt_intervals[o] for o in options[t]]) for t in T],
    # cumulative: at most one operation per machine at a time
    [
        SeqCumulative(
            [opt_intervals[o] for o in O if option_machines[o] == m],
            heights=[1 for o in O if option_machines[o] == m],
            capacity=1,
        )
        for m in M
    ],
)

minimize(Maximum(end_time(task_intervals[tasks[j][-1]]) for j in J))
