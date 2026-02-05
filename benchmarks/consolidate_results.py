#!/usr/bin/env python3
"""
Merge benchmark JSON files produced by parallel jobs and regenerate reports.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from report import generate_comparison_report


def _expand_patterns(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = [Path(p) for p in glob.glob(pattern, recursive=True)]
        files.extend(sorted(matches))
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in files:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _load_results(files: list[Path]) -> list[dict]:
    merged: list[dict] = []
    for path in files:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            merged.extend(item for item in data if isinstance(item, dict))
        else:
            print(f"  Warning: skipping non-list results file: {path}")
    return merged


def _dedupe_results(results: list[dict]) -> list[dict]:
    """
    Deduplicate by (model_type, model_name, instance, repetition).

    If duplicates exist, keeps the latest encountered record.
    """
    latest: dict[tuple[str, str, str, int], dict] = {}
    for r in results:
        key = (
            str(r.get("model_type", "")),
            str(r.get("model_name", "")),
            str(r.get("instance", "")),
            int(r.get("repetition", 0)),
        )
        latest[key] = r
    deduped = list(latest.values())
    deduped.sort(
        key=lambda r: (
            str(r.get("model_name", "")),
            str(r.get("instance", "")),
            str(r.get("model_type", "")),
            int(r.get("repetition", 0)),
        )
    )
    return deduped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Consolidate benchmark result files and regenerate reports"
    )
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="Input glob patterns (e.g. 'benchmarks/results/jobs/*/results_*.json')",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/results/results_merged.json",
        help="Path to merged output JSON file",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Keep duplicate entries instead of deduplicating",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation after merge",
    )
    parser.add_argument(
        "--report-dir",
        default=None,
        help="Directory where consolidated reports are generated (default: output parent)",
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

    files = _expand_patterns(args.inputs)
    if not files:
        print("No input files matched.")
        return 1

    print(f"Found {len(files)} files")
    merged = _load_results(files)
    print(f"Loaded {len(merged)} raw rows")

    if not args.no_dedupe:
        merged = _dedupe_results(merged)
        print(f"After dedupe: {len(merged)} rows")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"Merged results saved to: {output_path}")

    latest_path = output_path.parent / "results_latest.json"
    with open(latest_path, "w") as f:
        json.dump(merged, f, indent=2)
    print(f"Latest pointer updated: {latest_path}")

    if args.no_report:
        print("Skipping report generation (--no-report).")
        return 0

    report_dir = Path(args.report_dir) if args.report_dir else output_path.parent
    report_dir.mkdir(parents=True, exist_ok=True)
    selected_formats = (
        {"csv", "latex", "json", "plots"}
        if args.format == "all"
        else {args.format}
    )
    if args.no_plots:
        selected_formats.discard("plots")

    print("Generating consolidated reports...")
    generate_comparison_report(
        merged,
        report_dir,
        generate_plots=not args.no_plots,
        formats=selected_formats,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
