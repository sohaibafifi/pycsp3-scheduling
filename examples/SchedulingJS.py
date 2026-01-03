from pycsp3 import *
from pycsp3_scheduling import *

# Data
n_jobs, n_machines = 3, 3
durations = [[3, 2, 2], [2, 1, 4], [4, 3, 3]]
machines = [[0, 1, 2], [0, 2, 1], [1, 0, 2]]

# Create interval variables for each operation
ops = [[IntervalVar(size=durations[j][o], name=f"op_{j}_{o}")
        for o in range(n_machines)] for j in range(n_jobs)]

# Sequences for each machine
sequences = [SequenceVar(
    intervals=[ops[j][o] for j in range(n_jobs)
               for o in range(n_machines) if machines[j][o] == m],
    name=f"machine_{m}"
) for m in range(n_machines)]

# Precedence within jobs
satisfy(
    end_before_start(ops[j][o], ops[j][o+1])
    for j in range(n_jobs) for o in range(n_machines-1)
)

# No overlap on machines
satisfy(SeqNoOverlap(seq) for seq in sequences)

# Minimize makespan
minimize(Maximum(end_time(ops[j][-1]) for j in range(n_jobs)))

result = solve()
if result in [SAT, OPTIMUM]:
    for j in range(n_jobs):
        for o in range(n_machines):
            v = interval_value(ops[j][o])
            print(f"{ops[j][o].name}: start={v.start}, end={v.end}")
    for m in range(n_machines):
        print(f"Sequence on machine {m}: {sequences[m]}")
else: 
    print("Result: ", result)
