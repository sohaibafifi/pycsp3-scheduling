"""
Rotating Rostering (CSPLib prob087) with interval-based daily shift assignments.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, presence_time

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "008-2-3.json"

nDaysPerWeek, nWeeks, shift_min, shift_max, requirements = data or load_json_data(str(DEFAULT_DATA))

SATURDAY, SUNDAY = 5, 6
OFF, EARLY, LATE, NIGHT = range(4)
nShifts = 4
nDays = nWeeks * nDaysPerWeek

D, W, S = range(nDays), range(nWeeks), range(nShifts)

assign = [
    [IntervalVar(start=(d, d), size=1, optional=True, name=f"day{d}_s{s}") for s in S]
    for d in D
]

x = VarArray(size=nDays, dom=S)
idx = lambda i: i % nDays

satisfy(
    [ExactlyOne(presence_time(assign[d][s]) for s in S) for d in D],
    [x[d] == Sum(s * presence_time(assign[d][s]) for s in S) for d in D],

    [x[w * nDaysPerWeek + SATURDAY] == x[w * nDaysPerWeek + SUNDAY] for w in W],

    [
        If(x[d] != x[idx(d + 1)], Then=AllEqual([x[idx(d + j)] for j in range(1, shift_min + 1)]))
        for d in D
    ],
    [
        If(AllEqual([x[idx(d + j)] for j in range(shift_max)]), Then=x[d] != x[idx(d + shift_max)])
        for d in D
    ],

    [Sum(x[idx(d + j)] == OFF for j in range(2 * nDaysPerWeek)) >= 2 for d in D],

    [Table(scope=(x[d], x[idx(d + 1)]), conflicts={(LATE, EARLY), (NIGHT, EARLY), (NIGHT, LATE)}) for d in D],

    [
        Sum(presence_time(assign[w * nDaysPerWeek + d][s]) for w in W) == requirements[d][s]
        for d in range(nDaysPerWeek)
        for s in S
    ],
)
