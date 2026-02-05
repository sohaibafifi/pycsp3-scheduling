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
  python MRCPSP.py -data=<datafile.json> -solve

## Links
  - https://www.minizinc.org/challenge/2023/results/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/MRCPSP/MRCPSP.py

## Tags
  realistic, scheduling, mzn16, mzn23
"""

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    end_time,
    presence_time,
    start_time,
    alternative,
)

# Load data - uses pycsp3's -data= argument or falls back to default file
_data = data or load_json_data("j30-15-05.json")

# pycsp3's data converts JSON to named tuples - use attribute access
capacities = _data.resources.capacities
types = _data.resources.types
mode_durations = _data.mode_durations
modes = _data.tasks.modes
successors = _data.tasks.successors
requirements_raw = _data.tasks.requirements

nResources, nTasks, nModes = len(capacities), len(modes), len(mode_durations)
duration_by_mode = cp_array(mode_durations)
requirement_by_resource = [cp_array(requirements_raw[k]) for k in range(nResources)]

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

# presence expression for each mode interval
mode_present = cp_array([presence_time(mode_intervals[m]) for m in range(nModes)])

makespan = Var(dom=range(UB + 1))

satisfy(
    # each task uses exactly one mode (alternative constraint)
    [alternative(task_intervals[i], [mode_intervals[m] for m in modes[i]]) for i in range(nTasks)],
    # selected tm[i] must correspond to a present mode interval
    [mode_present[tm[i]] == 1 for i in range(nTasks)],
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
            lengths=[duration_by_mode[tm[i]] for i in range(nTasks)],
            heights=[requirement_by_resource[k][tm[i]] for i in range(nTasks)],
        ) <= capacities[k]
        for k in renewable
    ],
    # non-renewable resource constraints (total usage)
    [
        Sum(requirement_by_resource[k][tm[i]] for i in range(nTasks)) <= capacities[k]
        for k in non_renewable
    ],
    # makespan is the max end time of tasks with no successors
    makespan == Maximum(end_time(task_intervals[i]) for i in range(nTasks) if len(successors[i]) == 0),
)

minimize(makespan)
