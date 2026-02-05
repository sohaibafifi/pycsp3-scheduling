#!/usr/bin/env python3
"""
Build a model/instance manifest for array-job benchmark execution.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _resolve(path_like: str) -> Path:
    p = Path(path_like)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a TSV manifest for sbatch/oar array benchmark runs"
    )
    parser.add_argument(
        "--config",
        default="benchmarks/config.yaml",
        help="Path to benchmark config YAML",
    )
    parser.add_argument(
        "--suite",
        default="full",
        choices=["quick", "full"],
        help="Suite selection controls default instance subset",
    )
    parser.add_argument(
        "--model",
        action="append",
        help="Model name to include (repeat flag for multiple models)",
    )
    parser.add_argument(
        "--instance",
        help="Single instance to include (requires exactly one --model)",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=1,
        help="How many repetition slots to emit per model/instance",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/results/jobs/manifest.tsv",
        help="Output TSV path",
    )
    args = parser.parse_args()

    if args.repetitions < 1:
        print("Error: --repetitions must be >= 1")
        return 1

    if args.instance and (not args.model or len(args.model) != 1):
        print("Error: --instance requires exactly one --model")
        return 1

    config_path = _resolve(args.config)
    with open(config_path) as f:
        config = yaml.safe_load(f)

    models_cfg = config.get("models", {})
    suite_cfg = config.get("suites", {}).get(args.suite, {})
    instances_per_model = suite_cfg.get("instances_per_model")

    if args.model:
        unknown = [m for m in args.model if m not in models_cfg]
        if unknown:
            print(f"Error: unknown model(s): {', '.join(unknown)}")
            print(f"Available models: {', '.join(sorted(models_cfg.keys()))}")
            return 1
        selected_model_names = args.model
    else:
        selected_model_names = sorted(models_cfg.keys())

    rows: list[tuple[str, str, int]] = []
    for model_name in selected_model_names:
        instances = list(models_cfg[model_name].get("instances", []))
        if instances_per_model == 1:
            instances = instances[:1]

        if args.instance:
            if args.instance not in instances:
                print(
                    f"Error: instance '{args.instance}' not found for model '{model_name}'"
                )
                return 1
            instances = [args.instance]

        for repetition in range(args.repetitions):
            for instance in instances:
                rows.append((model_name, instance, repetition))

    if not rows:
        print("Error: no manifest rows generated")
        return 1

    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for model_name, instance, repetition in rows:
            f.write(f"{model_name}\t{instance}\t{repetition}\n")

    print(f"Manifest rows: {len(rows)}")
    print(f"Saved to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
