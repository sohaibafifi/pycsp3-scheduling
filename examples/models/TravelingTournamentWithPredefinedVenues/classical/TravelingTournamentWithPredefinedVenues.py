"""
Problem 068 on CSPLib (runtime-compatible formulation).

This uses the stable TTP_PV formulation style for predefined venues.

## Data Example
  circ8bbal.json

## Model
  constraints: AllDifferent, Element, Regular, Sum

## Execution
  python TravelingTournamentWithPredefinedVenues.py
  python TravelingTournamentWithPredefinedVenues.py -data=<datafile.json>

## Links
  - https://www.csplib.org/Problems/prob068/
  - https://www.researchgate.net/publication/220270875_The_Traveling_Tournament_Problem_Description_and_Benchmarks
"""

from pathlib import Path

from pycsp3 import *

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data" / "prob068" / "circ8bbal.json"
nTeams, venues = data or load_json_data(str(DEFAULT_DATA))

assert nTeams % 2 == 0, "an even number of teams is expected"

nRounds = nTeams - 1
R, T = range(nRounds), range(nTeams)

distances = cp_array([min(abs(v1 - v2), nTeams - abs(v1 - v2)) for v2 in T] for v1 in T)


def build_automaton():
    qi, q01, q02, q03, q11, q12, q13 = states = "q", "q01", "q02", "q03", "q11", "q12", "q13"
    t2 = [(qi, 0, q01), (qi, 1, q11), (q01, 0, q02), (q01, 1, q11), (q11, 0, q01), (q11, 1, q12), (q02, 1, q11), (q12, 0, q01)]
    t3 = [(q02, 0, q03), (q12, 1, q13), (q03, 1, q11), (q13, 0, q01)]
    return Automaton(start=qi, final={q for q in states if q != qi}, transitions=t2 + t3)


A = build_automaton()

# opp[i][k] is the opponent (team) of the ith team at round k
opp = VarArray(size=[nTeams, nRounds], dom=range(nTeams))

# h[i][k] is 1 iff the ith team plays at home at round k
h = VarArray(size=[nTeams, nRounds], dom={0, 1})

# t[i][k] is the travelled distance at round k; extra slot for return home
t = VarArray(size=[nTeams, nRounds + 1], dom=range(nTeams // 2 + 1))

satisfy(
    # predefined venues
    [venues[i][opp[i][k]] == h[i][k] for i in T for k in R],

    # a team cannot play itself
    [opp[i][k] != i for i in T for k in R],

    # symmetry of matchups
    [opp[opp[i][k]][k] == i for i in T for k in R],

    # each team plays all other teams once
    [AllDifferent(opp[i]) for i in T],

    # opponents all different each round (redundant)
    [AllDifferent(opp[:, j]) for j in R],

    # at most 3 consecutive home or away games
    [h[i] in A for i in T],

    # symmetry breaking
    opp[0][0] < opp[0][-1],

    # travelled distances for first round
    [
        If(
            h[i][0] == 1,
            Then=t[i][0] == 0,
            Else=t[i][0] == distances[i][opp[i][0]]
        ) for i in T
    ],

    # travelled distances between rounds
    [
        Match(
            (h[i][k], h[i][k + 1]),
            Cases={
                (1, 1): t[i][k + 1] == 0,
                (0, 1): t[i][k + 1] == distances[opp[i][k]][i],
                (1, 0): t[i][k + 1] == distances[i][opp[i][k + 1]],
                (0, 0): t[i][k + 1] == distances[opp[i][k]][opp[i][k + 1]],
            }
        ) for i in T for k in R[:-1]
    ],

    # travelled distances for return home
    [
        If(
            h[i][-1] == 1,
            Then=t[i][-1] == 0,
            Else=t[i][-1] == distances[opp[i][-1]][i]
        ) for i in T
    ],
)

minimize(
    Sum(t)
)
