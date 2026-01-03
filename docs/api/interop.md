# Interop

Helper functions for bridging pycsp3-scheduling with pycsp3.

```{eval-rst}
.. module:: pycsp3_scheduling.interop
   :synopsis: pycsp3 interoperability helpers
```

## Functions

### start_time

```{eval-rst}
.. autofunction:: pycsp3_scheduling.interop.start_time
```

### end_time

```{eval-rst}
.. autofunction:: pycsp3_scheduling.interop.end_time
```

### presence_time

```{eval-rst}
.. autofunction:: pycsp3_scheduling.interop.presence_time
```

### interval_value

```{eval-rst}
.. autofunction:: pycsp3_scheduling.interop.interval_value
```

## Classes

### IntervalValue

```{eval-rst}
.. autoclass:: pycsp3_scheduling.interop.IntervalValue
   :members:
```

## Function Reference

| Function | Returns | Description |
|----------|---------|-------------|
| `start_time(interval)` | pycsp3 Variable | Start time variable for pycsp3 constraints |
| `end_time(interval)` | pycsp3 Expression | End time expression (start + length) |
| `presence_time(interval)` | pycsp3 Variable | Presence variable (0/1) for optional intervals |
| `interval_value(interval)` | IntervalValue or None | Solution values after solving |

## Usage Examples

### Using in pycsp3 Constraints

```python
from pycsp3 import satisfy, minimize, Maximum
from pycsp3_scheduling import IntervalVar, start_time, end_time

tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

# Use start_time/end_time in pycsp3 expressions
# Minimize makespan
minimize(Maximum(end_time(task) for task in tasks))

# Custom constraint: all tasks must start before time 100
for task in tasks:
    satisfy(start_time(task) <= 100)
```

### Extracting Solution Values

```python
from pycsp3 import solve, SAT, OPTIMUM
from pycsp3_scheduling import IntervalVar, interval_value

task = IntervalVar(size=10, name="task")
optional_task = IntervalVar(size=10, optional=True, name="optional")

# ... add constraints ...

if solve() in (SAT, OPTIMUM):
    # Regular task
    result = interval_value(task)
    print(f"Task: start={result.start}, end={result.end}, length={result.length}")
    
    # Optional task (may be absent)
    result = interval_value(optional_task)
    if result is None:
        print("Optional task was not scheduled (absent)")
    else:
        print(f"Optional task: start={result.start}, end={result.end}")
```

### Working with Presence Variables

```python
from pycsp3 import satisfy, Sum
from pycsp3_scheduling import IntervalVar, presence_time

optional_tasks = [IntervalVar(size=10, optional=True, name=f"opt{i}") 
                  for i in range(5)]

# At least 3 optional tasks must be scheduled
satisfy(Sum(presence_time(task) for task in optional_tasks) >= 3)

# Two optional tasks must be scheduled together or not at all
task_a, task_b = optional_tasks[0], optional_tasks[1]
satisfy(presence_time(task_a) == presence_time(task_b))
```

### Return Value Format

The `interval_value()` function returns an `IntervalValue` with the following fields:

```python
{
    'start': int,     # Start time of the interval
    'end': int,       # End time of the interval
    'length': int,    # Duration/length of the interval
    'present': bool,  # True if interval is present (always True for non-optional)
}
```

`IntervalValue` supports attribute access (`result.start`) and dict-like access
(`result['start']`) for compatibility.

For optional intervals that are absent, `interval_value()` returns `None`.

## Important Notes

1. **Use `start_time()`/`end_time()` for pycsp3 expressions** (objectives, custom constraints)
2. **Use `start_of()`/`end_of()` for internal IntervalExpr objects** (scheduling expressions)
3. **Always check for `None` when reading optional intervals** with `interval_value()`
4. **Call `interval_value()` only after solving** (after `solve()` returns SAT/OPTIMUM)
