"""
Flexible Job Shop Scheduling Problem (FJSP)

In the flexible job shop, each operation can be processed on any machine
from a given set of eligible machines (with potentially different durations).

This example models machine selection using optional interval variables.
Each operation has multiple optional intervals (one per eligible machine),
and exactly one must be selected.
"""
from pycsp3 import *
from pycsp3_scheduling import *

# Data: jobs with operations, each operation has (machine, duration) alternatives
# Job format: [[(m1, d1), (m2, d2), ...], ...]  for each operation
jobs_data = [
    # Job 0: 2 operations
    [[(0, 3), (1, 4)],           # op0 can run on machine 0 (3) or machine 1 (4)
     [(1, 2), (2, 3)]],          # op1 can run on machine 1 (2) or machine 2 (3)
    # Job 1: 2 operations  
    [[(0, 2), (2, 4)],           # op0 can run on machine 0 (2) or machine 2 (4)
     [(0, 3), (1, 2)]],          # op1 can run on machine 0 (3) or machine 1 (2)
    # Job 2: 2 operations
    [[(0, 2), (1, 3)],           # op0 can run on machine 0 (2) or machine 1 (3)
     [(1, 2), (2, 4)]],          # op1 can run on machine 1 (2) or machine 2 (4)
]

n_jobs = len(jobs_data)
n_machines = 3

# Create optional interval variables for each (operation, machine) combination
# ops[j][o] = list of optional intervals, one per eligible machine
ops = [[
    [IntervalVar(size=d, optional=True, name=f"j{j}_o{o}_m{m}")
     for m, d in jobs_data[j][o]]
    for o in range(len(jobs_data[j]))]
    for j in range(n_jobs)]

# Store presence and start variables for use in constraints
# (We need these for the Sum and precedence constraints)
presence = [[
    [presence_time(ops[j][o][idx]) for idx in range(len(jobs_data[j][o]))]
    for o in range(len(jobs_data[j]))]
    for j in range(n_jobs)]

starts = [[
    [start_time(ops[j][o][idx]) for idx in range(len(jobs_data[j][o]))]
    for o in range(len(jobs_data[j]))]
    for j in range(n_jobs)]

# Exactly one machine selected per operation
satisfy(
    Sum(presence[j][o]) == 1
    for j in range(n_jobs)
    for o in range(len(jobs_data[j]))
)

# Precedence within jobs: each selected op must finish before next op starts
for j in range(n_jobs):
    for o in range(len(jobs_data[j]) - 1):
        for idx1, (m1, d1) in enumerate(jobs_data[j][o]):
            for idx2, (m2, d2) in enumerate(jobs_data[j][o + 1]):
                # If both are selected, precedence must hold
                satisfy(
                    (presence[j][o][idx1] == 0) | (presence[j][o + 1][idx2] == 0) |
                    (starts[j][o][idx1] + d1 <= starts[j][o + 1][idx2])
                )

# No overlap on each machine
for m in range(n_machines):
    machine_ops = []
    machine_durations = []
    for j in range(n_jobs):
        for o in range(len(jobs_data[j])):
            for idx, (machine, duration) in enumerate(jobs_data[j][o]):
                if machine == m:
                    machine_ops.append(ops[j][o][idx])
                    machine_durations.append(duration)
    if machine_ops:
        seq = SequenceVar(intervals=machine_ops, name=f"machine_{m}")
        satisfy(SeqNoOverlap(seq))

# Minimize makespan: max end time of last operations
last_op_ends = []
for j in range(n_jobs):
    o = len(jobs_data[j]) - 1  # Last operation
    for idx, (m, d) in enumerate(jobs_data[j][o]):
        last_op_ends.append(starts[j][o][idx] + d * presence[j][o][idx])

minimize(Maximum(last_op_ends))

# Solve
if solve() in [SAT, OPTIMUM]:
    print("Solution found!")
    print()
    makespan = 0
    for j in range(n_jobs):
        print(f"Job {j}:")
        for o in range(len(jobs_data[j])):
            for idx, (m, d) in enumerate(jobs_data[j][o]):
                v = interval_value(ops[j][o][idx])
                if v is not None:  # This alternative was selected
                    makespan = max(makespan, v.end)
                    print(f"  Op {o}: machine {m}, [{v.start}-{v.end}]")
                    break
    print()
    print(f"Makespan: {makespan}")
else:
    print("No solution found")
