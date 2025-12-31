# Functions

Cumulative functions and state functions for resource modeling.

## Cumulative Functions

```{eval-rst}
.. module:: pycsp3_scheduling.functions.cumul_functions
   :synopsis: Cumulative function implementation
```

### CumulFunction Class

```{eval-rst}
.. autoclass:: pycsp3_scheduling.functions.cumul_functions.CumulFunction
   :members:
   :undoc-members:
   :show-inheritance:
```

### Elementary Functions

```{eval-rst}
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.pulse
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.step_at
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.step_at_start
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.step_at_end
```

### Cumulative Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.cumul_range
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.always_in
```

### Cumulative Accessors

```{eval-rst}
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.height_at_start
.. autofunction:: pycsp3_scheduling.functions.cumul_functions.height_at_end
```

## State Functions

```{eval-rst}
.. module:: pycsp3_scheduling.functions.state_functions
   :synopsis: State function implementation
```

### StateFunction Class

```{eval-rst}
.. autoclass:: pycsp3_scheduling.functions.state_functions.StateFunction
   :members:
   :undoc-members:
   :show-inheritance:
```

### TransitionMatrix Class

```{eval-rst}
.. autoclass:: pycsp3_scheduling.functions.state_functions.TransitionMatrix
   :members:
   :undoc-members:
   :show-inheritance:
```

### State Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.functions.state_functions.always_equal
.. autofunction:: pycsp3_scheduling.functions.state_functions.always_in
.. autofunction:: pycsp3_scheduling.functions.state_functions.always_constant
.. autofunction:: pycsp3_scheduling.functions.state_functions.always_no_state
```

## Function Reference

### Cumulative Function Types

| Function | Description |
|----------|-------------|
| `pulse(interval, height)` | Rectangular consumption during interval |
| `step_at(time, height)` | Permanent step at fixed time |
| `step_at_start(interval, height)` | Permanent step at interval start |
| `step_at_end(interval, height)` | Permanent step at interval end |

### State Constraint Types

| Constraint | Description |
|------------|-------------|
| `always_equal(func, interval, value)` | State equals value during interval |
| `always_in(func, interval, min, max)` | State in range during interval |
| `always_constant(func, interval)` | State doesn't change during interval |
| `always_no_state(func, interval)` | No state defined during interval |

## Usage Examples

### Cumulative Resource Constraint

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, pulse

# Tasks with resource demands
tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(5)]
demands = [2, 3, 1, 2, 4]
capacity = 5

# Build cumulative function
resource_usage = sum(pulse(tasks[i], demands[i]) for i in range(5))

# Capacity constraint
satisfy(resource_usage <= capacity)
```

### Variable Height Pulse

```python
from pycsp3_scheduling import pulse

# Task with variable resource consumption
task = IntervalVar(size=10, name="task")
p = pulse(task, height_min=1, height_max=5)  # Solver chooses height
```

### Reservoir Model (Step Functions)

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, step_at_start, step_at_end, cumul_range

tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

# Each task acquires resource at start, releases at end
reservoir = sum(
    step_at_start(task, 1) + step_at_end(task, -1)
    for task in tasks
)

# Keep reservoir level between 0 and 2
satisfy(cumul_range(reservoir, 0, 2))
```

### State Function with Transitions

```python
from pycsp3 import satisfy
from pycsp3_scheduling import (
    IntervalVar, StateFunction, TransitionMatrix, always_equal
)

# Define transition times between states
transitions = TransitionMatrix([
    [0, 5, 10],   # From state 0: 0→0=0, 0→1=5, 0→2=10
    [5, 0, 3],    # From state 1
    [10, 3, 0],   # From state 2
])

machine_mode = StateFunction(name="machine_mode", transitions=transitions)

tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]
required_states = [0, 1, 2]

# Each task requires a specific machine state
for task, state in zip(tasks, required_states):
    satisfy(always_equal(machine_mode, task, state))
```

### State Range Constraint

```python
from pycsp3_scheduling import StateFunction, always_in

machine = StateFunction(name="machine")

# Task can execute in states 1, 2, or 3
satisfy(always_in(machine, task, min_value=1, max_value=3))
```

### Constant State During Interval

```python
from pycsp3_scheduling import StateFunction, always_constant

machine = StateFunction(name="machine")

# Machine state cannot change during task execution
satisfy(always_constant(machine, task))
```
