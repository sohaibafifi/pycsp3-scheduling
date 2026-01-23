# pycsp3-scheduling

Scheduling extension for [pycsp3](https://pycsp.org) with interval variables, sequence variables, and scheduling constraints.

## Features

- **Interval Variables**: Represent tasks/activities with start, end, size, length, and optional presence
- **Intensity Functions**: Stepwise intensity metadata with granularity scaling for size/length
- **Sequence Variables**: Ordered sequences of intervals on disjunctive resources
- **Precedence Constraints**: `end_before_start`, `start_at_start`, etc.
- **Grouping Constraints**: `span`, `alternative`, `synchronize`
- **Sequence Constraints**: `SeqNoOverlap`, `first`, `last`, `before`, `previous`, `same_sequence`
- **Forbidden Time Constraints**: `forbid_start`, `forbid_end`, `forbid_extent`
- **Presence Constraints**: `presence_implies`, `presence_or`, `presence_xor`, `chain`
- **Overlap Constraints**: `must_overlap`, `overlap_at_least`, `disjunctive`
- **Bounds Constraints**: `release_date`, `deadline`, `time_window`
- **Aggregate Expressions**: `count_present`, `earliest_start`, `latest_end`, `makespan`
- **Cumulative Functions**: `pulse`, `step_at_start`, `step_at_end` for resource modeling
- **State Functions**: Model resource states with transitions
- **XCSP3 Extension**: Output scheduling models in extended XCSP3 format
- **Visualization**: Gantt charts and resource profiles

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
| `overlap_length(interval1, interval2, absent_value=0)` | Overlap duration between two intervals |
| `expr_min(*args)` | Minimum of scheduling expressions |
| `expr_max(*args)` | Maximum of scheduling expressions |

### Element Expressions (Array Indexing)

| Function | Description |
|----------|-------------|
| `element(array, index)` | Access array element by interval expression index |
| `element2d(matrix, row, col)` | Access 2D matrix element by interval expressions |
| `ElementMatrix(matrix)` | Wrapper for 2D indexing with `[]` operator |

### Interop Helpers

| Function | Description |
|----------|-------------|
| `start_time(interval)` | pycsp3 variable for start time |
| `end_time(interval)` | pycsp3 expression for end time |
| `presence_time(interval)` | pycsp3 variable for presence (optional intervals) |
| `interval_value(interval)` | Get solved interval values (start, end, size, present) |
| `model_statistics()` | Get model statistics (variables, constraints counts) |
| `solution_statistics()` | Get solution statistics after solving |

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

### Sequence Constraints

| Constraint | Description |
|------------|-------------|
| `SeqNoOverlap(sequence, transition_matrix, is_direct)` | Non-overlap with optional transition times |
| `first(sequence, interval)` | Constrain interval to be first in sequence |
| `last(sequence, interval)` | Constrain interval to be last in sequence |
| `before(sequence, interval1, interval2)` | interval1 must end before interval2 starts |
| `previous(sequence, interval1, interval2)` | interval1 immediately precedes interval2 |
| `same_sequence(seq1, seq2)` | Common intervals have same position in both |
| `same_common_subsequence(seq1, seq2)` | Common intervals have same relative order |

### Sequence Accessor Expressions

| Function | Description |
|----------|-------------|
| `start_of_next(sequence, interval, absent_value)` | Start time of next interval in sequence |
| `end_of_next(sequence, interval, absent_value)` | End time of next interval |
| `size_of_next(sequence, interval, absent_value)` | Size of next interval |
| `length_of_next(sequence, interval, absent_value)` | Length of next interval |
| `type_of_next(sequence, interval, absent_value)` | Type of next interval |
| `start_of_prev(sequence, interval, absent_value)` | Start time of previous interval |
| `end_of_prev(sequence, interval, absent_value)` | End time of previous interval |
| `size_of_prev(sequence, interval, absent_value)` | Size of previous interval |
| `length_of_prev(sequence, interval, absent_value)` | Length of previous interval |
| `type_of_prev(sequence, interval, absent_value)` | Type of previous interval |

### Cumulative Functions

| Function | Description |
|----------|-------------|
| `pulse(interval, height)` | Constant consumption during interval |
| `step_at(time, height)` | Step at fixed time point |
| `step_at_start(interval, height)` | Step at interval start |
| `step_at_end(interval, height)` | Step at interval end |
| `height_at_start(interval, cumul)` | Cumulative height at interval start |
| `height_at_end(interval, cumul)` | Cumulative height at interval end |
| `cumul_range(cumul, min, max)` | Constrain cumul to [min, max] |
| `always_in(cumul, interval, min, max)` | Cumul in range during interval |
| `SeqCumulative(sequence, heights, capacity)` | Cumulative on sequence with per-interval heights |

### State Functions

| Function | Description |
|----------|-------------|
| `StateFunction(transition_matrix)` | Create state function with optional transitions |
| `TransitionMatrix(n_states)` | Create transition matrix for state function |
| `always_equal(func, interval, value)` | State equals value during interval |
| `always_constant(func, interval)` | State constant during interval |
| `always_no_state(func, interval)` | No state assigned during interval |

### Forbidden Time Constraints

| Constraint | Description |
|------------|-------------|
| `forbid_start(interval, periods)` | Interval cannot start during forbidden periods |
| `forbid_end(interval, periods)` | Interval cannot end during forbidden periods |
| `forbid_extent(interval, periods)` | Interval cannot overlap forbidden periods |

### Presence Constraints

| Constraint | Description |
|------------|-------------|
| `presence_implies(a, b)` | If a is present, b must be present |
| `presence_or(a, b)` | At least one must be present |
| `presence_xor(a, b)` | Exactly one must be present |
| `all_present_or_all_absent(intervals)` | All-or-nothing group |
| `if_present_then(interval, constraint)` | Apply constraint only when present |
| `at_least_k_present(intervals, k)` | At least k must be present |
| `at_most_k_present(intervals, k)` | At most k can be present |
| `exactly_k_present(intervals, k)` | Exactly k must be present |

### Chain Constraints

| Constraint | Description |
|------------|-------------|
| `chain(intervals, delays)` | Intervals execute in sequence with optional delays |
| `strict_chain(intervals, delays)` | Intervals execute back-to-back (equality) |

### Overlap Constraints

| Constraint | Description |
|------------|-------------|
| `must_overlap(a, b)` | Two intervals must share some time |
| `overlap_at_least(a, b, min_overlap)` | Intervals must overlap by at least min_overlap |
| `no_overlap_pairwise(intervals)` | Simple pairwise no-overlap |
| `disjunctive(intervals, transition_times)` | Unary resource (at most one active) |

### Bounds Constraints

| Constraint | Description |
|------------|-------------|
| `release_date(interval, time)` | Interval cannot start before given time |
| `deadline(interval, time)` | Interval must complete by given time |
| `time_window(interval, earliest_start, latest_end)` | Combined release + deadline |
| `interval >= time` | Operator shorthand for release_date |
| `interval <= time` | Operator shorthand for deadline |
| `interval > time` | Strict release: `start(interval) > time` |
| `interval < time` | Strict deadline: `end(interval) < time` |

### State Helpers

| Function | Description |
|----------|-------------|
| `requires_state(interval, state_func, state)` | Interval requires specific state (convenience for always_equal) |
| `sets_state(interval, state_func, before, after)` | Interval transitions state from before to after |

### Aggregate Expressions

| Expression | Description |
|------------|-------------|
| `count_present(intervals)` | Count of present intervals |
| `earliest_start(intervals)` | Minimum start time among present intervals |
| `latest_end(intervals)` | Maximum end time among present intervals |
| `span_length(intervals)` | Total span (latest_end - earliest_start) |
| `makespan(intervals)` | Alias for latest_end |

## Requirements

- Python >= 3.10
- pycsp3 >= 2.5
- lxml >= 4.9
- matplotlib >= 3.7 (optional, for visualization)
- java >= 8 (optional, for solving with ACE/Choco)

## License

MIT License - see [LICENSE](LICENSE) file.

## References

- [PyCSP3 Documentation](https://pycsp.org)
- [XCSP3 Specification](https://xcsp.org/specifications/)
