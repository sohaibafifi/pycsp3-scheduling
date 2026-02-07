# Models Workspace

This folder now uses a unified problem-centric layout that merges former `realistic` and `csplib` content.

## Layout

Each problem is stored as:

```text
examples/models/<Problem>/
  classical/
  scheduling/
  data/
```

- `classical/` contains the selected PyCSP3 classical model.
- `scheduling/` contains the selected pycsp3-scheduling model (when available).
- `data/` contains merged JSON instances from all available sources.

## Manifest

- `examples/models/MANIFEST.csv` is the authoritative inventory.
- It reports, per problem:
  - `problem`
  - `classical_model`
  - `scheduling_model`
  - `data_folder`
  - `source`
  - `missing` (empty if complete; otherwise missing components such as `scheduling`)

## Benchmarks

`benchmarks/config.yaml` is generated from this unified layout and includes only runnable pairs (problems with both classical and scheduling models plus data).
