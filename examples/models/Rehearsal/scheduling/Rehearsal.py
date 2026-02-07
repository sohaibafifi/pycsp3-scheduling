"""
Rehearsal Problem (CSPLib prob039) with interval scheduling.

This reformulation uses one mandatory interval per piece and a single sequence
for the concert order. Player waiting time is computed from the span between
first required piece start and last required piece end.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    SequenceVar,
    SeqNoOverlap,
    start_time,
    end_time,
)

DEFAULT_DATA = Path(__file__).resolve().parents[2] / "data" / "prob039" / "rs.json"
durations, playing = data or load_json_data(str(DEFAULT_DATA))

nPieces, nPlayers = len(durations), len(playing)
horizon = sum(durations)

piece_intervals = [
    IntervalVar(start=(0, horizon), size=durations[j], name=f"piece_{j}")
    for j in range(nPieces)
]
program = SequenceVar(intervals=piece_intervals, name="program")

arrival = VarArray(size=nPlayers, dom=range(horizon + 1))
departure = VarArray(size=nPlayers, dom=range(horizon + 1))

pieces_by_player = [[j for j in range(nPieces) if playing[i][j] == 1] for i in range(nPlayers)]
play_time = [sum(durations[j] for j in pieces_by_player[i]) for i in range(nPlayers)]

satisfy(
    # All pieces are performed in one non-overlapping sequence.
    SeqNoOverlap(program),

    # Arrival/departure time for each player.
    [
        arrival[i] == Minimum(start_time(piece_intervals[j]) for j in pieces_by_player[i])
        for i in range(nPlayers)
        if len(pieces_by_player[i]) > 0
    ],
    [
        departure[i] == Maximum(end_time(piece_intervals[j]) for j in pieces_by_player[i])
        for i in range(nPlayers)
        if len(pieces_by_player[i]) > 0
    ],
    [
        (arrival[i] == 0, departure[i] == 0)
        for i in range(nPlayers)
        if len(pieces_by_player[i]) == 0
    ],
)

minimize(
    Sum(departure[i] - arrival[i] - play_time[i] for i in range(nPlayers))
)
