"""
Traveling Tournament with predefined venues (CSPLib prob068) with interval-based travel legs.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, end_time

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "circ8bbal.json"

nTeams, venues = data or load_json_data(str(DEFAULT_DATA))
assert nTeams % 2 == 0

nRounds = nTeams - 1
R, T = range(nRounds), range(nTeams)
distances = cp_array([min(abs(a - b), nTeams - abs(a - b)) for b in T] for a in T)


def build_automaton():
    qi, q01, q02, q03, q11, q12, q13 = states = "q", "q01", "q02", "q03", "q11", "q12", "q13"
    t2 = [(qi, 0, q01), (qi, 1, q11), (q01, 0, q02), (q01, 1, q11), (q11, 0, q01), (q11, 1, q12), (q02, 1, q11), (q12, 0, q01)]
    t3 = [(q02, 0, q03), (q12, 1, q13), (q03, 1, q11), (q13, 0, q01)]
    return Automaton(start=qi, final={q for q in states if q != qi}, transitions=t2 + t3)


A = build_automaton()

opp = VarArray(size=[nTeams, nRounds], dom=range(nTeams))
h = VarArray(size=[nTeams, nRounds], dom={0, 1})
t = VarArray(size=[nTeams, nRounds + 1], dom=range(nTeams // 2 + 1))

legs = [
    [IntervalVar(start=(0, 0), size=(0, nTeams // 2), name=f"leg_{i}_{k}") for k in range(nRounds + 1)]
    for i in T
]

satisfy(
    [venues[i][opp[i][k]] == h[i][k] for i in T for k in R],
    [opp[i][k] != i for i in T for k in R],
    [opp[opp[i][k]][k] == i for i in T for k in R],
    [AllDifferent(opp[i]) for i in T],
    [AllDifferent(opp[:, k]) for k in R],
    [h[i] in A for i in T],
    opp[0][0] < opp[0][-1],

    [If(h[i][0] == 1, Then=t[i][0] == 0, Else=t[i][0] == distances[i][opp[i][0]]) for i in T],

    [
        Match(
            (h[i][k], h[i][k + 1]),
            Cases={
                (1, 1): t[i][k + 1] == 0,
                (0, 1): t[i][k + 1] == distances[opp[i][k]][i],
                (1, 0): t[i][k + 1] == distances[i][opp[i][k + 1]],
                (0, 0): t[i][k + 1] == distances[opp[i][k]][opp[i][k + 1]],
            },
        )
        for i in T
        for k in R[:-1]
    ],

    [If(h[i][-1] == 1, Then=t[i][-1] == 0, Else=t[i][-1] == distances[opp[i][-1]][i]) for i in T],

    [end_time(legs[i][k]) == t[i][k] for i in T for k in range(nRounds + 1)],
)

minimize(Sum(end_time(legs[i][k]) for i in T for k in range(nRounds + 1)))
