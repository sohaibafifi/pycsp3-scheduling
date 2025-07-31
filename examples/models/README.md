# Scheduling Models

This folder contains scheduling models adapted from the [PyCSP3-models](https://github.com/xcsp3team/PyCSP3-models) repository.

## Source

The original models and data files are from:
- **Repository**: https://github.com/xcsp3team/PyCSP3-models
- **Path**: `realistic/` folder

## Adaptations

The models have been adapted to use **pycsp3-scheduling** constructs:

- `IntervalVar` for representing tasks/activities with start, end, and duration
- `SequenceVar` for machine/resource sequences
- Scheduling constraints: `end_before_start`, `SeqNoOverlap`, `SeqCumulative`, `alternative`
- Interop functions: `start_time()`, `end_time()`, `interval_value()`

## Models

| Model | Description | Original |
|-------|-------------|----------|
| SchedulingFS | Flow-shop scheduling | [SchedulingFS](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/SchedulingFS) |
| SchedulingJS | Job-shop scheduling | [SchedulingJS](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/SchedulingJS) |
| SchedulingOS | Open-shop scheduling | [SchedulingOS](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/SchedulingOS) |
| FlexibleJobshop | Flexible job-shop with machine alternatives | [FlexibleJobshop](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/FlexibleJobshop) |
| RCPSP | Resource-Constrained Project Scheduling | [RCPSP](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/RCPSP) |
| MRCPSP | Multi-mode RCPSP | [MRCPSP](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/MRCPSP) |
| CyclicRCPSP | Cyclic RCPSP | [CyclicRCPSP](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/CyclicRCPSP) |
| MSPSP | Multi-Skilled Project Scheduling | [MSPSP](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/MSPSP) |
| AircraftLanding | Aircraft landing scheduling | [AircraftLanding](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/AircraftLanding) |
| TestScheduling | Test scheduling on machines | [TestScheduling](https://github.com/xcsp3team/PyCSP3-models/tree/main/realistic/TestScheduling) |

## Running

Each model can be run directly:

```bash
python SchedulingFS/SchedulingFS.py
python RCPSP/RCPSP.py
```

## License

The original models are part of the PyCSP3-models project, licensed under the [MIT License](https://github.com/xcsp3team/PyCSP3-models/blob/main/LICENSE).
