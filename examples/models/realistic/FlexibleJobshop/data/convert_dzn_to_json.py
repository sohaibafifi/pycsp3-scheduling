#!/usr/bin/env python3
"""Convert FlexibleJobshop MiniZinc .dzn instances to JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ASSIGNMENT_PATTERN = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);", re.DOTALL)


def _strip_comments(content: str) -> str:
    return "\n".join(line.split("%", 1)[0] for line in content.splitlines())


def _split_top_level_csv(content: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in content:
        if ch == "," and depth == 0:
            token = "".join(current).strip()
            if token:
                tokens.append(token)
            current = []
            continue
        if ch in "[{(":
            depth += 1
        elif ch in "]})":
            depth -= 1
            if depth < 0:
                raise ValueError("Malformed expression: unexpected closing bracket")
        current.append(ch)

    if depth != 0:
        raise ValueError("Malformed expression: unbalanced brackets")

    token = "".join(current).strip()
    if token:
        tokens.append(token)
    return tokens


def _parse_int(token: str) -> int:
    return int(token.strip())


def _parse_int_list(expr: str) -> list[int]:
    expr = expr.strip()
    if not (expr.startswith("[") and expr.endswith("]")):
        raise ValueError(f"Expected bracket list, got: {expr[:30]}")
    return [_parse_int(token) for token in _split_top_level_csv(expr[1:-1])]


def _parse_index_token(token: str) -> list[int]:
    token = token.strip()
    if token.startswith("{") and token.endswith("}"):
        inner = token[1:-1].strip()
        return [] if not inner else [_parse_int(part) for part in _split_top_level_csv(inner)]
    if ".." in token:
        left, right = token.split("..", 1)
        start, end = _parse_int(left), _parse_int(right)
        if end < start:
            raise ValueError(f"Invalid range {token}")
        return list(range(start, end + 1))
    return [_parse_int(token)]


def _parse_grouped_indexes(expr: str) -> list[list[int]]:
    expr = expr.strip()
    if not (expr.startswith("[") and expr.endswith("]")):
        raise ValueError(f"Expected bracket list, got: {expr[:30]}")
    return [_parse_index_token(token) for token in _split_top_level_csv(expr[1:-1])]


def _decrement(values: list[int]) -> list[int]:
    return [value - 1 for value in values]


def _decrement_nested(values: list[list[int]]) -> list[list[int]]:
    return [[value - 1 for value in group] for group in values]


def parse_flexible_jobshop_dzn(path: Path) -> dict[str, object]:
    content = _strip_comments(path.read_text())
    assignments = {key: value.strip() for key, value in ASSIGNMENT_PATTERN.findall(content)}

    required = ("no_mach", "no_jobs", "no_task", "no_optt", "tasks", "optts", "optt_mach", "optt_dur")
    missing = [name for name in required if name not in assignments]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    n_machines = _parse_int(assignments["no_mach"])
    n_jobs = _parse_int(assignments["no_jobs"])
    n_tasks = _parse_int(assignments["no_task"])
    n_options = _parse_int(assignments["no_optt"])

    tasks = _decrement_nested(_parse_grouped_indexes(assignments["tasks"]))
    optional_tasks = _decrement_nested(_parse_grouped_indexes(assignments["optts"]))
    machines = _decrement(_parse_int_list(assignments["optt_mach"]))
    durations = _parse_int_list(assignments["optt_dur"])

    if len(tasks) != n_jobs:
        raise ValueError(f"Expected {n_jobs} jobs, found {len(tasks)}")
    if len(optional_tasks) != n_tasks:
        raise ValueError(f"Expected {n_tasks} tasks, found {len(optional_tasks)}")
    if len(machines) != n_options:
        raise ValueError(f"Expected {n_options} options in optt_mach, found {len(machines)}")
    if len(durations) != n_options:
        raise ValueError(f"Expected {n_options} options in optt_dur, found {len(durations)}")

    return {
        "nMachines": n_machines,
        "tasks": tasks,
        "optionalTasks": optional_tasks,
        "machines": machines,
        "durations": durations,
    }


def _default_input_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[5]
    return repo_root / "examples" / "PyCSP3-models" / "realistic" / "FlexibleJobshop" / "data"


def _default_output_dir() -> Path:
    return Path(__file__).resolve().parent


def _collect_inputs(positional_inputs: list[Path], input_dir: Path, glob_pattern: str) -> list[Path]:
    if positional_inputs:
        return [path.resolve() for path in positional_inputs]
    return sorted(path.resolve() for path in input_dir.glob(glob_pattern))


def _convert_one(input_path: Path, output_dir: Path, overwrite: bool) -> tuple[Path, str]:
    output_path = output_dir / f"{input_path.stem}.json"
    if output_path.exists() and not overwrite:
        return output_path, "skipped"

    payload = parse_flexible_jobshop_dzn(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n")
    return output_path, "written"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert FlexibleJobshop MiniZinc .dzn files to JSON files compatible with "
            "examples/models/realistic/FlexibleJobshop/FlexibleJobshop.py"
        )
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="Specific .dzn file(s) to convert")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=_default_input_dir(),
        help="Directory scanned when no positional inputs are provided",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Directory where .json files are written",
    )
    parser.add_argument("--glob", default="*.dzn", help="File pattern used with --input-dir")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing .json files",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()
    input_paths = _collect_inputs(args.inputs, args.input_dir, args.glob)
    if not input_paths:
        print(f"No input files found in {args.input_dir} with pattern {args.glob}")
        return 1

    written = 0
    skipped = 0
    for input_path in input_paths:
        output_path, status = _convert_one(input_path, args.output_dir, args.overwrite)
        print(f"{status:7} {input_path} -> {output_path}")
        if status == "written":
            written += 1
        else:
            skipped += 1

    print(f"Done: {written} written, {skipped} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
