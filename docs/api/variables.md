# Variables

This module provides the core variable types for scheduling models.

## Interval Variables

```{eval-rst}
.. module:: pycsp3_scheduling.variables.interval
   :synopsis: Interval variable implementation
```

### IntervalVar

```{eval-rst}
.. autoclass:: pycsp3_scheduling.variables.interval.IntervalVar
   :members:
   :undoc-members:
   :show-inheritance:
```

### IntervalVarArray

```{eval-rst}
.. autofunction:: pycsp3_scheduling.variables.interval.IntervalVarArray
```

### IntervalVarDict

```{eval-rst}
.. autofunction:: pycsp3_scheduling.variables.interval.IntervalVarDict
```

### Constants

```{eval-rst}
.. autodata:: pycsp3_scheduling.variables.interval.INTERVAL_MIN
.. autodata:: pycsp3_scheduling.variables.interval.INTERVAL_MAX
```

## Sequence Variables

```{eval-rst}
.. module:: pycsp3_scheduling.variables.sequence
   :synopsis: Sequence variable implementation
```

### SequenceVar

```{eval-rst}
.. autoclass:: pycsp3_scheduling.variables.sequence.SequenceVar
   :members:
   :undoc-members:
   :show-inheritance:
```

### SequenceVarArray

```{eval-rst}
.. autofunction:: pycsp3_scheduling.variables.sequence.SequenceVarArray
```

## Usage Examples

### Creating Interval Variables

```python
from pycsp3_scheduling import IntervalVar, IntervalVarArray, IntervalVarDict

# Single interval with fixed duration
task = IntervalVar(size=10, name="task1")

# Interval with variable duration
flexible = IntervalVar(size=(5, 20), name="flexible_task")

# Optional interval (can be absent)
optional = IntervalVar(size=10, optional=True, name="optional_task")

# Bounded start and end times
bounded = IntervalVar(
    start=(0, 100),
    end=(10, 200),
    size=10,
    name="bounded_task"
)

# Array of intervals
tasks = IntervalVarArray(5, size_range=10, name="task")

# Dictionary of intervals
named_tasks = IntervalVarDict(
    keys=["assembly", "testing", "packaging"],
    size_range=(5, 15),
    name="stage"
)
```

### Creating Sequence Variables

```python
from pycsp3_scheduling import IntervalVar, SequenceVar, SequenceVarArray

# Create tasks
tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

# Simple sequence (no types)
machine = SequenceVar(intervals=tasks, name="machine1")

# Sequence with types for transition constraints
typed_seq = SequenceVar(
    intervals=tasks,
    types=[0, 1, 0],  # Task types
    name="machine_with_types"
)

# Access sequence properties
print(f"Sequence has {len(machine)} intervals")
print(f"Has types: {machine.has_types}")
```

### Accessing Interval Properties

```python
task = IntervalVar(start=(0, 100), size=(5, 15), name="task")

# Bound properties
print(f"Start range: [{task.start_min}, {task.start_max}]")
print(f"End range: [{task.end_min}, {task.end_max}]")
print(f"Size range: [{task.size_min}, {task.size_max}]")

# Status properties
print(f"Is optional: {task.is_optional}")
print(f"Is fixed size: {task.is_fixed_size}")
print(f"Is fixed start: {task.is_fixed_start}")
```
