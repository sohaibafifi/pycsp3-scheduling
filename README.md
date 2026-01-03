# pycsp3-scheduling

Scheduling extension for [pycsp3](https://pycsp.org) with interval variables, sequence variables, and scheduling constraints.

## Features

- **Interval Variables**: Represent tasks/activities with start, end, size, length, and optional presence
- **Intensity Functions**: Stepwise intensity metadata with granularity scaling for size/length
- **Sequence Variables**: Ordered sequences of intervals on disjunctive resources
- **Precedence Constraints**: `end_before_start`, `start_at_start`, etc.
- **Grouping Constraints**: `span`, `alternative`, `synchronize`
- **Cumulative Functions**: `pulse`, `step_at_start`, `step_at_end` for resource modeling
- **State Functions**: Model resource states with transitions
- **XCSP3 Extension**: Output scheduling models in extended XCSP3 format

## Installation

```bash
pip install pycsp3-scheduling
```

For development:

```bash
git clone https://github.com/sohaibafifi/pycsp3-scheduling.git
cd pycsp3-scheduling
pip install -e ".[dev]"
```

## Quick Start

```python
from pycsp3 import *
from pycsp3_scheduling import *

# Create interval variables for tasks
task1 = IntervalVar(size=10, name="task1")
task2 = IntervalVar(size=15, name="task2")
task3 = IntervalVar(size=8, name="task3")

# Precedence: task1 must finish before task2 starts
satisfy(end_before_start(task1, task2))

# No overlap: task2 and task3 cannot overlap
satisfy(SeqNoOverlap([task2, task3]))

# Minimize makespan
minimize(max(end_time(task1), end_time(task2), end_time(task3)))
```

## Example: Job Shop Scheduling

```python
from pycsp3 import *
from pycsp3_scheduling import *

# Data
n_jobs, n_machines = 3, 3
durations = [[3, 2, 2], [2, 1, 4], [4, 3, 3]]
machines = [[0, 1, 2], [0, 2, 1], [1, 0, 2]]

# Create interval variables for each operation
ops = [[IntervalVar(size=durations[j][o], name=f"op_{j}_{o}")
        for o in range(n_machines)] for j in range(n_jobs)]

# Sequences for each machine
sequences = [SequenceVar(
    intervals=[ops[j][o] for j in range(n_jobs)
               for o in range(n_machines) if machines[j][o] == m],
    name=f"machine_{m}"
) for m in range(n_machines)]

# Precedence within jobs
satisfy(
    end_before_start(ops[j][o], ops[j][o+1])
    for j in range(n_jobs) for o in range(n_machines-1)
)

# No overlap on machines
satisfy(SeqNoOverlap(seq) for seq in sequences)

# Minimize makespan
minimize(Maximum(end_time(ops[j][-1]) for j in range(n_jobs)))
```

## Example: RCPSP (Resource-Constrained Project Scheduling)

```python
from pycsp3 import *
from pycsp3_scheduling import *

# Data
durations = [3, 2, 5, 4, 2]
demands = [[2, 1], [1, 2], [3, 0], [2, 1], [1, 3]]
capacities = [4, 3]
precedences = [(0, 2), (1, 3), (2, 4)]

# Interval variables
tasks = [IntervalVar(size=durations[i], name=f"task_{i}")
         for i in range(len(durations))]

# Precedence constraints
satisfy(end_before_start(tasks[p], tasks[s]) for p, s in precedences)

# Cumulative resource constraints
for r in range(len(capacities)):
    resource = sum(pulse(tasks[i], demands[i][r])
                   for i in range(len(tasks)) if demands[i][r] > 0)
    satisfy(resource <= capacities[r])

# Minimize makespan
minimize(Maximum(end_time(t) for t in tasks))
```

## API Reference

### Variables

| Function | Description |
|----------|-------------|
| `IntervalVar(size, start, end, length, intensity, granularity, optional, name)` | Create an interval variable |
| `IntervalVarArray(size, ...)` | Create array of interval variables |
| `SequenceVar(intervals, types, name)` | Create a sequence variable |

### Expressions

| Function | Description |
|----------|-------------|
| `start_of(interval, absent_value=0)` | Start time of interval |
| `end_of(interval, absent_value=0)` | End time of interval |
| `size_of(interval, absent_value=0)` | Size/duration of interval |
| `length_of(interval, absent_value=0)` | Length of interval |
| `presence_of(interval)` | Boolean presence status |

### Interop Helpers

| Function | Description |
|----------|-------------|
| `start_time(interval)` | pycsp3 variable for start time |
| `end_time(interval)` | pycsp3 expression for end time |

### Precedence Constraints

| Constraint | Semantics (when both present) |
|------------|------------------------------|
| `start_before_start(a, b, delay)` | `start(b) >= start(a) + delay` |
| `start_before_end(a, b, delay)` | `end(b) >= start(a) + delay` |
| `end_before_start(a, b, delay)` | `start(b) >= end(a) + delay` |
| `end_before_end(a, b, delay)` | `end(b) >= end(a) + delay` |
| `start_at_start(a, b, delay)` | `start(b) == start(a) + delay` |
| `start_at_end(a, b, delay)` | `start(b) == end(a) + delay` |
| `end_at_start(a, b, delay)` | `end(a) == start(b) + delay` |
| `end_at_end(a, b, delay)` | `end(b) == end(a) + delay` |

### Grouping Constraints

| Constraint | Description |
|------------|-------------|
| `span(main, subtasks)` | Main interval spans all present subtasks |
| `alternative(main, alts, card=1)` | Select `card` alternatives matching main |
| `synchronize(main, intervals)` | All present intervals sync with main |

### Cumulative Functions

| Function | Description |
|----------|-------------|
| `pulse(interval, height)` | Constant consumption during interval |
| `step_at(time, height)` | Step at fixed time point |
| `step_at_start(interval, height)` | Step at interval start |
| `step_at_end(interval, height)` | Step at interval end |
| `cumul_range(cumul, min, max)` | Constrain cumul to [min, max] |

### State Functions

| Function | Description |
|----------|-------------|
| `StateFunction(transition_matrix)` | Create state function |
| `always_in(func, interval, min, max)` | State in range during interval |
| `always_equal(func, interval, value)` | State equals value during interval |
| `always_constant(func, interval)` | State constant during interval |

## Requirements

- Python >= 3.9
- pycsp3 >= 2.5
- lxml >= 4.9

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [PyCSP3 Documentation](https://pycsp.org)
- [XCSP3 Specification](https://xcsp.org/specifications/)
