# Cheat Sheet

Many succinct, illustrative examples for specifying data, declaring scheduling variables, posting constraints, building resource models, and solving.



## 1) Declaring Variables

```python
from pycsp3 import *
from pycsp3_scheduling import *
```

### IntervalVar

```python
task = IntervalVar(size=10, name="task1")                       # fixed size
flex = IntervalVar(size=(5, 15), name="task2")                  # variable size
optional = IntervalVar(size=8, optional=True, name="task3")     # optional
bounded = IntervalVar(start=(0, 50), end=(10, 120), size=10, name="task4")

# with intensity function (size differs from length based on efficiency)
intensity = [(INTERVAL_MIN, 100), (10, 50)]  # 100% until t=10, then 50%
scaled = IntervalVar(size=10, intensity=intensity, granularity=100, name="task5")
```

### Arrays and Dictionaries

```python
tasks = [IntervalVar(size=d, name=f"t{i}") for i, d in enumerate(durations)]
tasks = IntervalVarArray(n_tasks, size_range=(5, 15), name="task")
tasks = IntervalVarDict(keys=["cut", "weld", "paint"], size_range=10, name="stage")
```

### SequenceVar

```python
machine = SequenceVar(intervals=tasks, name="machine")
typed_machine = SequenceVar(intervals=tasks, types=[0, 1, 0], name="typed_machine")
```

## 2) Posting Constraints

```python
satisfy(
    end_before_start(t1, t2)  # a single constraint
)

satisfy(
    end_before_start(tasks[i], tasks[i + 1])
    for i in range(n_tasks - 1)  # a generator of constraints
)

satisfy(
    end_before_start(t1, t2),
    [end_before_start(tasks[i], tasks[i + 1]) for i in range(n_tasks - 1)]
)
```

## 3) Building Scheduling Constraints (to be posted)

In the following:
- `t`, `u` are IntervalVar
- `tasks` is a list of IntervalVar
- `seq` is a SequenceVar built from `tasks`

### Precedence

```python
satisfy(end_before_start(t1, t2))              # t1 finishes before t2 starts
satisfy(start_before_start(t1, t2, delay=5))   # t2 starts at least 5 after t1
satisfy(start_at_end(t1, t2))                  # t2 starts exactly at t1 end
```

### Grouping

```python
project = IntervalVar(size=(0, 200), name="project")
phases = [IntervalVar(size=s, name=f"phase{i}") for i, s in enumerate([10, 15, 20])]
satisfy(span(project, phases))

main = IntervalVar(size=10, name="main")
alts = [IntervalVar(size=10, optional=True, name=f"alt{i}") for i in range(3)]
satisfy(alternative(main, alts))               # select one alternative
satisfy(synchronize(main, alts))               # align all to main
```

### No-Overlap and Sequencing

```python
satisfy(SeqNoOverlap(tasks))                   # simple no-overlap

seq = SequenceVar(intervals=tasks, types=[0, 1, 0], name="machine")
transition = [
    [0, 3],
    [2, 0],
]
satisfy(SeqNoOverlap(seq, transition_matrix=transition))

satisfy(first(seq, tasks[0]))
satisfy(last(seq, tasks[-1]))
satisfy(before(seq, tasks[1], tasks[2]))
satisfy(previous(seq, tasks[1], tasks[2]))
```

### Cumulative Resources

```python
demands = [2, 1, 3]
capacity = 4
usage = sum(pulse(tasks[i], demands[i]) for i in range(len(tasks)))
satisfy(usage <= capacity)

reservoir = sum(
    step_at_start(tasks[i], 1) + step_at_end(tasks[i], -1)
    for i in range(len(tasks))
)
satisfy(cumul_range(reservoir, 0, 2))
```

### State Functions

```python
transitions = TransitionMatrix([
    [0, 5, 10],
    [5, 0, 3],
    [10, 3, 0],
])
machine_state = StateFunction(name="machine", transitions=transitions)

satisfy(always_equal(machine_state, tasks[0], 1))
satisfy(always_in(machine_state, tasks[1], 1, 3))
satisfy(always_constant(machine_state, tasks[2]))
```

### Expressions and Interop

```python
gap = start_of(tasks[1]) - end_of(tasks[0])
satisfy(gap >= 2)

opt = IntervalVar(size=8, optional=True, name="opt")
satisfy(start_time(opt) >= 0)
satisfy(end_time(opt) <= 100)
satisfy(presence_time(opt) == 1)
```

## 4) Specifying an Objective

```python
# Minimize makespan
minimize(Maximum(end_time(t) for t in tasks))

# Minimize total tardiness
tardiness = [Maximum(end_time(t) - due[i], 0) for i, t in enumerate(tasks)]
minimize(Sum(tardiness))

# Maximize the number of optional tasks selected
maximize(Sum(presence_time(t) for t in optional_tasks))
```

## 5) Solving and Inspecting Results

```python
if solve() in (SAT, OPTIMUM):
    result = interval_value(task)
    print(result["start"], result["end"], result["length"])

    opt_result = interval_value(optional)
    if opt_result is None:
        print("optional task absent")
    else:
        print(opt_result)
```
