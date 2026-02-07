"""
Bus Driver Scheduling (CSPLib prob022) with interval-based shift selection.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, count_present, presence_time

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "c1.json"

nTasks, shifts = data or load_json_data(str(DEFAULT_DATA))

shift_tokens = [
    IntervalVar(start=(i, i), size=1, optional=True, name=f"shift_{i}")
    for i in range(len(shifts))
]

satisfy(
    [
        ExactlyOne(presence_time(shift_tokens[i]) for i, sh in enumerate(shifts) if t in sh)
        for t in range(nTasks)
    ]
)

minimize(count_present(shift_tokens))
