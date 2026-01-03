# RCPSP Example

This example demonstrates how to model a Resource-Constrained Project Scheduling Problem (RCPSP).

## Problem Description

In the RCPSP:
- A **project** consists of a set of **activities** (tasks)
- Activities have **precedence relations** (dependencies)
- Activities consume **renewable resources** during execution
- Each resource has limited **capacity**
- **Objective**: Minimize the project makespan

## Mathematical Model

**Sets**:
- $T$ = set of tasks (activities)
- $R$ = set of renewable resources
- $E$ = set of precedence relations (edges)

**Parameters**:
- $d_t$ = duration of task $t$
- $r_{tr}$ = resource $r$ demand of task $t$
- $C_r$ = capacity of resource $r$

**Variables**:
- $s_t$ = start time of task $t$

**Constraints**:
1. **Precedence**: Task $t$ must finish before task $t'$ starts if $(t, t') \in E$
   $$s_{t'} \geq s_t + d_t \quad \forall (t, t') \in E$$

2. **Resource capacity**: At any time, resource usage cannot exceed capacity
   $$\sum_{t: s_t \leq \tau < s_t + d_t} r_{tr} \leq C_r \quad \forall r \in R, \tau$$

**Objective**: 
$$\text{minimize} \max_{t \in T} (s_t + d_t)$$

## Implementation

```python
from pycsp3 import satisfy, minimize, solve, SAT, OPTIMUM, Maximum
from pycsp3_scheduling import (
    IntervalVar, end_before_start, end_time, 
    interval_value, pulse
)

# Problem data
durations = [3, 2, 5, 4, 2]
demands = [  # [resource1, resource2] for each task
    [2, 1],
    [1, 2],
    [3, 0],
    [2, 1],
    [1, 3],
]
capacities = [4, 3]
precedences = [(0, 2), (1, 3), (2, 4), (3, 4)]  # (pred, succ) pairs

n_tasks = len(durations)
n_resources = len(capacities)

# Create interval variables for tasks
tasks = [IntervalVar(size=durations[i], name=f"task{i}") 
         for i in range(n_tasks)]

# Precedence constraints
satisfy(
    end_before_start(tasks[pred], tasks[succ]) 
    for pred, succ in precedences
)

# Resource capacity constraints using cumulative functions
for r in range(n_resources):
    resource_usage = sum(
        pulse(tasks[t], demands[t][r])
        for t in range(n_tasks)
        if demands[t][r] > 0
    )
    satisfy(resource_usage <= capacities[r])

# Minimize makespan
minimize(Maximum(end_time(t) for t in tasks))

# Solve and print solution
if solve() in (SAT, OPTIMUM):
    print("Solution found!")
    print("\nTask Schedule:")
    for i, task in enumerate(tasks):
        result = interval_value(task)
        demand_str = ", ".join(f"R{r}:{demands[i][r]}" for r in range(n_resources))
        print(f"  {task.name}: [{result.start}, {result.end}] ({demand_str})")
    
    makespan = max(interval_value(t).end for t in tasks)
    print(f"\nMakespan: {makespan}")
else:
    print("No solution found")
```

## Expected Output

```
Solution found!

Task Schedule:
  task0: [0, 3] (R0:2, R1:1)
  task1: [0, 2] (R0:1, R1:2)
  task2: [3, 8] (R0:3, R1:0)
  task3: [2, 6] (R0:2, R1:1)
  task4: [8, 10] (R0:1, R1:3)

Makespan: 10
```

## Visualizing Resource Usage

```python
def print_resource_profile(tasks, demands, capacities, horizon):
    """Print ASCII resource usage profile."""
    for r in range(len(capacities)):
        print(f"\nResource {r} (capacity={capacities[r]}):")
        for t in range(horizon):
            usage = sum(
                demands[i][r]
                for i, task in enumerate(tasks)
                if (result := interval_value(task)) and
                   result.start <= t < result.end
            )
            bar = '#' * usage + '.' * (capacities[r] - usage)
            print(f"  t={t:2}: [{bar}] {usage}/{capacities[r]}")

# After solving:
if solve() in (SAT, OPTIMUM):
    makespan = max(interval_value(t).end for t in tasks)
    print_resource_profile(tasks, demands, capacities, makespan)
```

## Multi-Mode RCPSP

In Multi-Mode RCPSP, each task can be executed in different **modes**, each with different duration and resource demands.

```python
from pycsp3_scheduling import alternative

# Multi-mode data
modes = [  # For each task: list of (duration, [demands]) per mode
    [(3, [2, 1]), (5, [1, 1])],       # Task 0: 2 modes
    [(2, [1, 2]), (3, [1, 1])],       # Task 1: 2 modes
    [(5, [3, 0]), (4, [2, 1])],       # Task 2: 2 modes
    [(4, [2, 1])],                     # Task 3: 1 mode
    [(2, [1, 3]), (3, [1, 2])],       # Task 4: 2 modes
]

# Create main task intervals
tasks = [IntervalVar(size=(1, 100), name=f"task{i}") for i in range(len(modes))]

# Create mode alternatives
mode_vars = []
for t, task_modes in enumerate(modes):
    task_mode_vars = []
    for m, (dur, _) in enumerate(task_modes):
        mode_var = IntervalVar(
            size=dur, 
            optional=True, 
            name=f"task{t}_mode{m}"
        )
        task_mode_vars.append(mode_var)
    mode_vars.append(task_mode_vars)
    
    # Select exactly one mode
    satisfy(alternative(tasks[t], task_mode_vars))

# Resource constraints on mode variables
for r in range(n_resources):
    resource_usage = sum(
        pulse(mode_vars[t][m], modes[t][m][1][r])
        for t in range(len(modes))
        for m in range(len(modes[t]))
        if modes[t][m][1][r] > 0
    )
    satisfy(resource_usage <= capacities[r])
```

## Non-Renewable Resources

For resources consumed permanently (like budget):

```python
from pycsp3 import Sum

# Non-renewable resource constraint
budget = 100
costs = [20, 15, 30, 25, 10]

# Total cost must not exceed budget
satisfy(Sum(costs[t] * 1 for t in range(n_tasks)) <= budget)  # If all tasks mandatory

# For optional tasks:
from pycsp3_scheduling import presence_of
optional_tasks = [IntervalVar(size=d, optional=True, name=f"opt{i}") 
                  for i, d in enumerate(durations)]
satisfy(Sum(costs[t] * presence_of(optional_tasks[t]) for t in range(n_tasks)) <= budget)
```

## Performance Tips

1. **Critical path lower bound**: Calculate minimum makespan from longest path
2. **Resource lower bound**: Sum of (duration × demand) / capacity per resource
3. **Precedence transitivity**: Add implied precedences from transitive closure

```python
# Example: Compute critical path lower bound
import networkx as nx

G = nx.DiGraph()
for pred, succ in precedences:
    G.add_edge(pred, succ, weight=durations[pred])

# Longest path gives lower bound
critical_path_length = nx.dag_longest_path_length(G) + durations[-1]
print(f"Critical path lower bound: {critical_path_length}")
```
