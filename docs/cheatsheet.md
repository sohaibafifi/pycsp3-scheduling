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
# Important: set explicit length bounds when using intensity!
intensity = [(INTERVAL_MIN, 100), (10, 50)]  # 100% until t=10, then 50%
scaled = IntervalVar(
    size=10,
    length=(10, 25),  # allow larger length for lower intensity
    intensity=intensity,
    granularity=100,
    name="task5"
)
```

This can be seen as in the following diagram:
![IntervalVar](resources/IntervalVar.png)

This curve demonstrates how the physical length (duration) of `scaled` changes depending on when it starts.

- Start $t=0$: The task finishes by $t=10$ (entirely within the 100% zone), so Length = 10.
- Start $t>10$: The task runs entirely in the 50% zone, requiring twice the time to complete the same work. Length = 20.
- Transition: Starting between 0 and 10 results in a mixed duration between 10 and 20.
- The red dashed line shows the user-defined constraint `length=(10, 25)`. The actual physics of the intensity function keep the length well within this bound (maxing out at 20).

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

### Forbidden Time Constraints

```python
satisfy(forbid_start(task, [(12, 13), (17, 24)]))    # cannot start during these periods
satisfy(forbid_end(task, [(6, 8)]))                   # cannot end during this period
satisfy(forbid_extent(task, [(12, 13)]))              # cannot overlap this period
```

### Presence Constraints

```python
satisfy(presence_implies(main, setup))                # if main present, setup must be
satisfy(presence_or(opt_a, opt_b))                    # at least one must be present
satisfy(presence_xor(route_a, route_b))               # exactly one must be present
satisfy(all_present_or_all_absent(subtasks))          # all-or-nothing
satisfy(at_least_k_present(tasks, 3))                 # at least 3 must be present
satisfy(at_most_k_present(tasks, 5))                  # at most 5 can be present
satisfy(exactly_k_present(workers, 2))                # exactly 2 must be present
```

### Chain Constraints

```python
satisfy(chain(steps))                                 # steps execute in order
satisfy(chain(steps, delays=2))                       # with gap of 2 between each
satisfy(chain(steps, delays=[1, 2, 3]))               # variable delays
satisfy(strict_chain(steps))                          # back-to-back (no gaps)
```

### Overlap Constraints

```python
satisfy(must_overlap(a, b))                           # a and b must share some time
satisfy(overlap_at_least(a, b, 30))                   # must overlap by at least 30
satisfy(no_overlap_pairwise(tasks))                   # simple pairwise no-overlap
satisfy(disjunctive(tasks))                           # unary resource (at most one)
satisfy(disjunctive(tasks, transition_times=matrix))  # with transition times
```

### Bounds Constraints

```python
satisfy(release_date(task, 8))                        # cannot start before time 8
satisfy(deadline(task, 50))                           # must finish by time 50
satisfy(time_window(task, earliest_start=8, latest_end=50))  # combined

# Operator syntax (shorthand)
satisfy(task >= 8)                                    # same as release_date(task, 8)
satisfy(task <= 50)                                   # same as deadline(task, 50)
satisfy(task > 5)                                     # start strictly after 5
satisfy(task < 60)                                    # end strictly before 60
satisfy(t >= 0 for t in tasks)                        # all tasks start at or after 0
```

### State Helpers

```python
satisfy(requires_state(task, machine, 2))             # task requires machine in state 2
satisfy(sets_state(preheat, oven, before_state=0, after_state=2))  # transition
satisfy(sets_state(cooldown, oven, before_state=None, after_state=0))  # any -> cold
```

### Aggregate Expressions

```python
satisfy(count_present(tasks) >= 3)                    # at least 3 must be present
satisfy(earliest_start(tasks) >= 10)                  # all start after time 10
satisfy(latest_end(tasks) <= 100)                     # all end before time 100
minimize(makespan(tasks))                             # minimize latest end time
minimize(span_length(tasks))                          # minimize total span
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

### Element Expressions (Array Indexing with Variables)

```python
from pycsp3_scheduling import ElementArray, ElementMatrix

# 1D Array - transparent variable indexing
costs = ElementArray([10, 20, 30, 40, 50])
costs[2]           # → 30 (integer index)
costs[var_index]   # → element expression (variable index)

# 2D Matrix for VRPTW with special boundary values
M = ElementMatrix(
    matrix=travel_times,         # [from][to] distances
    last_value=depot_distances,  # Cost when interval is last
    absent_value=0,              # Cost when interval is absent
)
M[i, j]       # tuple syntax
M[i][j]       # chained syntax (both work with variables)

# Use with next_arg for distance objectives
cost = M[type_i][next_arg(route, interval, M.last_type, M.absent_type)]
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
    print(result.start, result.end, result.length)

    opt_result = interval_value(optional)
    if opt_result is None:
        print("optional task absent")
    else:
        print(opt_result)

    print(model_statistics())
    print(solution_statistics())
```

## 6) Visualizing Schedules

```python
from pycsp3_scheduling import visu
from pycsp3_scheduling.interop import IntervalValue

if visu.is_visu_enabled():
    visu.timeline("Job Shop Schedule", origin=0, horizon=100)

    # Display intervals on machines
    visu.panel("Machine 1")
    visu.interval(IntervalValue(start=0, length=10, name="Job1_Op1"), color=0)
    visu.interval(IntervalValue(start=15, length=15, name="Job2_Op1"), color=1)

    visu.panel("Machine 2")
    visu.interval(IntervalValue(start=10, length=15, name="Job1_Op2"), color=0)
    visu.interval(IntervalValue(start=0, length=12, name="Job2_Op2"), color=1)

    # Display cumulative resource usage
    visu.panel("Workers")
    visu.segment(0, 10, 2)   # 2 workers from t=0 to t=10
    visu.segment(10, 25, 3)  # 3 workers from t=10 to t=25
    visu.segment(25, 30, 1)  # 1 worker from t=25 to t=30

    # Display pauses/maintenance
    visu.panel("Machine 3")
    visu.pause(20, 25, "Maintenance")
    visu.interval(IntervalValue(start=0, length=20, name="Task"), color=2)
    visu.interval(IntervalValue(start=25, length=15, name="Task"), color=2)

    visu.show()
```

### Displaying Solved Variables

```python
# After solving, display interval variables with their values
if solve() in (SAT, OPTIMUM):
    visu.timeline("Solution")

    for machine_id, seq in enumerate(machines):
        visu.panel(f"Machine {machine_id}")
        for task in seq.intervals:
            val = interval_value(task)
            if val is not None:
                visu.interval(val, color=machine_id)

    visu.show()
```
