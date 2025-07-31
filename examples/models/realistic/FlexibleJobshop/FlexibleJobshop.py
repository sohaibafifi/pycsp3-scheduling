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

## Links
  - https://www.minizinc.org/challenge/2013/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/FlexibleJobshop/FlexibleJobshop.py

## Tags
  realistic, scheduling, mzn13
"""

import json
import os

from pycsp3 import Var, satisfy, minimize, solve, SAT, OPTIMUM, value
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    end_time,
    alternative,
    SeqCumulative,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "easy01.json")) as f:
    _data = json.load(f)

nMachines = _data["nMachines"]
tasks = _data["tasks"]
options = _data["optionalTasks"]
option_machines = _data["machines"]
option_durations = _data["durations"]

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

# makespan is the objective
makespan = Var(dom=range(horizon + 1))

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
    # makespan
    [makespan >= end_time(task_intervals[tasks[j][-1]]) for j in J],
)

minimize(makespan)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Makespan: {value(makespan)}")
        for j in J:
            print(f"Job {j}:")
            for t in tasks[j]:
                v = interval_value(task_intervals[t])
                # Find which option was selected
                selected_opt = None
                for o in options[t]:
                    ov = interval_value(opt_intervals[o])
                    if ov is not None and ov["present"]:
                        selected_opt = o
                        break
                machine = option_machines[selected_opt] if selected_opt is not None else "?"
                print(f"  Task {t} on M{machine}: [{v['start']}, {v['end']})")
