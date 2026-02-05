#!/usr/bin/env python3
"""
Report Generator for benchmark comparison.

Generates CSV, LaTeX, and optional plots from benchmark results.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from metrics import ComparisonResult, RunResult


def _mean(values: list[float]) -> float | None:
    """Return arithmetic mean or None if empty."""
    if not values:
        return None
    return sum(values) / len(values)


def _objective_match_label(match: bool | None) -> str:
    """Map objective match tri-state to report label."""
    if match is True:
        return "Yes"
    if match is False:
        return "No"
    return "N/A"


def _objective_better_label(better: str | None) -> str:
    """Map objective-quality comparison to report label."""
    if better == "classical":
        return "Classical"
    if better == "scheduling":
        return "Scheduling"
    if better == "tie":
        return "Tie"
    return "N/A"


def aggregate_results(results: list[dict]) -> dict[tuple[str, str], dict[str, RunResult]]:
    """
    Aggregate results by (model_name, instance) and model_type.

    For multiple repetitions, averages timing metrics and takes the first
    status/objective.
    """
    # Group by (model, instance, type)
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for r in results:
        key = (r["model_name"], r["instance"], r["model_type"])
        grouped[key].append(r)

    # Average and combine
    by_model: dict[tuple[str, str], dict[str, RunResult]] = defaultdict(dict)
    for (model, instance, model_type), runs in grouped.items():
        runs = sorted(runs, key=lambda r: r.get("repetition", 0))
        # Average timing metrics
        avg_solve_time = sum(r["solve_time"] for r in runs) / len(runs)
        avg_build_time = sum(r["build_time"] for r in runs) / len(runs)
        avg_total_time = sum(r["total_time"] for r in runs) / len(runs)

        # Take first run's non-timing values
        first = runs[0]
        aggregated = RunResult(
            model_type=model_type,
            model_name=model,
            instance=instance,
            status=first["status"],
            objective=first.get("objective"),
            solve_time=avg_solve_time,
            build_time=avg_build_time,
            total_time=avg_total_time,
            n_vars=first.get("n_vars", 0),
            n_constraints=first.get("n_constraints", 0),
            constraint_types=first.get("constraint_types", {}),
            n_interval_vars=first.get("n_interval_vars", 0),
            n_optional_intervals=first.get("n_optional_intervals", 0),
            n_sequences=first.get("n_sequences", 0),
            n_cumul_functions=first.get("n_cumul_functions", 0),
            n_state_functions=first.get("n_state_functions", 0),
            loc=first.get("loc", 0),
            error=first.get("error"),
            timestamp=first.get("timestamp", ""),
            repetition=0,
        )

        by_model[(model, instance)][model_type] = aggregated

    return by_model


def generate_csv_report(
    comparisons: list[ComparisonResult], output_path: Path
) -> None:
    """Generate CSV comparison report."""
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Model",
                "Instance",
                "Classical_Vars",
                "Scheduling_Vars",
                "Var_Augmentation%",
                "Classical_Ctrs",
                "Scheduling_Ctrs",
                "Ctr_Augmentation%",
                "Classical_Time",
                "Scheduling_Time",
                "Speedup",
                "Classical_LOC",
                "Scheduling_LOC",
                "LOC_Reduction%",
                "IntervalVars",
                "Sequences",
                "Classical_Obj",
                "Scheduling_Obj",
                "Obj_Better",
                "Obj_Match",
                "Classical_Status",
                "Scheduling_Status",
            ]
        )

        for c in comparisons:
            writer.writerow(
                [
                    c.model_name,
                    c.instance,
                    c.classical_vars,
                    c.scheduling_vars,
                    f"{c.var_augmentation * 100:.1f}",
                    c.classical_constraints,
                    c.scheduling_constraints,
                    f"{c.constraint_augmentation * 100:.1f}",
                    f"{c.classical_solve_time:.3f}",
                    f"{c.scheduling_solve_time:.3f}",
                    f"{c.solve_speedup:.2f}",
                    c.classical_loc,
                    c.scheduling_loc,
                    f"{c.loc_reduction * 100:.1f}",
                    c.scheduling_interval_vars,
                    c.scheduling_sequences,
                    c.classical_objective if c.classical_objective is not None else "",
                    c.scheduling_objective if c.scheduling_objective is not None else "",
                    _objective_better_label(c.objective_better),
                    _objective_match_label(c.objectives_match),
                    c.classical_status,
                    c.scheduling_status,
                ]
            )


def generate_latex_table(
    comparisons: list[ComparisonResult], output_path: Path
) -> None:
    """Generate LaTeX table for paper."""
    with open(output_path, "w") as f:
        f.write(
            r"""\begin{table}[htbp]
\centering
\caption{Comparison of Classical vs. Scheduling Models}
\label{tab:comparison}
\begin{tabular}{lrrrrrrr}
\toprule
Model & \multicolumn{2}{c}{Variables} & \multicolumn{2}{c}{Constraints} & \multicolumn{2}{c}{Solve Time (s)} & Obj \\
\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7}
 & Classic & Sched & Classic & Sched & Classic & Sched & Match \\
\midrule
"""
        )

        for c in comparisons:
            if c.objectives_match is True:
                match_symbol = r"\checkmark"
            elif c.objectives_match is False:
                match_symbol = r"\texttimes"
            else:
                match_symbol = "--"
            f.write(
                f"{c.model_name} & "
                f"{c.classical_vars} & {c.scheduling_vars} & "
                f"{c.classical_constraints} & {c.scheduling_constraints} & "
                f"{c.classical_solve_time:.2f} & {c.scheduling_solve_time:.2f} & "
                f"{match_symbol} \\\\\n"
            )

        f.write(
            r"""\bottomrule
\end{tabular}
\end{table}
"""
        )

    # Also generate a model-size summary table
    summary_path = output_path.with_name("reduction_summary.tex")
    with open(summary_path, "w") as f:
        f.write(
            r"""\begin{table}[htbp]
\centering
\caption{Model Compactness: Augmentation Percentages}
\label{tab:reduction}
\begin{tabular}{lrrr}
\toprule
Model & Var Augmentation (\%) & Ctr Augmentation (\%) & LOC Reduction (\%) \\
\midrule
"""
        )

        for c in comparisons:
            f.write(
                f"{c.model_name} & "
                f"{c.var_augmentation * 100:.1f} & "
                f"{c.constraint_augmentation * 100:.1f} & "
                f"{c.loc_reduction * 100:.1f} \\\\\n"
            )

        # Average row (only status-comparable pairs)
        valid = [c for c in comparisons if c.statuses_comparable]
        avg_var = _mean([c.var_augmentation for c in valid if c.classical_vars > 0])
        avg_ctr = _mean(
            [c.constraint_augmentation for c in valid if c.classical_constraints > 0]
        )
        avg_loc = _mean([c.loc_reduction for c in valid if c.classical_loc > 0])

        f.write(r"\midrule" + "\n")
        f.write(
            f"\\textbf{{Average}} & "
            f"{(avg_var * 100) if avg_var is not None else 0:.1f} & "
            f"{(avg_ctr * 100) if avg_ctr is not None else 0:.1f} & "
            f"{(avg_loc * 100) if avg_loc is not None else 0:.1f} \\\\\n"
        )

        f.write(
            r"""\bottomrule
\end{tabular}
\end{table}
"""
        )


def generate_summary_json(
    comparisons: list[ComparisonResult], output_path: Path
) -> None:
    """Generate JSON summary with aggregated statistics."""
    status_comparable = [c for c in comparisons if c.statuses_comparable]
    objective_snapshot_comparable = [
        c for c in comparisons if c.objective_snapshot_comparable
    ]
    objective_comparable = [c for c in comparisons if c.objectives_comparable]
    objective_matches = [c for c in objective_comparable if c.objectives_match is True]
    objective_better_classical = [
        c for c in objective_snapshot_comparable if c.objective_better == "classical"
    ]
    objective_better_scheduling = [
        c for c in objective_snapshot_comparable if c.objective_better == "scheduling"
    ]
    objective_better_tie = [
        c for c in objective_snapshot_comparable if c.objective_better == "tie"
    ]
    classical_optimum = [c for c in comparisons if c.classical_status == "OPTIMUM"]
    scheduling_optimum = [c for c in comparisons if c.scheduling_status == "OPTIMUM"]
    both_optimum = [
        c
        for c in comparisons
        if c.classical_status == "OPTIMUM" and c.scheduling_status == "OPTIMUM"
    ]

    var_augmentations = [
        c.var_augmentation for c in status_comparable if c.classical_vars > 0
    ]
    constraint_augmentations = [
        c.constraint_augmentation
        for c in status_comparable
        if c.classical_constraints > 0
    ]
    solve_speedups = [c.solve_speedup for c in status_comparable if c.solve_speedup > 0]
    loc_reductions = [c.loc_reduction for c in status_comparable if c.classical_loc > 0]

    summary = {
        "num_models": len(comparisons),
        "num_status_comparable": len(status_comparable),
        "num_objective_snapshot_comparable": len(objective_snapshot_comparable),
        "num_objective_better_classical": len(objective_better_classical),
        "num_objective_better_scheduling": len(objective_better_scheduling),
        "num_objective_better_tie": len(objective_better_tie),
        "num_classical_optimum": len(classical_optimum),
        "num_scheduling_optimum": len(scheduling_optimum),
        "num_both_optimum": len(both_optimum),
        "num_objective_comparable": len(objective_comparable),
        "num_objective_matches": len(objective_matches),
        "comparisons": [c.to_dict() for c in comparisons],
        "averages": {
            "var_augmentation": _mean(var_augmentations),
            "constraint_augmentation": _mean(constraint_augmentations),
            "solve_speedup": _mean(solve_speedups),
            "loc_reduction": _mean(loc_reductions),
            "objectives_match_rate": (
                len(objective_matches) / len(objective_comparable)
                if objective_comparable
                else None
            ),
            "objective_better_scheduling_rate": (
                len(objective_better_scheduling) / len(objective_snapshot_comparable)
                if objective_snapshot_comparable
                else None
            ),
        },
    }

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)


def try_generate_plots(
    comparisons: list[ComparisonResult], output_dir: Path
) -> bool:
    """Try to generate plots if matplotlib is available."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("  matplotlib not available, skipping plots")
        return False

    models = [c.model_name for c in comparisons]
    x = np.arange(len(models))
    width = 0.35

    # 1. Variable/Constraint Augmentation Bar Chart
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    var_augmentation = [c.var_augmentation * 100 for c in comparisons]
    ctr_augmentation = [c.constraint_augmentation * 100 for c in comparisons]

    axes[0].bar(x, var_augmentation, color="steelblue", edgecolor="black")
    axes[0].set_ylabel("Variable Augmentation (%)")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(models, rotation=45, ha="right")
    axes[0].set_title("Model Compactness: Variables")
    axes[0].axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    axes[0].set_ylim(min(0, min(var_augmentation) - 5), max(var_augmentation) + 5)

    axes[1].bar(x, ctr_augmentation, color="coral", edgecolor="black")
    axes[1].set_ylabel("Constraint Augmentation (%)")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(models, rotation=45, ha="right")
    axes[1].set_title("Model Compactness: Constraints")
    axes[1].axhline(y=0, color="black", linestyle="-", linewidth=0.5)
    axes[1].set_ylim(min(0, min(ctr_augmentation) - 5), max(ctr_augmentation) + 5)

    plt.tight_layout()
    plt.savefig(output_dir / "size_comparison.pdf")
    plt.savefig(output_dir / "size_comparison.png", dpi=150)
    plt.close()

    # 2. Solve Time Comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    classical_times = [c.classical_solve_time for c in comparisons]
    scheduling_times = [c.scheduling_solve_time for c in comparisons]

    ax.bar(x - width / 2, classical_times, width, label="Classical", color="steelblue")
    ax.bar(
        x + width / 2, scheduling_times, width, label="Scheduling", color="coral"
    )
    ax.set_ylabel("Solve Time (s)")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha="right")
    ax.set_title("Solve Time Comparison")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "solve_time_comparison.pdf")
    plt.savefig(output_dir / "solve_time_comparison.png", dpi=150)
    plt.close()

    # 3. LOC Comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    classical_loc = [c.classical_loc for c in comparisons]
    scheduling_loc = [c.scheduling_loc for c in comparisons]

    ax.bar(x - width / 2, classical_loc, width, label="Classical", color="steelblue")
    ax.bar(x + width / 2, scheduling_loc, width, label="Scheduling", color="coral")
    ax.set_ylabel("Lines of Code")
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha="right")
    ax.set_title("Code Size Comparison")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "loc_comparison.pdf")
    plt.savefig(output_dir / "loc_comparison.png", dpi=150)
    plt.close()

    # 4. Scatter plot: Classical vs Scheduling solve time
    fig, ax = plt.subplots(figsize=(8, 8))

    ax.scatter(classical_times, scheduling_times, s=100, alpha=0.7)

    # Add model labels
    for i, model in enumerate(models):
        ax.annotate(
            model,
            (classical_times[i], scheduling_times[i]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=8,
        )

    # Add diagonal line (equal performance)
    max_time = max(max(classical_times), max(scheduling_times))
    ax.plot([0, max_time], [0, max_time], "k--", alpha=0.5, label="Equal")

    ax.set_xlabel("Classical Solve Time (s)")
    ax.set_ylabel("Scheduling Solve Time (s)")
    ax.set_title("Solve Time: Classical vs Scheduling")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_dir / "solve_time_scatter.pdf")
    plt.savefig(output_dir / "solve_time_scatter.png", dpi=150)
    plt.close()

    # 5. Objective snapshot quality (incumbent comparison)
    fig, ax = plt.subplots(figsize=(8, 5))

    snapshot_labels = ["Classical Better", "Tie", "Scheduling Better", "N/A"]
    snapshot_values = [
        sum(1 for c in comparisons if c.objective_better == "classical"),
        sum(1 for c in comparisons if c.objective_better == "tie"),
        sum(1 for c in comparisons if c.objective_better == "scheduling"),
        sum(1 for c in comparisons if c.objective_better is None),
    ]
    snapshot_colors = ["steelblue", "gray", "coral", "lightgray"]

    ax.bar(snapshot_labels, snapshot_values, color=snapshot_colors, edgecolor="black")
    ax.set_ylabel("Number of Model/Instance Pairs")
    ax.set_title("Objective Snapshot Quality")
    ax.set_ylim(0, max(snapshot_values) + 1 if snapshot_values else 1)

    plt.tight_layout()
    plt.savefig(output_dir / "objective_snapshot_comparison.pdf")
    plt.savefig(output_dir / "objective_snapshot_comparison.png", dpi=150)
    plt.close()

    # 6. Number of proven optima
    fig, ax = plt.subplots(figsize=(8, 5))

    optimum_labels = ["Classical OPTIMUM", "Scheduling OPTIMUM", "Both OPTIMUM"]
    optimum_values = [
        sum(1 for c in comparisons if c.classical_status == "OPTIMUM"),
        sum(1 for c in comparisons if c.scheduling_status == "OPTIMUM"),
        sum(
            1
            for c in comparisons
            if c.classical_status == "OPTIMUM" and c.scheduling_status == "OPTIMUM"
        ),
    ]

    ax.bar(optimum_labels, optimum_values, color=["steelblue", "coral", "seagreen"], edgecolor="black")
    ax.set_ylabel("Number of Model/Instance Pairs")
    ax.set_title("Proven Optimality Counts")
    ax.set_ylim(0, max(optimum_values) + 1 if optimum_values else 1)

    plt.tight_layout()
    plt.savefig(output_dir / "optimality_counts.pdf")
    plt.savefig(output_dir / "optimality_counts.png", dpi=150)
    plt.close()

    return True


def generate_comparison_report(
    results: list[dict],
    output_dir: Path,
    generate_plots: bool = True,
    formats: set[str] | None = None,
) -> list[ComparisonResult]:
    """Generate all comparison reports from raw results."""
    selected_formats = formats or {"csv", "latex", "json", "plots"}

    # Aggregate results
    by_model = aggregate_results(results)

    # Build comparisons
    comparisons = []
    for (model, instance), versions in sorted(by_model.items()):
        classical = versions.get("classical")
        scheduling = versions.get("scheduling")

        if classical and scheduling:
            comparison = ComparisonResult.from_runs(classical, scheduling)
            comparisons.append(comparison)
        else:
            print(
                f"  Warning: Missing {'classical' if not classical else 'scheduling'} "
                f"for {model}/{instance}"
            )

    if not comparisons:
        print("  No valid comparisons to report")
        return []

    # Create reports directory
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Generate reports
    if "csv" in selected_formats:
        print(f"  CSV report: {reports_dir / 'comparison.csv'}")
        generate_csv_report(comparisons, reports_dir / "comparison.csv")

    if "latex" in selected_formats:
        print(f"  LaTeX table: {reports_dir / 'comparison.tex'}")
        generate_latex_table(comparisons, reports_dir / "comparison.tex")

    if "json" in selected_formats:
        print(f"  JSON summary: {reports_dir / 'summary.json'}")
        generate_summary_json(comparisons, reports_dir / "summary.json")

    if generate_plots and "plots" in selected_formats:
        print("  Generating plots...")
        if try_generate_plots(comparisons, reports_dir):
            print("  Plots saved to reports/")

    # Print summary to console
    status_comparable = [c for c in comparisons if c.statuses_comparable]
    objective_snapshot_comparable = [
        c for c in comparisons if c.objective_snapshot_comparable
    ]
    objective_comparable = [c for c in comparisons if c.objectives_comparable]
    objective_matches = [c for c in objective_comparable if c.objectives_match is True]
    objective_better_classical = [
        c for c in objective_snapshot_comparable if c.objective_better == "classical"
    ]
    objective_better_scheduling = [
        c for c in objective_snapshot_comparable if c.objective_better == "scheduling"
    ]
    objective_better_tie = [
        c for c in objective_snapshot_comparable if c.objective_better == "tie"
    ]
    classical_optimum = [c for c in comparisons if c.classical_status == "OPTIMUM"]
    scheduling_optimum = [c for c in comparisons if c.scheduling_status == "OPTIMUM"]
    both_optimum = [
        c
        for c in comparisons
        if c.classical_status == "OPTIMUM" and c.scheduling_status == "OPTIMUM"
    ]

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(
        f"{'Model':<20} {'Var Aug':>10} {'Ctr Aug':>10} {'Obj Best':>10} {'Obj Match':>10} {'Status':>8}"
    )
    print("-" * 60)
    for c in comparisons:
        obj_best = _objective_better_label(c.objective_better)
        obj_match = _objective_match_label(c.objectives_match)
        status_str = "OK" if c.statuses_comparable else "N/A"
        print(
            f"{c.model_name:<20} "
            f"{c.var_augmentation * 100:>9.1f}% "
            f"{c.constraint_augmentation * 100:>9.1f}% "
            f"{obj_best:>10} "
            f"{obj_match:>10} "
            f"{status_str:>8}"
        )
    print("-" * 60)
    avg_var = _mean(
        [c.var_augmentation for c in status_comparable if c.classical_vars > 0]
    )
    avg_ctr = _mean(
        [
            c.constraint_augmentation
            for c in status_comparable
            if c.classical_constraints > 0
        ]
    )
    match_rate = (
        len(objective_matches) / len(objective_comparable) * 100
        if objective_comparable
        else None
    )
    avg_var_txt = f"{avg_var * 100:>9.1f}%" if avg_var is not None else f"{'N/A':>10}"
    avg_ctr_txt = f"{avg_ctr * 100:>9.1f}%" if avg_ctr is not None else f"{'N/A':>10}"
    match_txt = f"{match_rate:>9.1f}%" if match_rate is not None else f"{'N/A':>10}"
    print(
        f"{'AVERAGE(valid)':<20} {avg_var_txt} {avg_ctr_txt} "
        f"{'':>10} {match_txt} {'':>8}"
    )
    print(
        f"{'Valid pairs':<20} "
        f"{len(status_comparable):>10}/{len(comparisons)} "
        f"{'':>10} "
        f"{len(objective_matches):>5}/{len(objective_comparable):<4}"
        f"{'':>8}"
    )
    print(
        f"{'OPTIMUM proven':<20} "
        f"C:{len(classical_optimum):>2}/{len(comparisons):<2} "
        f"S:{len(scheduling_optimum):>2}/{len(comparisons):<2} "
        f"{'':>10} "
        f"Both:{len(both_optimum):>2}/{len(comparisons):<2}"
        f"{'':>8}"
    )
    print(
        f"{'Obj better(snapshot)':<20} "
        f"C:{len(objective_better_classical):>2} "
        f"S:{len(objective_better_scheduling):>2} "
        f"Tie:{len(objective_better_tie):>2} "
        f"{'':>10} "
        f"N:{len(objective_snapshot_comparable):>2}"
        f"{'':>8}"
    )
    print("=" * 60)

    return comparisons


def main():
    parser = argparse.ArgumentParser(description="Generate benchmark comparison reports")
    parser.add_argument(
        "--input",
        default="benchmarks/results/results_latest.json",
        help="Path to results JSON file",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/results",
        help="Output directory for reports",
    )
    parser.add_argument(
        "--format",
        default="all",
        choices=["all", "csv", "latex", "json", "plots"],
        help="Report format to generate",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation",
    )
    args = parser.parse_args()

    # Load results
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Results file not found: {input_path}")
        return 1

    with open(input_path) as f:
        results = json.load(f)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_formats = (
        {"csv", "latex", "json", "plots"}
        if args.format == "all"
        else {args.format}
    )
    if args.no_plots:
        selected_formats.discard("plots")

    if not selected_formats:
        print("No report format selected (plots were disabled).")
        return 0

    generate_comparison_report(
        results,
        output_dir,
        generate_plots=not args.no_plots,
        formats=selected_formats,
    )

    return 0


if __name__ == "__main__":
    exit(main())
