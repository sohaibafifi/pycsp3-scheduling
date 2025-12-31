from pycsp3 import *
from pycsp3_scheduling import *

# Data
durations = [3, 2, 5, 4, 2]
demands = [[2, 1], [1, 2], [3, 0], [2, 1], [1, 3]]
capacities = [4, 3]
precedences = [(0, 2), (1, 3), (2, 4)]

# Interval variables
tasks = [IntervalVar(size=durations[i], name=f"task_{i}")
         for i in range(len(durations))]

# Get start variables for solution extraction
starts = [start_time(t) for t in tasks]

# Precedence constraints
satisfy(end_before_start(tasks[p], tasks[s]) for p, s in precedences)

# Cumulative resource constraints
for r in range(len(capacities)):
    resource = sum(pulse(tasks[i], demands[i][r])
                   for i in range(len(tasks)) if demands[i][r] > 0)
    satisfy(resource <= capacities[r])

# Minimize makespan
minimize(Maximum(end_time(t) for t in tasks))

if solve() in [SAT, OPTIMUM]:
    for i, t in enumerate(tasks):
        s = value(starts[i])
        e = s + durations[i]
        print(f"{t.name}: start={s}, end={e}")
else:
    print("No solution found")