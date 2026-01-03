# Scheduling Concepts

This guide explains the core concepts used in constraint-based scheduling with pycsp3-scheduling.

## Interval Variables

An **interval variable** represents a task or activity in a schedule. It has:

- **Start time**: When the task begins
- **End time**: When the task completes
- **Size/Duration**: How long the task takes
- **Presence**: Whether the task is scheduled (for optional tasks)

```python
from pycsp3_scheduling import IntervalVar

# Fixed duration task
task = IntervalVar(size=10, name="task")

# Variable duration task
flexible = IntervalVar(size=(5, 15), name="flexible")

# Task with bounded start time
bounded = IntervalVar(start=(0, 100), size=10, name="bounded")

# Optional task
optional = IntervalVar(size=10, optional=True, name="optional")
```

### Interval Properties

| Property | Description |
|----------|-------------|
| `start` | Start time bounds as `(min, max)` tuple |
| `end` | End time bounds as `(min, max)` tuple |
| `size` | Duration bounds as `(min, max)` tuple |
| `length` | Length bounds as `(min, max)` tuple |
| `intensity` | Stepwise intensity function as `(x, value)` pairs |
| `granularity` | Scale for the intensity function |
| `optional` | Whether the task can be absent |
| `name` | Identifier for the task |

### Accessing Bounds

```python
task = IntervalVar(start=(0, 100), size=(5, 15), name="task")

print(task.start_min, task.start_max)  # 0, 100
print(task.size_min, task.size_max)    # 5, 15
print(task.is_fixed_size)              # False
print(task.is_optional)                # False
```

### Intensity Functions

Intensity functions relate size to length for intervals. A stepwise function is
a special case of a piecewise linear function where all slopes are 0 and the
domain and image are integer. Steps are expressed as a list of `(x, value)` pairs
specifying that the function value is `value` after `x`, up to the next step.
The default value is 0 up to the first step. To change this default value, set
the first step to `(INTERVAL_MIN, value)`. Consecutive steps with the same value
are merged so the function is represented with the minimal number of steps.

The fundamental equation relating size, length, and intensity is:

```
size x granularity = sum of intensity(t) for t in [start, start + length)
```

> **Important:** When using intensity, you should explicitly set `length` bounds.
> At lower intensity values, more elapsed time (length) is needed to complete
> the same amount of work (size). For example, at 50% intensity, a task with
> `size=10` needs `length=20`. If `length` is not set, it defaults to `size`,
> which may be too restrictive and cause infeasible schedules.

```python
from pycsp3_scheduling import IntervalVar, INTERVAL_MIN

# Intensity: 100% until t=5, 80% until t=10, then 60%
intensity = [(INTERVAL_MIN, 100), (5, 80), (10, 60)]

# Set explicit length bounds to allow longer durations at low intensity
task = IntervalVar(
    size=10,
    length=(10, 25),  # Allow length up to 25 for lower intensity periods
    intensity=intensity,
    granularity=100,
    name="task"
)
```

## Sequence Variables

A **sequence variable** represents an ordered sequence of intervals, typically used for modeling a disjunctive resource (a resource that can only process one task at a time).

```python
from pycsp3_scheduling import SequenceVar

# Tasks assigned to a machine
tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]
machine = SequenceVar(intervals=tasks, name="machine")
```

### Sequences with Types

When tasks have different types (e.g., product types), you can specify types for transition constraints:

```python
# Tasks with types for setup time calculations
machine = SequenceVar(
    intervals=tasks,
    types=[0, 1, 0],  # Task types
    name="machine"
)
```

## Precedence Constraints

Precedence constraints define temporal relationships between tasks.

### Before Constraints (Inequalities)

| Constraint | Meaning |
|------------|---------|
| `end_before_start(a, b, delay)` | Task `a` ends before task `b` starts (+ delay) |
| `start_before_start(a, b, delay)` | Task `b` cannot start before task `a` starts |
| `end_before_end(a, b, delay)` | Task `b` cannot end before task `a` ends |
| `start_before_end(a, b, delay)` | Task `b` cannot end before task `a` starts |

```python
from pycsp3_scheduling import end_before_start

# task1 must complete before task2 starts
satisfy(end_before_start(task1, task2))

# task1 must complete at least 5 time units before task2 starts
satisfy(end_before_start(task1, task2, delay=5))
```

### At Constraints (Equalities)

| Constraint | Meaning |
|------------|---------|
| `end_at_start(a, b, delay)` | Task `a` ends exactly when task `b` starts |
| `start_at_start(a, b, delay)` | Tasks start at the same time |
| `end_at_end(a, b, delay)` | Tasks end at the same time |
| `start_at_end(a, b, delay)` | Task `b` starts exactly when task `a` ends |

```python
from pycsp3_scheduling import start_at_start, end_at_end

# task1 and task2 must start together
satisfy(start_at_start(task1, task2))

# task1 and task2 must end together
satisfy(end_at_end(task1, task2))
```

## No-Overlap Constraints

The **SeqNoOverlap** constraint ensures that tasks in a sequence do not overlap in time:

```python
from pycsp3_scheduling import SeqNoOverlap

# Tasks cannot execute simultaneously
satisfy(SeqNoOverlap(tasks))

# With transition times between task types
transition_matrix = [
    [0, 5, 10],  # From type 0: 0→0=0, 0→1=5, 0→2=10
    [5, 0, 3],   # From type 1
    [10, 3, 0],  # From type 2
]
satisfy(SeqNoOverlap(machine, transition_matrix=transition_matrix))
```

## Grouping Constraints

### Span

The **span** constraint makes a main interval span over all present sub-intervals:

```python
from pycsp3_scheduling import span

project = IntervalVar(size=(0, 1000), name="project")
phases = [IntervalVar(size=s, name=f"phase{i}") for i, s in enumerate([10, 15, 20])]

# Project spans from first phase start to last phase end
satisfy(span(project, phases))
```

### Alternative

The **alternative** constraint selects exactly one (or k) alternatives:

```python
from pycsp3_scheduling import alternative

main = IntervalVar(size=10, name="main")
alts = [IntervalVar(size=10, optional=True, name=f"alt{i}") for i in range(3)]

# Exactly one alternative must be selected and match main
satisfy(alternative(main, alts))

# Select exactly 2 alternatives
satisfy(alternative(main, alts, cardinality=2))
```

### Synchronize

The **synchronize** constraint synchronizes intervals to a main interval:

```python
from pycsp3_scheduling import synchronize

main = IntervalVar(size=10, name="main")
synced = [IntervalVar(size=10, name=f"s{i}") for i in range(3)]

# All synced intervals start and end with main
satisfy(synchronize(main, synced))
```

## Cumulative Functions

Cumulative functions model resource consumption over time.

### Pulse

A **pulse** represents constant resource consumption during a task:

```python
from pycsp3_scheduling import pulse, CumulFunction

tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]
demands = [2, 3, 1]

# Total resource usage
resource = sum(pulse(tasks[i], demands[i]) for i in range(3))

# Capacity constraint
satisfy(resource <= 4)
```

### Step Functions

Step functions represent permanent changes at specific times:

```python
from pycsp3_scheduling import step_at, step_at_start, step_at_end

# Increase level by 5 at time 10
step_at(10, 5)

# Increase at task start, decrease at task end (reservoir model)
reservoir = step_at_start(task, 3) + step_at_end(task, -3)
```

## State Functions

State functions model resources with discrete states and transitions.

```python
from pycsp3_scheduling import StateFunction, TransitionMatrix, always_equal

# Define valid transitions between states
transitions = TransitionMatrix([
    [0, 5, 10],   # From state 0
    [5, 0, 3],    # From state 1
    [10, 3, 0],   # From state 2
])

machine_mode = StateFunction(name="machine_mode", transitions=transitions)

# Task requires machine in state 1
satisfy(always_equal(machine_mode, task, 1))
```

## Interop with pycsp3

To use interval values in pycsp3 expressions and objectives:

```python
from pycsp3_scheduling import start_time, end_time, interval_value

# Get pycsp3 variables for use in expressions
start_var = start_time(task)  # pycsp3 variable
end_expr = end_time(task)     # pycsp3 expression

# After solving, extract results
result = interval_value(task)
print(f"start={result.start}, end={result.end}")
```

You can also inspect model and solution statistics:

```python
from pycsp3_scheduling import model_statistics, solution_statistics

print(model_statistics())
print(solution_statistics())
```

Call `solution_statistics()` only after a successful solve.

## Optional Intervals Semantics

When intervals are optional:

1. **Present**: Task is scheduled with valid start/end times
2. **Absent**: Task is not scheduled (skipped)

Constraints involving absent intervals are **trivially satisfied**:

```python
task_a = IntervalVar(size=10, optional=True, name="a")
task_b = IntervalVar(size=10, name="b")

# If task_a is absent, this constraint is satisfied
# If task_a is present, task_a must end before task_b starts
satisfy(end_before_start(task_a, task_b))
```

## Summary

| Concept | Class/Function | Purpose |
|---------|---------------|---------|
| Task | `IntervalVar` | Represent schedulable activities |
| Machine | `SequenceVar` | Ordered tasks on disjunctive resource |
| Precedence | `end_before_start`, etc. | Temporal relationships |
| No-overlap | `SeqNoOverlap` | Disjunctive resource constraint |
| Grouping | `span`, `alternative`, `synchronize` | Task hierarchies |
| Resources | `pulse`, `CumulFunction` | Cumulative resource usage |
| States | `StateFunction` | Discrete resource modes |
