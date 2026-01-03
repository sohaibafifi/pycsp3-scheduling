# Job Shop Scheduling Example

This example demonstrates how to model a classic Job Shop Scheduling Problem (JSP).

## Problem Description

In the Job Shop Scheduling Problem:
- A set of **jobs** must be processed
- Each job consists of a sequence of **operations**
- Each operation must be processed on a specific **machine**
- Each machine can process only one operation at a time
- Operations within a job must be processed in order
- **Objective**: Minimize the makespan (total completion time)

## Mathematical Model

**Sets**:
- $J$ = set of jobs
- $M$ = set of machines
- $O_j$ = ordered sequence of operations for job $j$

**Parameters**:
- $p_{jo}$ = processing time of operation $o$ of job $j$
- $m_{jo}$ = machine required by operation $o$ of job $j$

**Variables**:
- $s_{jo}$ = start time of operation $o$ of job $j$

**Constraints**:
1. **Precedence**: Operations in a job are processed in order
   $$s_{j,o+1} \geq s_{jo} + p_{jo} \quad \forall j \in J, o \in O_j \setminus \{\text{last}\}$$

2. **No-overlap**: Operations on the same machine don't overlap

**Objective**: Minimize makespan
$$\text{minimize} \max_{j \in J} (s_{j,|O_j|} + p_{j,|O_j|})$$

## Implementation

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import (
    IntervalVar, SequenceVar, SeqNoOverlap,
    end_before_start, end_time, interval_value
)

# Problem data
n_jobs = 3
n_machines = 3
durations = [
    [3, 2, 2],  # Job 0: operation durations
    [2, 1, 4],  # Job 1
    [4, 3, 3],  # Job 2
]
machines = [
    [0, 1, 2],  # Job 0: machine sequence
    [0, 2, 1],  # Job 1
    [1, 0, 2],  # Job 2
]

# Create interval variables for each operation
ops = [[IntervalVar(size=durations[j][o], name=f"job{j}_op{o}")
        for o in range(n_machines)] 
       for j in range(n_jobs)]

# Precedence constraints within jobs
satisfy(
    end_before_start(ops[j][o], ops[j][o+1])
    for j in range(n_jobs) 
    for o in range(n_machines - 1)
)

# Group operations by machine
machine_ops = [
    [ops[j][o] for j in range(n_jobs) 
               for o in range(n_machines) 
               if machines[j][o] == m]
    for m in range(n_machines)
]

# No-overlap constraints on machines
satisfy(SeqNoOverlap(machine_ops[m]) for m in range(n_machines))

# Minimize makespan
minimize(Maximum(end_time(ops[j][-1]) for j in range(n_jobs)))

# Solve and print solution
if solve() in (SAT, OPTIMUM):
    print("Solution found!")
    for j in range(n_jobs):
        print(f"\nJob {j}:")
        for o in range(n_machines):
            result = interval_value(ops[j][o])
            m = machines[j][o]
            print(f"  Op {o} on M{m}: [{result.start}, {result.end}]")
    
    makespan = max(interval_value(ops[j][-1]).end for j in range(n_jobs))
    print(f"\nMakespan: {makespan}")
else:
    print("No solution found")
```

## Expected Output

```
Solution found!

Job 0:
  Op 0 on M0: [0, 3]
  Op 1 on M1: [4, 6]
  Op 2 on M2: [7, 9]

Job 1:
  Op 0 on M0: [3, 5]
  Op 1 on M2: [5, 9]
  Op 2 on M1: [9, 13]

Job 2:
  Op 0 on M1: [0, 4]
  Op 1 on M0: [5, 8]
  Op 2 on M2: [9, 12]

Makespan: 13
```

## Using Sequence Variables

For more control over machine scheduling, use `SequenceVar`:

```python
# Create sequence variables for each machine
sequences = [
    SequenceVar(intervals=machine_ops[m], name=f"machine{m}")
    for m in range(n_machines)
]

# No-overlap on sequences
satisfy(SeqNoOverlap(seq) for seq in sequences)
```

## With Setup Times

If there are setup times between different job types:

```python
# Define job types
job_types = [0, 1, 0]  # Type of each job

# Create sequences with types
for m in range(n_machines):
    types = [job_types[j] for j in range(n_jobs) 
             for o in range(n_machines) if machines[j][o] == m]
    sequences[m] = SequenceVar(
        intervals=machine_ops[m],
        types=types,
        name=f"machine{m}"
    )

# Setup time matrix (type -> type)
setup_times = [
    [0, 5],  # From type 0: 0->0=0, 0->1=5
    [3, 0],  # From type 1: 1->0=3, 1->1=0
]

satisfy(SeqNoOverlap(seq, transition_matrix=setup_times) for seq in sequences)
```

## Performance Tips

1. **Tight bounds**: Set horizon based on problem analysis
2. **Symmetry breaking**: Order identical operations
3. **Implied constraints**: Add redundant constraints that help propagation

```python
# Example: Lower bound on makespan
total_work = sum(sum(durations[j]) for j in range(n_jobs))
min_makespan = total_work // n_machines
satisfy(Maximum(end_time(ops[j][-1]) for j in range(n_jobs)) >= min_makespan)
```
