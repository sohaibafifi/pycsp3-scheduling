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

from metrics import ComparisonResult, RunResult, compare_objective_values


def _mean(values: list[float]) -> float | None:
    """Return arithmetic mean or None if empty."""
    if not values:
        return None
    return sum(values) / len(values)


def _weighted_mean(values: list[float], weights: list[int]) -> float | None:
    """Return weighted mean or None if empty."""
    if not values or not weights:
        return None
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    return sum(v * w for v, w in zip(values, weights)) / total_weight


def _fmt_count(value: float | int, instance_count: int) -> str:
    """Format count-like values, showing decimals only for aggregated rows."""
    if instance_count <= 1:
        return str(int(value))
    try:
        if float(value).is_integer():
            return str(int(value))
    except (TypeError, ValueError):
        return str(value)
    return f"{value:.1f}"


def _fmt_objective(value: float | int | None, instance_count: int) -> str:
    """Format objective values (averaged on aggregated rows)."""
    if value is None:
        return ""
    if instance_count <= 1:
        try:
            if float(value).is_integer():
                return str(int(value))
        except (TypeError, ValueError):
            return str(value)
        return str(value)
    return f"{float(value):.2f}"


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


def aggregate_comparisons_by_model(
    comparisons: list[ComparisonResult],
) -> list[ComparisonResult]:
    """Aggregate comparisons across instances, producing one row per model."""
    grouped: dict[str, list[ComparisonResult]] = defaultdict(list)
    for c in comparisons:
        grouped[c.model_name].append(c)

    aggregated: list[ComparisonResult] = []
    for model_name, items in sorted(grouped.items()):
        instance_count = sum(c.instance_count for c in items) or len(items)

        def wmean(attr: str) -> float:
            vals: list[float] = []
            weights: list[int] = []
            for c in items:
                val = getattr(c, attr)
                if val is None:
                    continue
                weight = c.instance_count if c.instance_count > 0 else 1
                vals.append(float(val))
                weights.append(weight)
            mean_val = _weighted_mean(vals, weights)
            return mean_val if mean_val is not None else 0.0

        def combine_status(values: list[str]) -> str:
            values = [v for v in values if v]
            if not values:
                return ""
            return values[0] if all(v == values[0] for v in values) else "MIXED"

        objective_items = [
            c
            for c in items
            if c.objective_snapshot_comparable
            and c.classical_objective is not None
            and c.scheduling_objective is not None
        ]
        if objective_items:
            weights = [c.instance_count if c.instance_count > 0 else 1 for c in objective_items]
            classical_obj_avg = _weighted_mean(
                [float(c.classical_objective) for c in objective_items],
                weights,
            )
            scheduling_obj_avg = _weighted_mean(
                [float(c.scheduling_objective) for c in objective_items],
                weights,
            )
            if classical_obj_avg is not None and scheduling_obj_avg is not None:
                objective_better = compare_objective_values(
                    classical_obj_avg, scheduling_obj_avg
                )
                objective_snapshot_comparable = True
            else:
                objective_better = None
                objective_snapshot_comparable = False
        else:
            classical_obj_avg = None
            scheduling_obj_avg = None
            objective_better = None
            objective_snapshot_comparable = False

        comparable_items = [c for c in items if c.objectives_comparable]
        if comparable_items:
            any_mismatch = any(c.objectives_match is False for c in comparable_items)
            all_match = all(c.objectives_match is True for c in comparable_items)
            objectives_match = True if all_match else False if any_mismatch else None
            objectives_comparable = True
        else:
            objectives_match = None
            objectives_comparable = False

        aggregated.append(
            ComparisonResult(
                model_name=model_name,
                instance=f"avg({instance_count})",
                instance_count=instance_count,
                classical_vars=wmean("classical_vars"),
                classical_constraints=wmean("classical_constraints"),
                classical_solve_time=wmean("classical_solve_time"),
                classical_build_time=wmean("classical_build_time"),
                classical_total_time=wmean("classical_total_time"),
                classical_objective=classical_obj_avg,
                classical_status=combine_status([c.classical_status for c in items]),
                classical_loc=wmean("classical_loc"),
                scheduling_vars=wmean("scheduling_vars"),
                scheduling_constraints=wmean("scheduling_constraints"),
                scheduling_solve_time=wmean("scheduling_solve_time"),
                scheduling_build_time=wmean("scheduling_build_time"),
                scheduling_total_time=wmean("scheduling_total_time"),
                scheduling_objective=scheduling_obj_avg,
                scheduling_status=combine_status([c.scheduling_status for c in items]),
                scheduling_loc=wmean("scheduling_loc"),
                scheduling_interval_vars=wmean("scheduling_interval_vars"),
                scheduling_sequences=wmean("scheduling_sequences"),
                var_augmentation=wmean("var_augmentation"),
                constraint_augmentation=wmean("constraint_augmentation"),
                solve_speedup=wmean("solve_speedup"),
                total_speedup=wmean("total_speedup"),
                loc_reduction=wmean("loc_reduction"),
                statuses_comparable=any(c.statuses_comparable for c in items),
                objective_snapshot_comparable=objective_snapshot_comparable,
                objective_better=objective_better,
                objectives_comparable=objectives_comparable,
                objectives_match=objectives_match,
            )
        )

    return aggregated


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
                "Instances",
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
                "Classical_Obj_Avg",
                "Scheduling_Obj_Avg",
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
                    c.instance_count,
                    _fmt_count(c.classical_vars, c.instance_count),
                    _fmt_count(c.scheduling_vars, c.instance_count),
                    f"{c.var_augmentation * 100:.1f}",
                    _fmt_count(c.classical_constraints, c.instance_count),
                    _fmt_count(c.scheduling_constraints, c.instance_count),
                    f"{c.constraint_augmentation * 100:.1f}",
                    f"{c.classical_solve_time:.3f}",
                    f"{c.scheduling_solve_time:.3f}",
                    f"{c.solve_speedup:.2f}",
                    _fmt_count(c.classical_loc, c.instance_count),
                    _fmt_count(c.scheduling_loc, c.instance_count),
                    f"{c.loc_reduction * 100:.1f}",
                    _fmt_count(c.scheduling_interval_vars, c.instance_count),
                    _fmt_count(c.scheduling_sequences, c.instance_count),
                    _fmt_objective(c.classical_objective, c.instance_count),
                    _fmt_objective(c.scheduling_objective, c.instance_count),
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
                f"{_fmt_count(c.classical_vars, c.instance_count)} & "
                f"{_fmt_count(c.scheduling_vars, c.instance_count)} & "
                f"{_fmt_count(c.classical_constraints, c.instance_count)} & "
                f"{_fmt_count(c.scheduling_constraints, c.instance_count)} & "
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
    objective_avg_pairs = [
        c
        for c in objective_snapshot_comparable
        if c.classical_objective is not None and c.scheduling_objective is not None
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
    avg_classical_objective = _mean(
        [c.classical_objective for c in objective_avg_pairs]  # type: ignore[arg-type]
    )
    avg_scheduling_objective = _mean(
        [c.scheduling_objective for c in objective_avg_pairs]  # type: ignore[arg-type]
    )
    avg_objective_gap = (
        _mean(
            [
                c.scheduling_objective - c.classical_objective
                for c in objective_avg_pairs
            ]
        )
        if objective_avg_pairs
        else None
    )

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
            "classical_objective_avg": avg_classical_objective,
            "scheduling_objective_avg": avg_scheduling_objective,
            "objective_avg_gap": avg_objective_gap,
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

    # 5. Average objective comparison (lower is better)
    obj_models = []
    classical_obj = []
    scheduling_obj = []
    for c in comparisons:
        if c.classical_objective is None or c.scheduling_objective is None:
            continue
        obj_models.append(c.model_name)
        classical_obj.append(c.classical_objective)
        scheduling_obj.append(c.scheduling_objective)

    if obj_models:
        x_obj = np.arange(len(obj_models))
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.bar(
            x_obj - width / 2,
            classical_obj,
            width,
            label="Classical",
            color="steelblue",
        )
        ax.bar(
            x_obj + width / 2,
            scheduling_obj,
            width,
            label="Scheduling",
            color="coral",
        )
        ax.set_ylabel("Average Objective (lower is better)")
        ax.set_xticks(x_obj)
        ax.set_xticklabels(obj_models, rotation=45, ha="right")
        ax.set_title("Average Objective Comparison")
        ax.legend()

        plt.tight_layout()
        plt.savefig(output_dir / "objective_avg_comparison.pdf")
        plt.savefig(output_dir / "objective_avg_comparison.png", dpi=150)
        plt.close()

        # Objective gap (Scheduling - Classical)
        gaps = [s - c for s, c in zip(scheduling_obj, classical_obj)]
        gap_colors = [
            "seagreen" if g < 0 else ("coral" if g > 0 else "gray") for g in gaps
        ]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(x_obj, gaps, color=gap_colors, edgecolor="black")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_ylabel("Objective Gap (Scheduling - Classical)")
        ax.set_xticks(x_obj)
        ax.set_xticklabels(obj_models, rotation=45, ha="right")
        ax.set_title("Average Objective Gap (negative = scheduling better)")

        plt.tight_layout()
        plt.savefig(output_dir / "objective_gap.pdf")
        plt.savefig(output_dir / "objective_gap.png", dpi=150)
        plt.close()

    # 6. Objective average better counts
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
    ax.set_ylabel("Number of Models")
    ax.set_title("Objective Average: Better Counts")
    ax.set_ylim(0, max(snapshot_values) + 1 if snapshot_values else 1)

    plt.tight_layout()
    plt.savefig(output_dir / "objective_snapshot_comparison.pdf")
    plt.savefig(output_dir / "objective_snapshot_comparison.png", dpi=150)
    plt.close()

    # 7. Number of proven optima
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
    ax.set_ylabel("Number of Models")
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

    # Aggregate across instances to one row per model (averages)
    comparisons = aggregate_comparisons_by_model(comparisons)

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
    objective_avg_pairs = [
        c
        for c in objective_snapshot_comparable
        if c.classical_objective is not None and c.scheduling_objective is not None
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
        f"{'Obj better(avg)':<20} "
        f"C:{len(objective_better_classical):>2} "
        f"S:{len(objective_better_scheduling):>2} "
        f"Tie:{len(objective_better_tie):>2} "
        f"{'':>10} "
        f"N:{len(objective_snapshot_comparable):>2}"
        f"{'':>8}"
    )
    if objective_avg_pairs:
        avg_classical_obj = _mean(
            [c.classical_objective for c in objective_avg_pairs]  # type: ignore[arg-type]
        )
        avg_scheduling_obj = _mean(
            [c.scheduling_objective for c in objective_avg_pairs]  # type: ignore[arg-type]
        )
        if avg_classical_obj is not None and avg_scheduling_obj is not None:
            gap = avg_scheduling_obj - avg_classical_obj
            print(
                f"{'Objective avg':<20} "
                f"C:{avg_classical_obj:>8.2f} "
                f"S:{avg_scheduling_obj:>8.2f} "
                f"Gap:{gap:>8.2f}"
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
