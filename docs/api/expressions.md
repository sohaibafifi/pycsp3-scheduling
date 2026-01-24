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
| `next_arg(seq, iv, last_val, absent_val)` | ID of next interval |

### Previous Accessors

| Function | Description |
|----------|-------------|
| `start_of_prev(seq, iv, first_val, absent_val)` | Start time of previous interval |
| `end_of_prev(seq, iv, first_val, absent_val)` | End time of previous interval |
| `size_of_prev(seq, iv, first_val, absent_val)` | Size of previous interval |
| `length_of_prev(seq, iv, first_val, absent_val)` | Length of previous interval |
| `prev_arg(seq, iv, first_val, absent_val)` | ID of previous interval |

## Element Expressions

```{eval-rst}
.. module:: pycsp3_scheduling.expressions.element
   :synopsis: Element expressions for array indexing
```

### ElementArray

A 1D array wrapper that supports transparent `array[variable]` indexing syntax.

```{eval-rst}
.. autoclass:: pycsp3_scheduling.expressions.element.ElementArray
   :members:
   :undoc-members:
   :show-inheritance:
```

### ElementMatrix

A 2D matrix that supports indexing with pycsp3 expressions, similar to CP Optimizer's `IloNumArray2`.
Supports both `M[i, j]` (tuple) and `M[i][j]` (chained) syntax.

```{eval-rst}
.. autoclass:: pycsp3_scheduling.expressions.element.ElementMatrix
   :members:
   :undoc-members:
   :show-inheritance:
```

### element

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.element.element
```

### element2d

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.element.element2d
```

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

### next_arg for Distance Objectives (VRPTW Pattern)

The `next_arg` function returns the ID of the next interval in a sequence,
enabling CP Optimizer-style distance objectives. Similar to pycsp3's `maximum_arg` pattern:

```python
from pycsp3 import minimize, Sum
from pycsp3_scheduling import IntervalVar, SequenceVar
from pycsp3_scheduling.expressions.sequence_expr import next_arg
from pycsp3_scheduling.expressions.element import ElementMatrix

# Create intervals with IDs (types)
visits = [IntervalVar(size=5, optional=True, name=f"v{i}") for i in range(n)]
route = SequenceVar(intervals=visits, types=list(range(n)), name="route")

# Build cost matrix with boundary values
M = ElementMatrix(
    matrix=travel_costs,           # [from_id][to_id] distances
    last_value=depot_return_costs, # Cost when interval is last
    absent_value=0,                # No cost when interval is absent
)

# Objective: minimize total transition costs
distance_terms = []
for i, visit in enumerate(visits):
    next_id = next_arg(
        route, visit,
        last_value=M.last_type,      # Column index for "last"
        absent_value=M.absent_type,  # Column index for "absent"
    )
    distance_terms.append(M[i, next_id])

minimize(Sum(distance_terms))
```

### ElementMatrix for Transition Costs

```python
from pycsp3_scheduling.expressions.element import ElementMatrix

# Travel distance matrix between customers
travel_costs = [
    [0, 10, 15],   # From customer 0
    [10, 0, 8],    # From customer 1
    [15, 8, 0],    # From customer 2
]

# Return-to-depot distances (per customer)
depot_distances = [20, 18, 22]

# Create matrix with boundary values
M = ElementMatrix(
    matrix=travel_costs,
    last_value=depot_distances,  # When interval is last in sequence
    absent_value=0,              # When interval is not scheduled
)

# Access properties
print(M.n_rows, M.n_cols)  # 3, 3
print(M.last_type)         # 3 (column index for last)
print(M.absent_type)       # 4 (column index for absent)

# Get constant value (debugging)
print(M.get_value(0, 1))        # 10 (travel from 0 to 1)
print(M.get_value(1, M.last_type))  # 18 (return from 1 to depot)

# Use with expressions - both syntaxes work
cost = M[id_i, next_arg(route, interval, M.last_type, M.absent_type)]  # tuple
cost = M[id_i][next_arg(route, interval, M.last_type, M.absent_type)]  # chained
```

### ElementArray for Simple Array Indexing

```python
from pycsp3_scheduling import ElementArray

# Create an array with transparent variable indexing
costs = ElementArray([10, 20, 30, 40, 50])

# Integer indexing - returns value directly
costs[2]  # → 30

# Variable indexing - returns pycsp3 element expression
idx = next_arg(route, interval)
cost = costs[idx]  # Creates element constraint automatically

# Use in objective
minimize(Sum(costs[type_of_next(route, v)] for v in visits))
```
