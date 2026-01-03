"""
Open Shop Scheduling Problem

In an open shop, each job must be processed once on each machine,
but the order of machines for each job is not fixed (unlike flow shop).
Each operation has a given processing time.
"""
from pycsp3 import *
from pycsp3_scheduling import *

# Data: processing times for each job on each machine
# durations[j][m] = processing time of job j on machine m
durations = [
    [3, 2, 4],  # Job 0
    [2, 3, 1],  # Job 1
    [4, 2, 3],  # Job 2
]

n_jobs = len(durations)
n_machines = len(durations[0])

# Create interval variables for each (job, machine) pair
ops = [[IntervalVar(size=durations[j][m], name=f"job_{j}_machine_{m}")
        for m in range(n_machines)]
       for j in range(n_jobs)]

# No overlap constraint 1: Each machine can process only one job at a time
machine_sequences = [
    SequenceVar(intervals=[ops[j][m] for j in range(n_jobs)], name=f"machine_{m}")
    for m in range(n_machines)
]
satisfy(SeqNoOverlap(seq) for seq in machine_sequences)

# No overlap constraint 2: Each job can be on only one machine at a time
job_sequences = [
    SequenceVar(intervals=[ops[j][m] for m in range(n_machines)], name=f"job_{j}")
    for j in range(n_jobs)
]
satisfy(SeqNoOverlap(seq) for seq in job_sequences)

# Minimize makespan
minimize(Maximum(end_time(ops[j][m]) for j in range(n_jobs) for m in range(n_machines)))

# Solve
if solve() in [SAT, OPTIMUM]:
    print("Solution found!")
    print()
    
    # Print schedule by job
    for j in range(n_jobs):
        print(f"Job {j}:")
        # Get operation order for this job
        job_ops = [(m, interval_value(ops[j][m])) for m in range(n_machines)]
        job_ops.sort(key=lambda x: x[1].start)
        for m, v in job_ops:
            print(f"  Machine {m}: [{v.start}-{v.end}]")
    
    print()
    
    # Print schedule by machine
    for m in range(n_machines):
        print(f"Machine {m}: ", end="")
        machine_ops = [(j, interval_value(ops[j][m])) for j in range(n_jobs)]
        machine_ops.sort(key=lambda x: x[1].start)
        for j, v in machine_ops:
            print(f"J{j}[{v.start}-{v.end}] ", end="")
        print()
    
    print()
    makespan = max(interval_value(ops[j][m]).end
                   for j in range(n_jobs) for m in range(n_machines))
    print(f"Makespan: {makespan}")
else:
    print("No solution found")
