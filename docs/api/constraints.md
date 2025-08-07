# Constraints

Scheduling constraints for interval and sequence variables.

## Precedence Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.precedence
   :synopsis: Precedence constraints
```

### Before Constraints (Inequalities)

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.precedence.end_before_start
.. autofunction:: pycsp3_scheduling.constraints.precedence.start_before_start
.. autofunction:: pycsp3_scheduling.constraints.precedence.end_before_end
.. autofunction:: pycsp3_scheduling.constraints.precedence.start_before_end
```

### At Constraints (Equalities)

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.precedence.start_at_start
.. autofunction:: pycsp3_scheduling.constraints.precedence.start_at_end
.. autofunction:: pycsp3_scheduling.constraints.precedence.end_at_start
.. autofunction:: pycsp3_scheduling.constraints.precedence.end_at_end
```

## Grouping Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.grouping
   :synopsis: Grouping constraints
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.grouping.span
.. autofunction:: pycsp3_scheduling.constraints.grouping.alternative
.. autofunction:: pycsp3_scheduling.constraints.grouping.synchronize
```

## Sequence Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.sequence
   :synopsis: Sequence constraints
```

### No-Overlap

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.sequence.SeqNoOverlap
```

### Ordering Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.sequence.first
.. autofunction:: pycsp3_scheduling.constraints.sequence.last
.. autofunction:: pycsp3_scheduling.constraints.sequence.before
.. autofunction:: pycsp3_scheduling.constraints.sequence.previous
```

### Consistency Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.sequence.same_sequence
.. autofunction:: pycsp3_scheduling.constraints.sequence.same_common_subsequence
```

## Constraint Reference

### Precedence Constraint Semantics

| Constraint | Semantics (when both present) |
|------------|------------------------------|
| `end_before_start(a, b, delay=0)` | `start(b) >= end(a) + delay` |
| `start_before_start(a, b, delay=0)` | `start(b) >= start(a) + delay` |
| `end_before_end(a, b, delay=0)` | `end(b) >= end(a) + delay` |
| `start_before_end(a, b, delay=0)` | `end(b) >= start(a) + delay` |
| `start_at_start(a, b, delay=0)` | `start(b) == start(a) + delay` |
| `start_at_end(a, b, delay=0)` | `start(b) == end(a) + delay` |
| `end_at_start(a, b, delay=0)` | `end(a) == start(b) + delay` |
| `end_at_end(a, b, delay=0)` | `end(b) == end(a) + delay` |

### Optional Interval Behavior

When one or both intervals are optional:
- If either interval is **absent**, the constraint is **trivially satisfied**
- If both intervals are **present**, the constraint is **enforced**

## Usage Examples

### Precedence Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, end_before_start, start_at_start

task1 = IntervalVar(size=10, name="task1")
task2 = IntervalVar(size=15, name="task2")

# task1 must complete before task2 starts
satisfy(end_before_start(task1, task2))

# task1 must complete at least 5 time units before task2 starts
satisfy(end_before_start(task1, task2, delay=5))

# task1 and task2 must start at the same time
satisfy(start_at_start(task1, task2))
```

### No-Overlap Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, SequenceVar, SeqNoOverlap

tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

# Simple no-overlap
satisfy(SeqNoOverlap(tasks))

# With sequence variable and transition matrix
seq = SequenceVar(intervals=tasks, types=[0, 1, 0], name="machine")
transition_matrix = [
    [0, 5],   # From type 0: 0→0=0, 0→1=5
    [3, 0],   # From type 1: 1→0=3, 1→1=0
]
satisfy(SeqNoOverlap(seq, transition_matrix=transition_matrix))
```

### Grouping Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, span, alternative, synchronize

# Span: main interval covers all sub-intervals
project = IntervalVar(size=(0, 1000), name="project")
phases = [IntervalVar(size=s, name=f"phase{i}") for i, s in enumerate([10, 15, 20])]
satisfy(span(project, phases))

# Alternative: select exactly one alternative
main = IntervalVar(size=10, name="main")
alts = [IntervalVar(size=10, optional=True, name=f"alt{i}") for i in range(3)]
satisfy(alternative(main, alts))

# Synchronize: all intervals align with main
leader = IntervalVar(size=10, name="leader")
followers = [IntervalVar(size=10, name=f"f{i}") for i in range(2)]
satisfy(synchronize(leader, followers))
```

### Sequence Ordering

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, SequenceVar, first, last, before, previous

tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(4)]
seq = SequenceVar(intervals=tasks, name="machine")

# task[0] must be first in sequence
satisfy(first(seq, tasks[0]))

# task[3] must be last in sequence
satisfy(last(seq, tasks[3]))

# task[1] must come before task[2] (not necessarily immediately)
satisfy(before(seq, tasks[1], tasks[2]))

# task[1] must immediately precede task[2]
satisfy(previous(seq, tasks[1], tasks[2]))
```
