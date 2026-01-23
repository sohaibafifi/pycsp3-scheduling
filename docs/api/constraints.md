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

## Forbidden Time Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.forbidden
   :synopsis: Forbidden time constraints
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.forbidden.forbid_start
.. autofunction:: pycsp3_scheduling.constraints.forbidden.forbid_end
.. autofunction:: pycsp3_scheduling.constraints.forbidden.forbid_extent
```

## Presence Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.presence
   :synopsis: Presence implication constraints
```

### Binary Presence Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.presence.presence_implies
.. autofunction:: pycsp3_scheduling.constraints.presence.presence_or
.. autofunction:: pycsp3_scheduling.constraints.presence.presence_xor
```

### Group Presence Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.presence.all_present_or_all_absent
.. autofunction:: pycsp3_scheduling.constraints.presence.presence_or_all
.. autofunction:: pycsp3_scheduling.constraints.presence.if_present_then
```

### Cardinality Constraints

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.presence.at_least_k_present
.. autofunction:: pycsp3_scheduling.constraints.presence.at_most_k_present
.. autofunction:: pycsp3_scheduling.constraints.presence.exactly_k_present
```

## Chain Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.chain
   :synopsis: Chain constraints for sequential execution
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.chain.chain
.. autofunction:: pycsp3_scheduling.constraints.chain.strict_chain
```

## Overlap Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.overlap
   :synopsis: Overlap and disjunctive constraints
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.overlap.must_overlap
.. autofunction:: pycsp3_scheduling.constraints.overlap.overlap_at_least
.. autofunction:: pycsp3_scheduling.constraints.overlap.no_overlap_pairwise
.. autofunction:: pycsp3_scheduling.constraints.overlap.disjunctive
```

## Bounds Constraints

```{eval-rst}
.. module:: pycsp3_scheduling.constraints.bounds
   :synopsis: Bounds constraints for interval variables
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.constraints.bounds.release_date
.. autofunction:: pycsp3_scheduling.constraints.bounds.deadline
.. autofunction:: pycsp3_scheduling.constraints.bounds.time_window
```

## State Helpers

```{eval-rst}
.. autofunction:: pycsp3_scheduling.functions.state_functions.requires_state
.. autofunction:: pycsp3_scheduling.functions.state_functions.sets_state
```

## Aggregate Expressions

```{eval-rst}
.. module:: pycsp3_scheduling.expressions.aggregate
   :synopsis: Aggregate expressions for interval collections
```

```{eval-rst}
.. autofunction:: pycsp3_scheduling.expressions.aggregate.count_present
.. autofunction:: pycsp3_scheduling.expressions.aggregate.earliest_start
.. autofunction:: pycsp3_scheduling.expressions.aggregate.latest_end
.. autofunction:: pycsp3_scheduling.expressions.aggregate.span_length
.. autofunction:: pycsp3_scheduling.expressions.aggregate.makespan
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

### Forbidden Time Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, forbid_start, forbid_end, forbid_extent

task = IntervalVar(size=10, name="task")

# Cannot start during lunch break (12-13) or after hours (17-24)
satisfy(forbid_start(task, [(12, 13), (17, 24)]))

# Cannot end during maintenance window (6-8)
satisfy(forbid_end(task, [(6, 8)]))

# Cannot overlap the lunch break at all
satisfy(forbid_extent(task, [(12, 13)]))
```

### Presence Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import (
    IntervalVar, presence_implies, presence_or, presence_xor,
    all_present_or_all_absent, at_least_k_present, exactly_k_present
)

# Setup must run if main task runs
setup = IntervalVar(size=5, optional=True, name="setup")
main = IntervalVar(size=20, optional=True, name="main")
satisfy(presence_implies(main, setup))

# At least one delivery method must be chosen
delivery_a = IntervalVar(size=30, optional=True, name="delivery_a")
delivery_b = IntervalVar(size=45, optional=True, name="delivery_b")
satisfy(presence_or(delivery_a, delivery_b))

# Exactly one route must be taken
route_a = IntervalVar(size=30, optional=True, name="route_a")
route_b = IntervalVar(size=45, optional=True, name="route_b")
satisfy(presence_xor(route_a, route_b))

# All subtasks must run together or not at all
subtasks = [IntervalVar(size=5, optional=True, name=f"sub_{i}") for i in range(3)]
satisfy(all_present_or_all_absent(subtasks))

# At least 3 of 5 tasks must be completed
tasks = [IntervalVar(size=10, optional=True, name=f"t_{i}") for i in range(5)]
satisfy(at_least_k_present(tasks, 3))

# Exactly 2 workers must be assigned
workers = [IntervalVar(size=480, optional=True, name=f"w_{i}") for i in range(4)]
satisfy(exactly_k_present(workers, 2))
```

### Chain Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import IntervalVar, chain, strict_chain

# Assembly line: steps must execute in order
steps = [IntervalVar(size=d, name=f"step_{i}") for i, d in enumerate([5, 10, 3, 8])]
satisfy(chain(steps))

# With minimum gap of 2 between each step
satisfy(chain(steps, delays=2))

# With variable gaps between steps
satisfy(chain(steps, delays=[1, 2, 3]))

# Back-to-back execution (no gaps)
satisfy(strict_chain(steps))
```

### Overlap Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import (
    IntervalVar, must_overlap, overlap_at_least,
    no_overlap_pairwise, disjunctive
)

# Two intervals must overlap
meeting = IntervalVar(size=60, name="meeting")
availability = IntervalVar(size=480, name="available")
satisfy(must_overlap(meeting, availability))

# Shifts must overlap by at least 30 minutes for handoff
mentor_shift = IntervalVar(size=120, name="mentor")
trainee_shift = IntervalVar(size=120, name="trainee")
satisfy(overlap_at_least(mentor_shift, trainee_shift, 30))

# Simple pairwise no-overlap (without sequence variable)
meetings = [IntervalVar(size=30, name=f"meeting_{i}") for i in range(5)]
satisfy(no_overlap_pairwise(meetings))

# Disjunctive resource (unary - only one task at a time)
tasks = [IntervalVar(size=d, name=f"task_{i}") for i, d in enumerate([10, 15, 8])]
satisfy(disjunctive(tasks))

# Disjunctive with transition times between types
transition = [[0, 5], [3, 0]]
satisfy(disjunctive(tasks, transition_times=transition))
```

### Bounds Constraints

```python
from pycsp3 import satisfy
from pycsp3_scheduling import (
    IntervalVar, release_date, deadline, time_window
)

task = IntervalVar(size=30, name="delivery")

# Task cannot start before 9am (time 540 in minutes)
satisfy(release_date(task, 540))

# Task must complete by 5pm (time 1020 in minutes)
satisfy(deadline(task, 1020))

# Combined: task must execute within business hours
satisfy(time_window(task, earliest_start=540, latest_end=1020))

# Works with optional intervals too
optional_task = IntervalVar(size=30, optional=True, name="optional_delivery")
satisfy(time_window(optional_task, earliest_start=540, latest_end=1020))

# Operator syntax (shorthand) - more concise!
satisfy(task >= 540)           # same as release_date(task, 540)
satisfy(task <= 1020)          # same as deadline(task, 1020)
satisfy(task > 500)            # start strictly after 500
satisfy(task < 1100)           # end strictly before 1100

# Works great in list comprehensions
tasks = [IntervalVar(size=30, name=f"task_{i}") for i in range(5)]
satisfy(t >= 0 for t in tasks)      # all tasks start at or after 0
satisfy(t <= 1000 for t in tasks)   # all tasks end by time 1000
```

### State Helpers

```python
from pycsp3 import satisfy
from pycsp3_scheduling import (
    IntervalVar, StateFunction, requires_state, sets_state
)

# Create a state function for oven temperature
oven = StateFunction(name="oven_temp")

# Baking task requires oven at temperature state 2
bake = IntervalVar(size=30, name="bake")
satisfy(requires_state(bake, oven, 2))

# Preheat task transitions oven from cold (0) to hot (2)
preheat = IntervalVar(size=15, name="preheat")
satisfy(sets_state(preheat, oven, before_state=0, after_state=2))

# Cooldown task transitions oven from any state to cold
cooldown = IntervalVar(size=20, name="cooldown")
satisfy(sets_state(cooldown, oven, before_state=None, after_state=0))
```

### Aggregate Expressions

```python
from pycsp3 import satisfy, minimize, maximize
from pycsp3_scheduling import (
    IntervalVar, count_present, earliest_start, latest_end,
    span_length, makespan
)

tasks = [IntervalVar(size=10, optional=True, name=f"t_{i}") for i in range(10)]

# Must complete at least 5 tasks
satisfy(count_present(tasks) >= 5)

# Maximize number of completed tasks
maximize(count_present(tasks))

# All tasks must start after time 10
satisfy(earliest_start(tasks) >= 10)

# All tasks must end before time 100
satisfy(latest_end(tasks) <= 100)

# Minimize makespan (latest end time)
minimize(makespan(tasks))

# Minimize total span
minimize(span_length(tasks))
```
