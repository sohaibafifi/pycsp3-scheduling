"""
Balanced Nursing Workload (CSPLib prob069) with interval-based nurse workloads.
"""

from pathlib import Path

from pycsp3 import *
from pycsp3_scheduling import IntervalVar, end_time

DEFAULT_DATA = Path(__file__).resolve().parents[1] / "data" / "2zones1.json"

nNurses, minPatientsPerNurse, maxPatientsPerNurse, maxWorkloadPerNurse, demandsPerZone = data or load_json_data(str(DEFAULT_DATA))

Patient = namedtuple("Patient", ["zone", "demand"])
patients = [Patient(z, d) for z, row in enumerate(demandsPerZone) for d in row]
nPatients, nZones = len(patients), len(demandsPerZone)

lb = sum(sorted(p.demand for p in patients)[:minPatientsPerNurse])

x = VarArray(size=nPatients, dom=range(nNurses))
w = VarArray(size=nNurses, dom=range(lb, maxWorkloadPerNurse + 1))

zone_load = [
    [IntervalVar(start=(0, 0), size=(0, maxWorkloadPerNurse), name=f"n{k}_z{z}") for z in range(nZones)]
    for k in range(nNurses)
]
patients_in_zone = [[i for i, p in enumerate(patients) if p.zone == z] for z in range(nZones)]

satisfy(
    Cardinality(within=x, occurrences={k: range(minPatientsPerNurse, maxPatientsPerNurse + 1) for k in range(nNurses)}),

    [x[i] != x[j] for i, j in combinations(nPatients, 2) if patients[i].zone != patients[j].zone],

    [
        end_time(zone_load[k][z]) == Sum(patients[i].demand * (x[i] == k) for i in patients_in_zone[z])
        for k in range(nNurses)
        for z in range(nZones)
    ],
    [w[k] == Sum(end_time(zone_load[k][z]) for z in range(nZones)) for k in range(nNurses)],

    [x[z] == z for z in range(nZones)],
    Increasing(w),
)

minimize(w * w)
