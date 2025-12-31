"""
Employee Scheduling Problem

A simplified employee scheduling problem where:
- Multiple employees with different skills
- Tasks require specific skills and have time windows
- Each employee can only work on one task at a time
- Some tasks require specific employees (optional intervals + alternative)
"""
from pycsp3 import *
from pycsp3_scheduling import *

# Data
# Employees with their skills (skill -> list of employee indices)
employees = ["Alice", "Bob", "Carol"]
skills = {
    "coding": [0, 1],      # Alice and Bob can code
    "testing": [1, 2],     # Bob and Carol can test
    "documentation": [0, 2],  # Alice and Carol can document
}

# Tasks: (name, duration, required_skill, earliest_start, deadline)
tasks_data = [
    ("code_module_A", 4, "coding", 0, 10),
    ("code_module_B", 3, "coding", 0, 12),
    ("test_module_A", 2, "testing", 4, 15),  # Must start after some coding done
    ("test_module_B", 2, "testing", 3, 15),
    ("write_docs", 3, "documentation", 0, 15),
]

n_tasks = len(tasks_data)
n_employees = len(employees)

# Create main interval variables for tasks
tasks = [IntervalVar(
    start=(tasks_data[t][3], tasks_data[t][4] - tasks_data[t][1]),
    size=tasks_data[t][1],
    name=tasks_data[t][0]
) for t in range(n_tasks)]

# Create alternative variables for each task-employee combination
# Only employees with the required skill can do the task
task_assignments = []
for t in range(n_tasks):
    task_name, duration, skill, earliest, deadline = tasks_data[t]
    eligible = skills[skill]
    alts = [
        IntervalVar(
            start=(earliest, deadline - duration),
            size=duration,
            optional=True,
            name=f"{task_name}_by_{employees[e]}"
        )
        for e in eligible
    ]
    task_assignments.append((eligible, alts))

# Each task must be assigned to exactly one eligible employee
satisfy(
    alternative(tasks[t], task_assignments[t][1])
    for t in range(n_tasks)
)

# Each employee can only work on one task at a time
for e in range(n_employees):
    employee_tasks = []
    for t in range(n_tasks):
        eligible, alts = task_assignments[t]
        if e in eligible:
            idx = eligible.index(e)
            employee_tasks.append(alts[idx])
    if len(employee_tasks) > 1:
        seq = SequenceVar(intervals=employee_tasks, name=f"employee_{employees[e]}")
        satisfy(SeqNoOverlap(seq))

# Precedence: testing must start after corresponding coding is done
satisfy(end_before_start(tasks[0], tasks[2]))  # test_module_A after code_module_A
satisfy(end_before_start(tasks[1], tasks[3]))  # test_module_B after code_module_B

# Minimize makespan
minimize(Maximum(end_time(t) for t in tasks))

# Solve
if solve() in [SAT, OPTIMUM]:
    print("Solution found!")
    print()
    
    # Print assignments
    for t in range(n_tasks):
        task_name = tasks_data[t][0]
        eligible, alts = task_assignments[t]
        for i, e in enumerate(eligible):
            v = interval_value(alts[i])
            if v is not None:  # This employee was assigned
                print(f"{task_name}: {employees[e]} [{v['start']}-{v['end']}]")
                break
    
    print()
    
    # Print schedule by employee
    for e in range(n_employees):
        print(f"{employees[e]}'s schedule: ", end="")
        schedule = []
        for t in range(n_tasks):
            eligible, alts = task_assignments[t]
            if e in eligible:
                idx = eligible.index(e)
                v = interval_value(alts[idx])
                if v is not None:
                    schedule.append((v['start'], tasks_data[t][0], v['end']))
        schedule.sort()
        for s, name, end in schedule:
            print(f"{name}[{s}-{end}] ", end="")
        if not schedule:
            print("(no tasks)", end="")
        print()
    
    print()
    # Calculate makespan
    makespan = max(interval_value(t)['end'] for t in tasks)
    print(f"Makespan: {makespan}")
else:
    print("No solution found")
