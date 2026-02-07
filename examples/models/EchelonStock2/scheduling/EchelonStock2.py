"""
Echelon Stock problem (CSPLib prob040) with interval-based setup decisions.
"""

from pathlib import Path
from functools import reduce
from math import floor, gcd

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, SeqNoOverlap, SequenceVar, presence_time

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "A01.json"

children, hcosts, pcosts, demands = data or load_json_data(str(DEFAULT_DATA))

n, nPeriods, nLeaves = len(children), len(demands[0]), len(demands)

factor = reduce(gcd, {v for row in demands for v in row})
demands = [[row[t] // factor for t in range(nPeriods)] for row in demands]
hcosts = [hcosts[i] * factor for i in range(n)]

sum_dmds, all_dmds = [], []
for i in range(n):
    if i < nLeaves:
        sum_dmds.append(sum(demands[i]))
        all_dmds.append([sum(demands[i][t:]) for t in range(nPeriods)])
    else:
        sum_dmds.append(sum(sum_dmds[j] for j in children[i]))
        all_dmds.append([sum(all_dmds[j][t] for j in children[i]) for t in range(nPeriods)])


def ratio1(i, coeff=1):
    parent = next(j for j in range(n) if i in children[j])
    return floor(pcosts[i] // (coeff * (hcosts[i] - hcosts[parent])))


def ratio2(i, t_inf):
    return min(sum(demands[i][t_inf: t_sup + 1]) + ratio1(i, t_sup - t_inf + 1) for t_sup in range(t_inf, nPeriods))


def domain_x(i, t):
    return range(min(all_dmds[i][t], ratio2(i, t)) + 1) if i < nLeaves else range(all_dmds[i][t] + 1)


def domain_y(i, t):
    if t == nPeriods - 1:
        return {0}
    return range(min(all_dmds[i][t + 1], ratio1(i)) + 1) if i < n - 1 else range(all_dmds[i][t + 1] + 1)


x = VarArray(size=[n, nPeriods], dom=domain_x)
y = VarArray(size=[n, nPeriods], dom=domain_y)

setups = [
    [IntervalVar(start=(t, t), size=1, optional=True, name=f"setup_{i}_{t}") for t in range(nPeriods)]
    for i in range(n)
]
setup_seqs = [SequenceVar(intervals=setups[i], name=f"setup_seq_{i}") for i in range(n)]

satisfy(
    [presence_time(setups[i][t]) == (x[i][t] > 0) for i in range(n) for t in range(nPeriods)],
    [SeqNoOverlap(setup_seqs[i]) for i in range(n)],

    [y[i][0] == x[i][0] - demands[i][0] for i in range(nLeaves)],
    [y[i][t] == x[i][t] + y[i][t - 1] - demands[i][t] for i in range(nLeaves) for t in range(1, nPeriods)],

    [y[i][0] == x[i][0] - Sum(x[j][0] for j in children[i]) for i in range(nLeaves, n)],
    [y[i][t] == x[i][t] + y[i][t - 1] - Sum(x[j][t] for j in children[i]) for i in range(nLeaves, n) for t in range(1, nPeriods)],

    [(x[i][t] == 0) | disjunction(x[j][t] > 0 for j in children[i]) for i in range(nLeaves, n) for t in range(nPeriods)],
    [(y[i][t - 1] == 0) | (x[i][t] == 0) for i in range(n) for t in range(1, nPeriods)],

    [Sum(x[i]) == sum_dmds[i] for i in range(n)],
    [y[i][t - 1] + Sum(x[i][t:]) == all_dmds[i][t] for i in range(nLeaves) for t in range(1, nPeriods)],
)

minimize(
    Sum(hcosts[i] * y[i][t] for i in range(n) for t in range(nPeriods))
    + Sum(pcosts[i] * presence_time(setups[i][t]) for i in range(n) for t in range(nPeriods))
)
