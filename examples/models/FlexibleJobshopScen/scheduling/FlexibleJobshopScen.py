"""
Stochastic Assignment and Scheduling (CSPLib prob077) with interval variables.

First-stage decisions select one operation option per task.
Second-stage schedules are scenario-specific and use the same selected options.
"""

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    end_before_start,
    end_time,
    alternative,
    SeqCumulative,
    presence_time,
)

if data is None:
    raise ValueError("Missing input data. Run with -data=<json file>.")

nMachines = data.nMachines
tasks = [list(t) for t in data.tasks]
options = [list(o) for o in data.options]
option_machines = list(data.option_machines)
scenarios = data.scenarios

first_scen = scenarios.first
last_scen = scenarios.last
weights = list(scenarios.weights)
durations = [list(row) for row in scenarios.durations]

assert first_scen == 0 and 0 < last_scen < len(durations)
nScenarios = last_scen + 1
S = range(nScenarios)

nJobs, nTasks, nOptions = len(tasks), len(options), len(option_machines)
J, T, O, M = range(nJobs), range(nTasks), range(nOptions), range(nMachines)

task_for_option = [next(t for t in T if o in options[t]) for o in O]

horizon = [sum(max(durations[s][o] for o in options[t]) for t in T) for s in S]
h_max = max(horizon)

min_durations = [[min(durations[s][o] for o in options[t]) for t in T] for s in S]
max_durations = [[max(durations[s][o] for o in options[t]) for t in T] for s in S]

# main[s][t]: interval for task t in scenario s
main = [
    [
        IntervalVar(
            start=(0, horizon[s]),
            size=(min_durations[s][t], max_durations[s][t]),
            name=f"task_{s}_{t}",
        )
        for t in T
    ]
    for s in S
]

# opt[s][o]: optional interval for operation option o in scenario s
opt = [
    [
        IntervalVar(
            start=(0, horizon[s]),
            size=durations[s][o],
            optional=True,
            name=f"opt_{s}_{o}",
        )
        for o in O
    ]
    for s in S
]

# Scenario makespans.
z = VarArray(size=nScenarios, dom=range(h_max + 1))

satisfy(
    # Precedence inside each job, per scenario.
    [
        end_before_start(main[s][t], main[s][t + 1])
        for s in S
        for j in J
        for t in tasks[j][:-1]
    ],

    # Exactly one option per task, per scenario.
    [
        alternative(main[s][t], [opt[s][o] for o in options[t]])
        for s in S
        for t in T
    ],

    # First-stage decision consistency: same selected options across scenarios.
    [
        presence_time(opt[s][o]) == presence_time(opt[0][o])
        for s in S
        for o in O
        if s > 0
    ],

    # At most one active operation per machine and scenario.
    [
        SeqCumulative(
            [opt[s][o] for o in O if option_machines[o] == m],
            heights=[1 for o in O if option_machines[o] == m],
            capacity=1,
        )
        for s in S
        for m in M
    ],

    # Scenario makespan.
    [
        end_time(main[s][tasks[j][-1]]) <= z[s]
        for s in S
        for j in J
    ],
)

minimize(
    Sum(weights[s] * z[s] for s in S)
)
