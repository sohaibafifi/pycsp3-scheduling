"""
Balanced Academic Curriculum Problem (CSPLib prob030) with period intervals.

Each course is represented by a unit interval assigned to one period.
Prerequisites are expressed with end-before-start on course intervals.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    start_time,
    end_before_start,
)

assert not subvariant() or subvariant("d")

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data" / "prob030" / "10.json"
nCourses, nPeriods, (minCredits, maxCredits), (minCourses, maxCourses), credits, prerequisites = data or load_json_data(str(DEFAULT_DATA))

if subvariant("d"):
    maxCredits = maxCredits * maxCourses

C, P = range(nCourses), range(nPeriods)

course_intervals = [
    IntervalVar(start=(0, nPeriods - 1), size=1, name=f"course_{c}")
    for c in C
]

# Number of courses and credits in each period.
co = VarArray(size=nPeriods, dom=range(minCourses, maxCourses + 1))
cr = VarArray(size=nPeriods, dom=range(minCredits, maxCredits + 1))

satisfy(
    [
        co[p] == Sum(start_time(course_intervals[c]) == p for c in C)
        for p in P
    ],
    [
        cr[p] == Sum(credits[c] * (start_time(course_intervals[c]) == p) for c in C)
        for p in P
    ],
    [
        end_before_start(course_intervals[c2], course_intervals[c1])
        for (c1, c2) in prerequisites
    ],
)

if subvariant("d"):
    minimize(Maximum(cr) - Minimum(cr))
else:
    minimize(Maximum(cr))
