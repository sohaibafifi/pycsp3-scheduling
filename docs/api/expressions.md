# Expressions

Expression functions for extracting values from interval variables.

```{eval-rst}
.. module:: pycsp3_scheduling.expressions.interval_expr
   :synopsis: Interval expression functions
```

## Basic Accessors

### start_of

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.start_of
```

### end_of

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.end_of
```

### size_of

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.size_of
```

### length_of

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.length_of
```

### presence_of

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.presence_of
```

### overlap_length

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.overlap_length
```

## Utility Functions

### expr_min

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.expr_min
```

### expr_max

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.interval_expr.expr_max
```

## IntervalExpr Class

```{eval-rst}
.. autoclass:: pycsp3_scheduling.expressions.interval_expr.IntervalExpr
   :members:
   :undoc-members:
   :show-inheritance:
```

## Sequence Accessor Expressions

These functions access properties of neighboring intervals in a sequence.

### Next Accessors

| Function | Description |
|----------|-------------|
| `start_of_next(seq, iv, last_val, absent_val)` | Start time of next interval |
| `end_of_next(seq, iv, last_val, absent_val)` | End time of next interval |
| `size_of_next(seq, iv, last_val, absent_val)` | Size of next interval |
| `length_of_next(seq, iv, last_val, absent_val)` | Length of next interval |
| `type_of_next(seq, iv, last_val, absent_val)` | Type of next interval |

### Previous Accessors

| Function | Description |
|----------|-------------|
| `start_of_prev(seq, iv, first_val, absent_val)` | Start time of previous interval |
| `end_of_prev(seq, iv, first_val, absent_val)` | End time of previous interval |
| `size_of_prev(seq, iv, first_val, absent_val)` | Size of previous interval |
| `length_of_prev(seq, iv, first_val, absent_val)` | Length of previous interval |
| `type_of_prev(seq, iv, first_val, absent_val)` | Type of previous interval |

## Usage Examples

### Basic Expression Usage

```python
from pycsp3_scheduling import IntervalVar, start_of, end_of, size_of, presence_of

task = IntervalVar(size=(5, 15), optional=True, name="task")

# Get expressions (internal representation)
start_expr = start_of(task)
end_expr = end_of(task)
size_expr = size_of(task)
presence_expr = presence_of(task)

# With absent value for optional intervals
start_expr = start_of(task, absent_value=-1)
```

### Expression Arithmetic

```python
from pycsp3_scheduling import start_of, end_of

task1 = IntervalVar(size=10, name="task1")
task2 = IntervalVar(size=15, name="task2")

# Arithmetic operations
gap = start_of(task2) - end_of(task1)
total_duration = size_of(task1) + size_of(task2)
```

### Comparison Expressions

```python
from pycsp3_scheduling import start_of, end_of

# Build constraint expressions
must_start_early = start_of(task) <= 100
must_end_late = end_of(task) >= 50
```

### Min/Max of Multiple Expressions

```python
from pycsp3_scheduling import expr_min, expr_max, start_of, end_of

tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

# Earliest start
earliest = expr_min(*(start_of(t) for t in tasks))

# Latest end (makespan)
makespan = expr_max(*(end_of(t) for t in tasks))
```
