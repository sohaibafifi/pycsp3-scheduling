# Modeling Guide

This guide provides best practices for modeling scheduling problems with pycsp3-scheduling.

## Model Structure

A well-organized scheduling model follows this structure:

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import (
    IntervalVar, SequenceVar, SeqNoOverlap,
    end_before_start, end_time, interval_value, pulse
)

# 1. Data
# -------
durations = [10, 15, 8, 12]
precedences = [(0, 1), (1, 3), (2, 3)]
resources = [[2, 0], [1, 3], [0, 2], [2, 1]]
capacities = [3, 4]

# 2. Variables
# ------------
tasks = [IntervalVar(size=durations[i], name=f"task{i}") 
         for i in range(len(durations))]

# 3. Constraints
# --------------
# Precedence
satisfy(end_before_start(tasks[p], tasks[s]) for p, s in precedences)

# Resource capacity
for r in range(len(capacities)):
    usage = sum(pulse(tasks[i], resources[i][r]) 
                for i in range(len(tasks)) if resources[i][r] > 0)
    satisfy(usage <= capacities[r])

# 4. Objective
# ------------
minimize(Maximum(end_time(t) for t in tasks))

# 5. Solve & Output
# -----------------
if solve() in (SAT, OPTIMUM):
    for task in tasks:
        result = interval_value(task)
        print(f"{task.name}: [{result['start']}, {result['end']}]")
```

## Naming Conventions

Use meaningful names for variables to help with debugging:

```python
# Good: descriptive names
op_j0_m1 = IntervalVar(size=10, name="job0_op1_machine1")
machine_0 = SequenceVar(intervals=[...], name="machine_0")

# Avoid: generic names
x = IntervalVar(size=10, name="x")
```

## Creating Arrays of Variables

### 1D Arrays

```python
# Using list comprehension
tasks = [IntervalVar(size=durations[i], name=f"task_{i}") 
         for i in range(n_tasks)]

# Using IntervalVarArray
tasks = IntervalVarArray(n_tasks, size_range=10, name="task")
```

### 2D Arrays (Operations)

```python
# Jobs × Operations structure
ops = [[IntervalVar(size=durations[j][o], name=f"job{j}_op{o}")
        for o in range(n_operations)] 
       for j in range(n_jobs)]

# Access: ops[job][operation]
first_op_of_job_0 = ops[0][0]
```

### Dictionaries

```python
# Using IntervalVarDict
tasks = IntervalVarDict(
    keys=["assembly", "painting", "testing"],
    size_range=10,
    name="task"
)

# Access by name
assembly_task = tasks["assembly"]
```

## Constraint Patterns

### Job Shop Pattern

Jobs have operations that must be processed in order on specific machines:

```python
# Precedence within jobs
for j in range(n_jobs):
    satisfy(
        end_before_start(ops[j][o], ops[j][o+1])
        for o in range(n_operations - 1)
    )

# No overlap on machines
for m in range(n_machines):
    machine_ops = [ops[j][o] for j in range(n_jobs) 
                   for o in range(n_operations) 
                   if machine[j][o] == m]
    satisfy(SeqNoOverlap(machine_ops))
```

### Flexible Job Shop Pattern

Operations can be processed on alternative machines:

```python
# For each operation, create alternatives for each capable machine
for j in range(n_jobs):
    for o in range(n_operations):
        main = ops[j][o]  # Main operation interval
        alts = []
        for m in machines_for_op[j][o]:
            alt = IntervalVar(
                size=duration[j][o][m],
                optional=True,
                name=f"job{j}_op{o}_machine{m}"
            )
            alts.append(alt)
            machine_ops[m].append(alt)
        
        satisfy(alternative(main, alts))

# No overlap on each machine
for m in range(n_machines):
    satisfy(SeqNoOverlap(machine_ops[m]))
```

### RCPSP Pattern

Tasks require resources with limited capacity:

```python
# Cumulative resource constraints
for r in range(n_resources):
    resource_usage = sum(
        pulse(tasks[t], demand[t][r])
        for t in range(n_tasks)
        if demand[t][r] > 0
    )
    satisfy(resource_usage <= capacity[r])

# Precedence from project graph
satisfy(
    end_before_start(tasks[pred], tasks[succ])
    for pred, succ in precedence_graph
)
```

### Multi-Mode RCPSP Pattern

Tasks can execute in different modes with different durations/demands:

```python
for t in range(n_tasks):
    modes = []
    for m in range(n_modes[t]):
        mode = IntervalVar(
            size=duration[t][m],
            optional=True,
            name=f"task{t}_mode{m}"
        )
        modes.append(mode)
    
    # Select exactly one mode
    satisfy(alternative(tasks[t], modes))
```

## Working with Optional Intervals

### Counting Present Intervals

```python
from pycsp3_scheduling import presence_of

# Count how many optional tasks are scheduled
n_scheduled = Sum(presence_of(task) for task in optional_tasks)
satisfy(n_scheduled >= min_required)
```

### Conditional Precedence

```python
# If both tasks are present, precedence applies
# If either is absent, constraint is satisfied
satisfy(end_before_start(optional_a, optional_b))
```

## Objective Functions

### Minimize Makespan

```python
makespan = Maximum(end_time(task) for task in tasks)
minimize(makespan)
```

### Minimize Total Completion Time

```python
total_completion = Sum(end_time(task) for task in tasks)
minimize(total_completion)
```

### Minimize Weighted Tardiness

```python
# With due dates and weights
tardiness = Sum(
    weights[i] * Maximum(0, end_time(tasks[i]) - due_dates[i])
    for i in range(n_tasks)
)
minimize(tardiness)
```

### Multi-Objective (Lexicographic)

```python
# Minimize makespan, then total completion time
# Use hierarchical solving
minimize(Maximum(end_time(t) for t in tasks))
# ... solve and fix makespan ...
minimize(Sum(end_time(t) for t in tasks))
```

## Performance Tips

### 1. Reduce Domain Sizes

```python
# Bad: unnecessarily large domains
task = IntervalVar(size=10)  # start/end can be 0 to 2^30

# Good: tight bounds based on problem knowledge
task = IntervalVar(
    start=(0, horizon - 10),
    end=(10, horizon),
    size=10
)
```

### 2. Break Symmetries

```python
# If tasks are interchangeable, order them
for i in range(len(identical_tasks) - 1):
    satisfy(start_time(identical_tasks[i]) <= start_time(identical_tasks[i+1]))
```

### 3. Use Implied Constraints

```python
# Add redundant but helpful constraints
# E.g., lower bound on makespan
min_makespan = sum(durations) // n_machines
satisfy(Maximum(end_time(t) for t in tasks) >= min_makespan)
```

### 4. Structure Sequences Properly

```python
# Create sequences only for intervals on the same resource
# Don't create one big sequence for all intervals
for m in range(n_machines):
    seq = SequenceVar(intervals=ops_on_machine[m], name=f"machine_{m}")
    satisfy(SeqNoOverlap(seq))
```

## Debugging Models

### Print Variable Domains

```python
for task in tasks:
    print(f"{task.name}: start=[{task.start_min}, {task.start_max}], "
          f"size=[{task.size_min}, {task.size_max}]")
```

### Check Feasibility

```python
# Test without optimization first
result = solve()
if result == UNSAT:
    print("Model is infeasible!")
    # Try removing constraints to find the conflict
```

### Validate Solutions

```python
if solve() in (SAT, OPTIMUM):
    # Check precedences
    for p, s in precedences:
        pred_end = interval_value(tasks[p])['end']
        succ_start = interval_value(tasks[s])['start']
        assert pred_end <= succ_start, f"Precedence violated: {p} -> {s}"
    
    # Check resource usage at each time point
    # ...
```

## Common Pitfalls

### 1. Forgetting to Check Solution Status

```python
# Bad
solve()
print(interval_value(task))  # May crash if no solution

# Good
if solve() in (SAT, OPTIMUM):
    print(interval_value(task))
else:
    print("No solution found")
```

### 2. Mixing Expression Types

```python
# Use end_time() for pycsp3 objectives, not end_of()
minimize(Maximum(end_time(t) for t in tasks))  # Correct
# minimize(Maximum(end_of(t) for t in tasks))   # May not work
```

### 3. Ignoring Optional Interval Returns

```python
result = interval_value(optional_task)
if result is None:
    print("Task is absent")
else:
    print(f"Task at {result['start']}")
```

## Summary Checklist

- [ ] Use descriptive names for all variables
- [ ] Set tight bounds on start/end when known
- [ ] Group related constraints together
- [ ] Test feasibility before adding objectives
- [ ] Validate solution correctness after solving
- [ ] Handle both SAT and OPTIMUM return values
- [ ] Check for None when reading optional intervals
