# Flexible Job Shop Scheduling Example

This example demonstrates how to model a Flexible Job Shop Scheduling Problem (FJSP).

## Problem Description

The Flexible Job Shop extends the classical Job Shop:
- Each operation can be processed on **multiple alternative machines**
- Different machines may have **different processing times** for the same operation
- **Objective**: Select machines and schedule operations to minimize makespan

## Mathematical Model

**Sets**:
- $J$ = set of jobs
- $M$ = set of machines  
- $O_j$ = ordered operations of job $j$
- $M_{jo}$ = set of machines capable of processing operation $o$ of job $j$

**Parameters**:
- $p_{jom}$ = processing time of operation $o$ of job $j$ on machine $m$

**Variables**:
- $s_{jo}$ = start time of operation $o$ of job $j$
- $x_{jom}$ = 1 if operation $o$ of job $j$ is assigned to machine $m$

**Constraints**:
1. **Assignment**: Each operation assigned to exactly one capable machine
2. **Precedence**: Operations in a job processed in order
3. **No-overlap**: Operations on same machine don't overlap

## Implementation

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import (
    IntervalVar, SequenceVar, SeqNoOverlap,
    alternative, end_before_start, end_time, interval_value
)

# Problem data
# processing_times[job][operation] = {machine: duration}
processing_times = [
    # Job 0
    [{0: 3, 1: 2}, {1: 4, 2: 3}, {0: 2, 2: 4}],
    # Job 1  
    [{0: 2, 2: 5}, {1: 3}, {0: 4, 1: 3, 2: 2}],
    # Job 2
    [{1: 3, 2: 2}, {0: 4, 1: 2}, {2: 3}],
]

n_jobs = len(processing_times)
n_machines = 3

# Create main interval for each operation (machine not yet decided)
ops = []
for j, job in enumerate(processing_times):
    job_ops = []
    for o, machines_dict in enumerate(job):
        # Duration range from min to max across machines
        min_dur = min(machines_dict.values())
        max_dur = max(machines_dict.values())
        op = IntervalVar(size=(min_dur, max_dur), name=f"job{j}_op{o}")
        job_ops.append(op)
    ops.append(job_ops)

# Create optional alternatives for each (operation, machine) pair
alternatives = []  # alternatives[j][o] = list of (machine, interval) pairs
machine_ops = [[] for _ in range(n_machines)]  # Operations assigned to each machine

for j, job in enumerate(processing_times):
    job_alts = []
    for o, machines_dict in enumerate(job):
        op_alts = []
        for m, duration in machines_dict.items():
            alt = IntervalVar(
                size=duration,
                optional=True,
                name=f"job{j}_op{o}_m{m}"
            )
            op_alts.append((m, alt))
            machine_ops[m].append(alt)
        job_alts.append(op_alts)
    alternatives.append(job_alts)

# Alternative constraints: select exactly one machine per operation
for j in range(n_jobs):
    for o in range(len(ops[j])):
        alt_intervals = [alt for _, alt in alternatives[j][o]]
        satisfy(alternative(ops[j][o], alt_intervals))

# Precedence within jobs
for j in range(n_jobs):
    for o in range(len(ops[j]) - 1):
        satisfy(end_before_start(ops[j][o], ops[j][o+1]))

# No-overlap on each machine
for m in range(n_machines):
    if machine_ops[m]:
        satisfy(SeqNoOverlap(machine_ops[m]))

# Minimize makespan
last_ops = [ops[j][-1] for j in range(n_jobs)]
minimize(Maximum(end_time(op) for op in last_ops))

# Solve and print solution
if solve() in (SAT, OPTIMUM):
    print("Solution found!\n")
    
    for j in range(n_jobs):
        print(f"Job {j}:")
        for o in range(len(ops[j])):
            result = interval_value(ops[j][o])
            
            # Find which machine was selected
            selected_machine = None
            for m, alt in alternatives[j][o]:
                alt_result = interval_value(alt)
                if alt_result is not None:
                    selected_machine = m
                    break
            
            print(f"  Op {o}: Machine {selected_machine}, "
                  f"[{result['start']}, {result['end']}]")
    
    makespan = max(interval_value(ops[j][-1])['end'] for j in range(n_jobs))
    print(f"\nMakespan: {makespan}")
    
    # Print machine schedules
    print("\nMachine Schedules:")
    for m in range(n_machines):
        scheduled = []
        for j in range(n_jobs):
            for o in range(len(alternatives[j])):
                for mach, alt in alternatives[j][o]:
                    if mach == m:
                        result = interval_value(alt)
                        if result is not None:
                            scheduled.append((result['start'], j, o, result['end']))
        
        scheduled.sort()
        print(f"  Machine {m}: ", end="")
        for start, j, o, end in scheduled:
            print(f"J{j}O{o}[{start},{end}] ", end="")
        print()
else:
    print("No solution found")
```

## Expected Output

```
Solution found!

Job 0:
  Op 0: Machine 1, [0, 2]
  Op 1: Machine 2, [2, 5]
  Op 2: Machine 0, [5, 7]

Job 1:
  Op 0: Machine 0, [0, 2]
  Op 1: Machine 1, [2, 5]
  Op 2: Machine 2, [5, 7]

Job 2:
  Op 0: Machine 2, [0, 2]
  Op 1: Machine 1, [5, 7]
  Op 2: Machine 2, [7, 10]

Makespan: 10

Machine Schedules:
  Machine 0: J1O0[0,2] J0O2[5,7] 
  Machine 1: J0O0[0,2] J1O1[2,5] J2O1[5,7] 
  Machine 2: J2O0[0,2] J0O1[2,5] J1O2[5,7] J2O2[7,10]
```

## Using Sequence Variables

For better control over machine ordering:

```python
# Create sequence variables for each machine
sequences = []
for m in range(n_machines):
    if machine_ops[m]:
        seq = SequenceVar(intervals=machine_ops[m], name=f"machine{m}")
        sequences.append((m, seq))

# Apply no-overlap to sequences
satisfy(SeqNoOverlap(seq) for _, seq in sequences)
```

## With Setup Times

When setup times depend on job types:

```python
job_types = [0, 1, 0]  # Type of each job

# Setup time matrix: time to switch from type i to type j
setup_matrix = [
    [0, 5, 3],  # From type 0
    [4, 0, 2],  # From type 1
    [3, 4, 0],  # From type 2
]

# Create sequences with types
for m in range(n_machines):
    if machine_ops[m]:
        # Determine types for operations on this machine
        types = []
        for j in range(n_jobs):
            for o, machines_dict in enumerate(processing_times[j]):
                if m in machines_dict:
                    types.append(job_types[j])
        
        seq = SequenceVar(
            intervals=machine_ops[m],
            types=types,
            name=f"machine{m}"
        )
        satisfy(SeqNoOverlap(seq, transition_matrix=setup_matrix))
```

## Partial Flexibility

Some problems have only partial flexibility (not all machines for all operations):

```python
# Example: Operation 0 of Job 0 can only run on machines 0 and 1
processing_times = [
    [{0: 3, 1: 2}, {0: 4, 1: 3, 2: 3}, {2: 4}],  # Job 0
    # ...
]

# The code above handles this automatically through the machines_dict
```

## Performance Tips

1. **Dominant machines**: If one machine is always best for an operation, fix the assignment
2. **Critical operations**: Identify bottleneck machines and operations
3. **Lower bounds**: Use job-based and machine-based lower bounds

```python
# Machine-based lower bound
for m in range(n_machines):
    min_load = sum(
        min(times.get(m, float('inf')) 
            for times in [processing_times[j][o] 
                         for j in range(n_jobs) 
                         for o in range(len(processing_times[j]))
                         if m in processing_times[j][o]])
        for j in range(n_jobs)
        for o in range(len(processing_times[j]))
        if m in processing_times[j][o]
    )
    # This gives a lower bound per machine
```
