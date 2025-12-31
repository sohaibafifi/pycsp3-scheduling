# Getting Started

This guide will walk you through creating your first scheduling model with pycsp3-scheduling.

## Your First Scheduling Model

Let's model a simple scheduling problem: scheduling three tasks on a single machine with no overlap.

### Step 1: Import the Libraries

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import (
    IntervalVar,
    SeqNoOverlap,
    end_time,
    interval_value,
)
```

### Step 2: Create Interval Variables

Each task is represented by an `IntervalVar`:

```python
# Three tasks with different durations
task1 = IntervalVar(size=10, name="task1")
task2 = IntervalVar(size=15, name="task2")
task3 = IntervalVar(size=8, name="task3")
```

The `size` parameter specifies the duration. The solver will determine the `start` time.

### Step 3: Add Constraints

Tasks on the same machine cannot overlap:

```python
satisfy(SeqNoOverlap([task1, task2, task3]))
```

### Step 4: Define the Objective

Minimize the makespan (completion time of the last task):

```python
minimize(Maximum(end_time(task1), end_time(task2), end_time(task3)))
```

### Step 5: Solve and Extract Results

```python
if solve() in (SAT, OPTIMUM):
    for task in [task1, task2, task3]:
        result = interval_value(task)
        print(f"{task.name}: start={result['start']}, end={result['end']}")
else:
    print("No solution found")
```

### Complete Example

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import IntervalVar, SeqNoOverlap, end_time, interval_value

# Create tasks
task1 = IntervalVar(size=10, name="task1")
task2 = IntervalVar(size=15, name="task2")
task3 = IntervalVar(size=8, name="task3")

# No overlap constraint
satisfy(SeqNoOverlap([task1, task2, task3]))

# Minimize makespan
minimize(Maximum(end_time(task1), end_time(task2), end_time(task3)))

# Solve
if solve() in (SAT, OPTIMUM):
    for task in [task1, task2, task3]:
        result = interval_value(task)
        print(f"{task.name}: start={result['start']}, end={result['end']}")
```

Expected output:
```
task1: start=0, end=10
task2: start=10, end=25
task3: start=25, end=33
```

## Adding Precedence Constraints

Often tasks have dependencies. Let's say `task1` must finish before `task2` starts:

```python
from pycsp3_scheduling import end_before_start

# task1 → task2 precedence
satisfy(end_before_start(task1, task2))
```

## Working with Variable Durations

Tasks can have flexible durations:

```python
# Task with duration between 5 and 15 time units
flexible_task = IntervalVar(size=(5, 15), name="flexible")
```

## Optional Tasks

Some tasks may be optional (can be skipped):

```python
# Optional task - solver decides if it should be scheduled
optional_task = IntervalVar(size=10, optional=True, name="optional")

# Check if the task was scheduled
result = interval_value(optional_task)
if result is None:
    print("Task was not scheduled (absent)")
else:
    print(f"Task scheduled at: start={result['start']}")
```

## Next Steps

- Learn about [Scheduling Concepts](scheduling_concepts.md) for a deeper understanding
- See [Modeling Guide](modeling_guide.md) for best practices
- Explore full examples in the Examples section
