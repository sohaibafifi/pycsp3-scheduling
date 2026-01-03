"""
Flow Shop Scheduling Problem

In a flow shop, all jobs follow the same sequence of machines.
Each job must be processed on machine 0, then machine 1, then machine 2, etc.
The goal is to find the optimal order to process jobs on each machine.
"""
from pycsp3 import *
from pycsp3_scheduling import *

# Data: processing times for each job on each machine
# durations[j][m] = processing time of job j on machine m
durations = [
    [3, 2, 4],  # Job 0: 3 on M0, 2 on M1, 4 on M2
    [2, 4, 3],  # Job 1: 2 on M0, 4 on M1, 3 on M2
    [4, 3, 2],  # Job 2: 4 on M0, 3 on M1, 2 on M2
    [1, 5, 2],  # Job 3: 1 on M0, 5 on M1, 2 on M2
]

n_jobs = len(durations)
n_machines = len(durations[0])

# Create interval variables for each (job, machine) pair
ops = [[IntervalVar(size=durations[j][m], name=f"job_{j}_machine_{m}")
        for m in range(n_machines)]
       for j in range(n_jobs)]

# Precedence: each job follows machine sequence 0 -> 1 -> 2 -> ...
satisfy(
    end_before_start(ops[j][m], ops[j][m + 1])
    for j in range(n_jobs)
    for m in range(n_machines - 1)
)

# No overlap on each machine (all jobs share the same machine sequence)
sequences = [
    SequenceVar(intervals=[ops[j][m] for j in range(n_jobs)], name=f"machine_{m}")
    for m in range(n_machines)
]
satisfy(SeqNoOverlap(seq) for seq in sequences)

# Minimize makespan (completion time of the last operation)
minimize(Maximum(end_time(ops[j][-1]) for j in range(n_jobs)))

# Solve
if solve() in [SAT, OPTIMUM]:
    print("Solution found!")
    print()
    
    # Print schedule by job
    for j in range(n_jobs):
        print(f"Job {j}: ", end="")
        for m in range(n_machines):
            v = interval_value(ops[j][m])
            print(f"M{m}[{v.start}-{v.end}] ", end="")
        print()
    
    print()
    
    # Print schedule by machine
    for m in range(n_machines):
        print(f"Machine {m}: ", end="")
        # Get job order on this machine
        machine_schedule = [(j, interval_value(ops[j][m])) for j in range(n_jobs)]
        machine_schedule.sort(key=lambda x: x[1].start)
        for j, v in machine_schedule:
            print(f"J{j}[{v.start}-{v.end}] ", end="")
        print()
    
    print()
    print(f"Makespan: {max(interval_value(ops[j][-1]).end for j in range(n_jobs))}")
else:
    print("No solution found")
