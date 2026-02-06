# Benchmark Automation Framework

Automated comparison of classical pycsp3 models vs pycsp3-scheduling models.

## Quick Start

```bash
# Quick benchmark (first instance per model)
uv run python benchmarks/runner.py --suite=quick --timeout=60 --repetitions=1

# Full benchmark (all configured instances)
uv run python benchmarks/runner.py --suite=full --timeout=300 --repetitions=1

# One model only
uv run python benchmarks/runner.py --model=MRCPSP --timeout=600

# One model + one instance (useful for per-job execution)
uv run python benchmarks/runner.py --model=MRCPSP --instance=j30-15-05.json --no-report
```

## Directory Structure

```text
benchmarks/
├── config.yaml                  # Model mappings and benchmark settings
├── runner.py                    # Main benchmark runner
├── report.py                    # Report generation from raw results
├── consolidate_results.py       # Merge distributed run outputs + regenerate reports
├── build_manifest.py            # Build model/instance manifest for array jobs
├── download_data.py             # Download/extract benchmark data
├── parse_xcsp3.py               # XCSP3 parser helpers
├── metrics.py                   # Metric dataclasses and comparisons
├── cluster/
│   ├── run_sbatch_array.sh      # Slurm array task entrypoint
│   └── run_oar_array.sh         # OAR array task entrypoint
└── results/                     # Results and generated reports
```

## Data Preparation

```bash
# Extract XCSP ZIP files in PyCSP3-models
uv run python benchmarks/download_data.py --extract-zips

# Download PSPLIB instances (optional)
uv run python benchmarks/download_data.py --psplib

# Sync data files to model directories
uv run python benchmarks/download_data.py --sync

# All-in-one
uv run python benchmarks/download_data.py --all
```

## Running Benchmarks Locally

```bash
# Quick run
uv run python benchmarks/runner.py --suite=quick

# Full run with custom timeout/repetitions
uv run python benchmarks/runner.py --suite=full --timeout=600 --repetitions=3

# Run one model/instance pair
uv run python benchmarks/runner.py \
  --model=FlexibleJobshop \
  --instance=easy01.json \
  --timeout=120 \
  --no-report
```

## Running in Parallel on Slurm/OAR

### 1) Build the manifest

```bash
# Full suite, one repetition
uv run python benchmarks/build_manifest.py \
  --suite=full \
  --repetitions=1 \
  --output=benchmarks/results/jobs/manifest.tsv

# Example: one model, 3 repetitions
uv run python benchmarks/build_manifest.py \
  --suite=full \
  --model=MRCPSP \
  --repetitions=3 \
  --output=benchmarks/results/jobs/manifest.tsv
```

Manifest format is tab-separated: `model<TAB>instance<TAB>repetition_offset`.

### 2) Submit array jobs

```bash
N=$(wc -l < benchmarks/results/jobs/manifest.tsv)
```

Slurm (`sbatch`):

```bash
sbatch \
  --array=1-"${N}" \
  --export=ALL,SUITE=full,RESULTS_ROOT="$PWD/benchmarks/results/jobs" \
  benchmarks/cluster/run_sbatch_array.sh \
  "$PWD/benchmarks/results/jobs/manifest.tsv"
```

OAR (`oarsub`):

```bash
oarsub \
  --array "${N}" \
  --array-param-file "$PWD/benchmarks/results/jobs/manifest.tsv" \
  -l /nodes=1/core=1,walltime=00:20:00 \
  "$PWD/benchmarks/cluster/run_oar_array.sh"
```

Each task writes into its own folder under `benchmarks/results/jobs/`.
(`-S` is for script scanning directives, not for inline commands.)

### 3) Consolidate distributed outputs

```bash
MPLBACKEND=Agg uv run python benchmarks/consolidate_results.py \
  --inputs "benchmarks/results/jobs/*/results_*.json" \
  --output benchmarks/results/results_cluster_merged.json
```

Notes:
- Use `MPLBACKEND=Agg` on headless nodes when generating plots.
- If you intentionally rerun identical `(model, instance, repetition)` rows, add `--no-dedupe`.
- If `TIMEOUT` is not explicitly provided, cluster launchers use `benchmarks/config.yaml`.
- To override timeout from launcher env, set `TIMEOUT=<seconds>` explicitly.

## Report Generation

```bash
# Generate from latest results
uv run python benchmarks/report.py

# Generate from a specific file
uv run python benchmarks/report.py --input=benchmarks/results/results_cluster_merged.json

# Skip plots
uv run python benchmarks/report.py --format=csv --no-plots
```

Reports aggregate **instances per model** (averages). For per-instance detail, use the raw
`results_*.json` files.
Objective columns in `comparison.csv` are averaged costs per model.

## Metrics Collected

| Metric | Classical | Scheduling |
|--------|-----------|------------|
| XCSP3 variables | `<var>/<array>` count | `<var>/<array>` count |
| XCSP3 constraints | XCSP3 constraint count | XCSP3 constraint count |
| Scheduling internals | N/A | interval vars, sequences, cumul/state functions |
| Solve/build/total time | yes | yes |
| Objective snapshot | best known objective/bound | best known objective/bound |
| Status | SAT/OPTIMUM/UNSAT/TIMEOUT/ERROR | SAT/OPTIMUM/UNSAT/TIMEOUT/ERROR |
| LOC | model line count | model line count |

Comparison uses:
- variable/constraint **augmentation** percentages,
- objective snapshot quality on incomplete solves,
- counts of proven optima per approach.

## Output Files

- `benchmarks/results/results_latest.json` - most recent raw run output
- `benchmarks/results/results_*.json` - timestamped raw outputs
- `benchmarks/results/reports/comparison.csv` - full table
- `benchmarks/results/reports/comparison.tex` - LaTeX table
- `benchmarks/results/reports/reduction_summary.tex` - LaTeX summary
- `benchmarks/results/reports/summary.json` - aggregated metrics
- `benchmarks/results/reports/size_comparison.{pdf,png}`
- `benchmarks/results/reports/solve_time_comparison.{pdf,png}`
- `benchmarks/results/reports/solve_time_scatter.{pdf,png}`
- `benchmarks/results/reports/loc_comparison.{pdf,png}`
- `benchmarks/results/reports/objective_avg_comparison.{pdf,png}`
- `benchmarks/results/reports/objective_gap.{pdf,png}`
- `benchmarks/results/reports/objective_snapshot_comparison.{pdf,png}`
- `benchmarks/results/reports/optimality_counts.{pdf,png}`

## Interpretation Checklist

1. If both are `OPTIMUM`, objectives should match.
2. If status is `SAT`/`TIMEOUT`, compare objective snapshot (`Obj_Better`).
3. Compare average objective costs per model (`Classical_Obj_Avg` vs `Scheduling_Obj_Avg`).
4. Compare number of proven `OPTIMUM` statuses per side.
5. Inspect variable/constraint augmentation and solve-time tradeoff.

## Troubleshooting

- Missing model/data: verify paths and instances in `benchmarks/config.yaml`.
- Frequent timeouts: increase `--timeout` or run fewer models/instances.
- Missing plots on cluster/headless machines: set `MPLBACKEND=Agg`.
