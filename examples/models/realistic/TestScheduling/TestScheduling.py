"""
Test Scheduling Problem

This problem was presented as the Industrial Modelling Challenge at CP2015.
Tests must be performed in minimal time on machines with resource constraints.

## Data Example
  t020m10r03-1.json

## Model
  variables: IntervalVar
  constraints: NoOverlap (pycsp3), SeqCumulative

## Execution
  python TestScheduling.py -data=<datafile.json>

## Links
  - https://www.csplib.org/Problems/prob073/
  - https://github.com/xcsp3team/PyCSP3-models/blob/main/realistic/TestScheduling/TestScheduling.py

## Tags
  realistic, scheduling, csplib, xcsp24
"""

import json
import os
from itertools import combinations

from pycsp3 import (
    Var,
    VarArray,
    If,
    Then,
    either,
    satisfy,
    minimize,
    solve,
    SAT,
    OPTIMUM,
    value,
)
from pycsp3_scheduling import (
    IntervalVar,
    SequenceVar,
    SeqNoOverlap,
    SeqCumulative,
    start_time,
    end_time,
    interval_value,
)

# Load data
_data_dir = os.path.join(os.path.dirname(__file__), "data")
with open(os.path.join(_data_dir, "t020m10r03-1.json")) as f:
    _data = json.load(f)

nMachines = _data["nMachines"]
nResources = _data["nResources"]
tests = [(t["duration"], t["machines"], t["resources"]) for t in _data["tests"]]

durations, machines, resources = zip(*tests)

nTests = len(tests)
horizon = sum(durations) + 1

# Group tests by single pre-assigned machines
tests_by_single_machines = [
    t
    for t in [
        [i for i in range(nTests) if len(machines[i]) == 1 and m in machines[i]]
        for m in range(nMachines)
    ]
    if len(t) > 1
]

# Group tests by shared resources
tests_by_resources = [
    t
    for t in [[i for i in range(nTests) if r in resources[i]] for r in range(nResources)]
    if len(t) > 1
]


def conflicting_tests():
    """Find pairs of tests that may conflict due to shared machines."""

    def possibly_conflicting(i, j):
        return (
            len(machines[i]) == 0
            or len(machines[j]) == 0
            or len(set(machines[i] + machines[j])) != len(machines[i]) + len(machines[j])
        )

    pairs = [(i, j) for i, j in combinations(nTests, 2) if possibly_conflicting(i, j)]
    for t in tests_by_single_machines + tests_by_resources:
        for i, j in combinations(t, 2):
            if (i, j) in pairs:
                pairs.remove((i, j))
    return pairs


# test_intervals[i] is the interval for test i
test_intervals = [
    IntervalVar(
        start=(0, horizon),
        size=durations[i],
        name=f"test_{i}",
    )
    for i in range(nTests)
]

# m[i] is the machine used for test i
m = VarArray(
    size=nTests,
    dom=lambda i: range(nMachines) if len(machines[i]) == 0 else machines[i],
)

# makespan
makespan = Var(dom=range(horizon + 1))

satisfy(
    # no overlapping on machines (conditional on same machine)
    [
        If(
            m[i] == m[j],
            Then=either(
                end_time(test_intervals[i]) <= start_time(test_intervals[j]),
                end_time(test_intervals[j]) <= start_time(test_intervals[i]),
            ),
        )
        for i, j in conflicting_tests()
    ],
    # no overlapping on single pre-assigned machines (using SequenceVar)
    [
        SeqNoOverlap(SequenceVar(intervals=[test_intervals[i] for i in t], name=f"machine_group_{idx}"))
        for idx, t in enumerate(tests_by_single_machines)
    ],
    # no overlapping on resources (using SequenceVar)
    [
        SeqNoOverlap(SequenceVar(intervals=[test_intervals[i] for i in t], name=f"resource_group_{idx}"))
        for idx, t in enumerate(tests_by_resources)
    ],
    # cumulative constraint: at most nMachines tests running at any time
    SeqCumulative(
        test_intervals,
        heights=[1] * nTests,
        capacity=nMachines,
    ),
    # makespan
    [makespan >= end_time(test_intervals[i]) for i in range(nTests)],
)

minimize(makespan)

# --- Solution output ---
if __name__ == "__main__":
    if solve() in (SAT, OPTIMUM):
        print(f"Makespan: {value(makespan)}")
        print("\nSchedule:")
        for i in range(nTests):
            v = interval_value(test_intervals[i])
            machine = value(m[i])
            res_list = resources[i] if resources[i] else []
            res_str = f" resources={list(res_list)}" if res_list else ""
            print(f"  Test {i:2d} on M{machine}: [{v.start:4d}, {v.end:4d}){res_str}")
