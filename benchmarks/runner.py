#!/usr/bin/env python3
"""
Benchmark Runner for pycsp3-scheduling comparison.

Runs classical pycsp3 models and pycsp3-scheduling models, collecting metrics
for comparison.

Key insight: pycsp3 models cannot be run via exec() because pycsp3 uses
introspection to extract variable names from source code. We must run
them as separate Python scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

from metrics import RunResult, compare_objective_values, count_loc, now_iso
from report import generate_comparison_report

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def convert_flat_to_classical(flat_data: list) -> dict:
    """
    Convert scheduling flat format to classical pycsp3 format.

    Flat: [[[dur1, ...], [res1, ...], release, due], ...]
    Classical: {"jobs": [{"durations": [...], "resources": [...], ...}]}
    """
    return {
        "jobs": [
            {
                "durations": job[0],
                "resources": job[1],
                "releaseDate": job[2] if len(job) > 2 else 0,
                "dueDate": job[3] if len(job) > 3 else -1
            }
            for job in flat_data
        ]
    }


def _looks_like_scheduling_flat(raw_data: object) -> bool:
    """
    Check if JSON data follows scheduling-flat shape.

    Expected per job: [[durations...], [resources...], release, due]
    """
    if not isinstance(raw_data, list) or not raw_data:
        return False
    first = raw_data[0]
    if not isinstance(first, list) or len(first) < 2:
        return False
    return isinstance(first[0], list) and isinstance(first[1], list)


def should_convert_classical_data(raw_data: object, data_format: str) -> bool:
    """Decide if benchmark runner must convert scheduling-flat data for classical models."""
    normalized = data_format.lower()
    if normalized in {"scheduling_flat", "flat"}:
        return True
    if normalized in {"native", "as_is", "asis", "none"}:
        return False
    if normalized == "auto":
        return _looks_like_scheduling_flat(raw_data)
    print(f"  Warning: Unknown data_format '{data_format}', using auto detection")
    return _looks_like_scheduling_flat(raw_data)


def create_classical_wrapper(
    model_path: str,
    data_path: str,
    output_json: str,
    timeout: int,
) -> str:
    """Create wrapper script for classical pycsp3 model."""
    return f'''#!/usr/bin/env python3
"""Wrapper to run classical pycsp3 model and capture metrics."""
import json
import os
import re
import sys
import time

# Configuration
MODEL_PATH = "{model_path}"
DATA_PATH = "{data_path}"
OUTPUT_PATH = "{output_json}"

def save_result(result):
    """Save result to output file."""
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f)

# Initialize result
result = {{
    "status": "UNKNOWN",
    "error": None,
    "build_time": 0,
    "solve_time": 0,
    "n_vars": 0,
    "n_constraints": 0,
    "constraint_types": {{}},
    "objective": None,
}}

# Setup - first generate XML without solving
sys.argv = [MODEL_PATH, "-data=" + DATA_PATH]
sys.path.insert(0, "{PROJECT_ROOT}")
os.chdir("{PROJECT_ROOT}")

import glob as g

build_start = time.time()

try:
    # Run model to generate XCSP3 (without -solve)
    import runpy
    runpy.run_path(MODEL_PATH, run_name="__main__")
    result["build_time"] = time.time() - build_start
    # Manually trigger XML generation (pycsp3 normally does this on atexit)
    from pycsp3 import compile as pycsp3_compile
    pycsp3_compile()
except BaseException as e:
    result["status"] = "ERROR"
    result["error"] = (f"{{type(e).__name__}}: {{e}}" if str(e) else type(e).__name__)[:500]
    result["build_time"] = time.time() - build_start
    save_result(result)
    sys.exit(0)

# Get XCSP3 statistics from the generated XML file
try:
    import glob
    xml_files = glob.glob("*.xml")
    if xml_files:
        xml_file = max(xml_files, key=os.path.getmtime)
        result["_debug_xml_file"] = xml_file  # Debug info
        from xml.etree import ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()

        ns = ""
        if root.tag.startswith("{{"):
            ns = root.tag.split("}}")[0] + "}}"

        # Count variables
        vars_section = root.find(f".//{{ns}}variables")
        if vars_section is not None:
            for child in vars_section:
                tag = child.tag.replace(ns, "")
                if tag == "var":
                    result["n_vars"] += 1
                elif tag == "array":
                    size_str = child.get("size", "")
                    dims = re.findall(r"\\d+", size_str)
                    if dims:
                        count = 1
                        for d in dims:
                            count *= int(d)
                        result["n_vars"] += count

        # Count constraints
        def count_constraints(element):
            """Recursively count instantiated constraints in XCSP3 element."""
            tag = element.tag.replace(ns, "")
            ctype = {{}}

            if tag == "constraints":
                total = 0
                for sub in element:
                    c, ct = count_constraints(sub)
                    total += c
                    for k, v in ct.items():
                        ctype[k] = ctype.get(k, 0) + v
                return total, ctype

            if tag == "group":
                args_count = 0
                template_count = 0
                template_types = {{}}
                for sub in element:
                    subtag = sub.tag.replace(ns, "")
                    if subtag == "args":
                        args_count += 1
                        continue
                    c, ct = count_constraints(sub)
                    template_count += c
                    for k, v in ct.items():
                        template_types[k] = template_types.get(k, 0) + v

                if args_count == 0 or template_count == 0:
                    return 0, ctype

                for k, v in template_types.items():
                    ctype[k] = v * args_count
                return template_count * args_count, ctype

            if tag == "block":
                total = 0
                for sub in element:
                    c, ct = count_constraints(sub)
                    total += c
                    for k, v in ct.items():
                        ctype[k] = ctype.get(k, 0) + v
                return total, ctype

            # Direct primitive/meta-constraint
            ctype[tag] = 1
            return 1, ctype

        ctrs_section = root.find(f".//{{ns}}constraints")
        if ctrs_section is not None:
            for child in ctrs_section:
                c, ct = count_constraints(child)
                result["n_constraints"] += c
                for k, v in ct.items():
                    result["constraint_types"][k] = result["constraint_types"].get(k, 0) + v

        # Save partial result (model stats captured before solving)
        save_result(result)
except BaseException as e:
    result["error"] = (result.get("error") or "") + f" XML parse error: {{(str(e) if str(e) else type(e).__name__)[:200]}}"
    save_result(result)

# Now solve with internal timeout to capture best bound even on timeout
solve_start = time.time()
try:
    from pycsp3 import solve, SAT, OPTIMUM, UNSAT, bound as get_bound
    # Use solver's internal timeout (-t=seconds) to capture intermediate solutions
    solve_result = solve(options="-t={timeout}s")
    result["solve_time"] = time.time() - solve_start

    if solve_result == SAT:
        result["status"] = "SAT"
    elif solve_result == OPTIMUM:
        result["status"] = "OPTIMUM"
    elif solve_result == UNSAT:
        result["status"] = "UNSAT"
    else:
        result["status"] = "TIMEOUT"

    # Get best bound/objective using pycsp3's bound() function
    try:
        obj = get_bound()
        if obj is not None:
            result["objective"] = obj
    except Exception:
        pass
except BaseException as e:
    result["status"] = "ERROR"
    result["solve_time"] = time.time() - solve_start
    result["error"] = (result.get("error") or "") + f" Solve error: {{(str(e) if str(e) else type(e).__name__)[:200]}}"

# Final save
save_result(result)
'''


def create_scheduling_wrapper(
    model_path: str,
    data_path: str,
    output_json: str,
    timeout: int,
) -> str:
    """Create wrapper script for pycsp3-scheduling model."""
    return f'''#!/usr/bin/env python3
"""Wrapper to run pycsp3-scheduling model and capture metrics."""
import json
import os
import re
import sys
import time

# Configuration
MODEL_PATH = "{model_path}"
DATA_PATH = "{data_path}"
OUTPUT_PATH = "{output_json}"

def save_result(result):
    """Save result to output file."""
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f)

# Initialize result
result = {{
    "status": "UNKNOWN",
    "error": None,
    "build_time": 0,
    "solve_time": 0,
    "n_vars": 0,
    "n_constraints": 0,
    "constraint_types": {{}},
    "n_interval_vars": 0,
    "n_optional_intervals": 0,
    "n_sequences": 0,
    "n_cumul_functions": 0,
    "n_state_functions": 0,
    "objective": None,
}}

# Setup - first generate model without solving
sys.argv = [MODEL_PATH, "-data=" + DATA_PATH]
sys.path.insert(0, "{PROJECT_ROOT}")
os.chdir("{PROJECT_ROOT}")

import glob as g

# Clear state before running
from pycsp3_scheduling import clear
clear()

import pycsp3
pycsp3.clear()

build_start = time.time()

try:
    # Run model to generate XCSP3 (without -solve)
    import runpy
    runpy.run_path(MODEL_PATH, run_name="__main__")
    result["build_time"] = time.time() - build_start
    # Manually trigger XML generation (pycsp3 normally does this on atexit)
    from pycsp3 import compile as pycsp3_compile
    pycsp3_compile()
except Exception as e:
    result["status"] = "ERROR"
    result["error"] = (f"{{type(e).__name__}}: {{e}}" if str(e) else type(e).__name__)[:500]
    result["build_time"] = time.time() - build_start
    save_result(result)
    sys.exit(0)

# Get scheduling statistics
try:
    from pycsp3_scheduling import model_statistics
    stats = model_statistics()
    result["n_interval_vars"] = stats.nb_interval_vars
    result["n_optional_intervals"] = stats.nb_optional_interval_vars
    result["n_sequences"] = stats.nb_sequences
    result["n_cumul_functions"] = stats.nb_cumul_functions
    result["n_state_functions"] = stats.nb_state_functions
except Exception as e:
    result["error"] = (result.get("error") or "") + f" Stats error: {{(str(e) if str(e) else type(e).__name__)[:200]}}"

# Get XCSP3 statistics from the generated XML file
try:
    import glob
    xml_files = glob.glob("*.xml")
    if xml_files:
        xml_file = max(xml_files, key=os.path.getmtime)
        from xml.etree import ElementTree as ET
        tree = ET.parse(xml_file)
        root = tree.getroot()

        ns = ""
        if root.tag.startswith("{{"):
            ns = root.tag.split("}}")[0] + "}}"

        vars_section = root.find(f".//{{ns}}variables")
        if vars_section is not None:
            for child in vars_section:
                tag = child.tag.replace(ns, "")
                if tag == "var":
                    result["n_vars"] += 1
                elif tag == "array":
                    size_str = child.get("size", "")
                    dims = re.findall(r"\\d+", size_str)
                    if dims:
                        count = 1
                        for d in dims:
                            count *= int(d)
                        result["n_vars"] += count

        # Count constraints
        def count_constraints(element):
            """Recursively count instantiated constraints in XCSP3 element."""
            tag = element.tag.replace(ns, "")
            ctype = {{}}

            if tag == "constraints":
                total = 0
                for sub in element:
                    c, ct = count_constraints(sub)
                    total += c
                    for k, v in ct.items():
                        ctype[k] = ctype.get(k, 0) + v
                return total, ctype

            if tag == "group":
                args_count = 0
                template_count = 0
                template_types = {{}}
                for sub in element:
                    subtag = sub.tag.replace(ns, "")
                    if subtag == "args":
                        args_count += 1
                        continue
                    c, ct = count_constraints(sub)
                    template_count += c
                    for k, v in ct.items():
                        template_types[k] = template_types.get(k, 0) + v

                if args_count == 0 or template_count == 0:
                    return 0, ctype

                for k, v in template_types.items():
                    ctype[k] = v * args_count
                return template_count * args_count, ctype

            if tag == "block":
                total = 0
                for sub in element:
                    c, ct = count_constraints(sub)
                    total += c
                    for k, v in ct.items():
                        ctype[k] = ctype.get(k, 0) + v
                return total, ctype

            # Direct primitive/meta-constraint
            ctype[tag] = 1
            return 1, ctype

        ctrs_section = root.find(f".//{{ns}}constraints")
        if ctrs_section is not None:
            for child in ctrs_section:
                c, ct = count_constraints(child)
                result["n_constraints"] += c
                for k, v in ct.items():
                    result["constraint_types"][k] = result["constraint_types"].get(k, 0) + v

        # Save partial result (model stats captured before solving)
        save_result(result)
except Exception as e:
    result["error"] = (result.get("error") or "") + f" XML parse error: {{(str(e) if str(e) else type(e).__name__)[:200]}}"
    save_result(result)

# Now solve with internal timeout to capture best bound even on timeout
solve_start = time.time()
try:
    from pycsp3 import solve, SAT, OPTIMUM, UNSAT, bound as get_bound
    # Use solver's internal timeout (-t=seconds) to capture intermediate solutions
    solve_result = solve(options="-t={timeout}s")
    result["solve_time"] = time.time() - solve_start

    if solve_result == SAT:
        result["status"] = "SAT"
    elif solve_result == OPTIMUM:
        result["status"] = "OPTIMUM"
    elif solve_result == UNSAT:
        result["status"] = "UNSAT"
    else:
        result["status"] = "TIMEOUT"

    # Get best bound/objective using pycsp3's bound() function
    try:
        obj = get_bound()
        if obj is not None:
            result["objective"] = obj
    except Exception:
        pass
except BaseException as e:
    result["status"] = "ERROR"
    result["solve_time"] = time.time() - solve_start
    result["error"] = (result.get("error") or "") + f" Solve error: {{(str(e) if str(e) else type(e).__name__)[:200]}}"

# Final save
save_result(result)
'''


def run_model(
    model_path: str,
    data_file: str,
    data_dir: str,
    model_name: str,
    instance: str,
    timeout: int,
    is_scheduling: bool = False,
    repetition: int = 0,
    data_format: str = "auto",
) -> RunResult:
    """Run a model and collect metrics."""
    # Create temp directory for this run
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Prepare data file
        original_data_path = PROJECT_ROOT / data_dir / data_file

        if is_scheduling:
            # Scheduling models use the data as-is
            data_path = str(original_data_path)
        else:
            # Classical models might need data format conversion
            with open(original_data_path) as f:
                raw_data = json.load(f)

            # Convert only when explicitly configured or auto-detected as scheduling-flat.
            if should_convert_classical_data(raw_data, data_format):
                converted_data = convert_flat_to_classical(raw_data)
                converted_path = temp_path / data_file
                with open(converted_path, "w") as f:
                    json.dump(converted_data, f)
                data_path = str(converted_path)
            else:
                data_path = str(original_data_path)

        # Create wrapper script
        output_json = str(temp_path / "output.json")
        full_model_path = str(PROJECT_ROOT / model_path)

        if is_scheduling:
            wrapper_content = create_scheduling_wrapper(
                full_model_path, data_path, output_json, timeout
            )
        else:
            wrapper_content = create_classical_wrapper(
                full_model_path, data_path, output_json, timeout
            )

        wrapper_path = temp_path / "wrapper.py"
        with open(wrapper_path, "w") as f:
            f.write(wrapper_content)

        # Run wrapper
        try:
            total_start = time.time()
            result = subprocess.run(
                ["python", str(wrapper_path)],
                capture_output=True,
                text=True,
                timeout=timeout + 60,  # Safety buffer - solver handles actual timeout
                cwd=PROJECT_ROOT,
            )
            total_time = time.time() - total_start

            # Parse output
            if os.path.exists(output_json):
                with open(output_json) as f:
                    output = json.load(f)
            else:
                stderr_text = (result.stderr or "").strip()
                stdout_text = (result.stdout or "").strip()
                error_parts = [f"No output file (exit={result.returncode})"]
                if stderr_text:
                    error_parts.append(f"stderr: {stderr_text[:300]}")
                elif stdout_text:
                    error_parts.append(f"stdout: {stdout_text[:300]}")
                return RunResult(
                    model_type="scheduling" if is_scheduling else "classical",
                    model_name=model_name,
                    instance=instance,
                    status="ERROR",
                    error=" | ".join(error_parts),
                    total_time=total_time,
                    timestamp=now_iso(),
                    repetition=repetition,
                    loc=count_loc(PROJECT_ROOT / model_path),
                )

            return RunResult(
                model_type="scheduling" if is_scheduling else "classical",
                model_name=model_name,
                instance=instance,
                status=output.get("status", "ERROR"),
                objective=output.get("objective"),
                solve_time=output.get("solve_time", 0),
                build_time=output.get("build_time", 0),
                total_time=total_time,
                n_vars=output.get("n_vars", 0),
                n_constraints=output.get("n_constraints", 0),
                constraint_types=output.get("constraint_types", {}),
                n_interval_vars=output.get("n_interval_vars", 0),
                n_optional_intervals=output.get("n_optional_intervals", 0),
                n_sequences=output.get("n_sequences", 0),
                n_cumul_functions=output.get("n_cumul_functions", 0),
                n_state_functions=output.get("n_state_functions", 0),
                error=output.get("error"),
                timestamp=now_iso(),
                repetition=repetition,
                loc=count_loc(PROJECT_ROOT / model_path),
            )

        except subprocess.TimeoutExpired:
            # Check if output file exists with partial results
            if os.path.exists(output_json):
                try:
                    with open(output_json) as f:
                        output = json.load(f)
                    return RunResult(
                        model_type="scheduling" if is_scheduling else "classical",
                        model_name=model_name,
                        instance=instance,
                        status="TIMEOUT",  # Override status since we timed out
                        objective=output.get("objective"),
                        solve_time=output.get("solve_time", 0),
                        build_time=output.get("build_time", 0),
                        total_time=timeout,
                        n_vars=output.get("n_vars", 0),
                        n_constraints=output.get("n_constraints", 0),
                        constraint_types=output.get("constraint_types", {}),
                        n_interval_vars=output.get("n_interval_vars", 0),
                        n_optional_intervals=output.get("n_optional_intervals", 0),
                        n_sequences=output.get("n_sequences", 0),
                        n_cumul_functions=output.get("n_cumul_functions", 0),
                        n_state_functions=output.get("n_state_functions", 0),
                        error="Solver timeout",
                        timestamp=now_iso(),
                        repetition=repetition,
                        loc=count_loc(PROJECT_ROOT / model_path),
                    )
                except Exception:
                    pass

            return RunResult(
                model_type="scheduling" if is_scheduling else "classical",
                model_name=model_name,
                instance=instance,
                status="TIMEOUT",
                total_time=timeout,
                timestamp=now_iso(),
                repetition=repetition,
                loc=count_loc(PROJECT_ROOT / model_path),
            )
        except Exception as e:
            return RunResult(
                model_type="scheduling" if is_scheduling else "classical",
                model_name=model_name,
                instance=instance,
                status="ERROR",
                error=str(e),
                timestamp=now_iso(),
                repetition=repetition,
                loc=count_loc(PROJECT_ROOT / model_path),
            )


def main():
    parser = argparse.ArgumentParser(
        description="Run benchmark comparison between classical and scheduling models"
    )
    parser.add_argument(
        "--config",
        default="benchmarks/config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--suite",
        default="quick",
        choices=["quick", "full"],
        help="Benchmark suite to run",
    )
    parser.add_argument(
        "--output",
        default="benchmarks/results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--model",
        help="Run only a specific model (by name)",
    )
    parser.add_argument(
        "--instance",
        help="Run only a specific instance (requires --model)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Override timeout in seconds",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        help="Override number of repetitions",
    )
    parser.add_argument(
        "--repetition-offset",
        type=int,
        default=0,
        help="Offset applied to stored repetition index (useful for array jobs)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip report generation (useful for parallel jobs)",
    )
    args = parser.parse_args()

    def _print_error_details(run_result: RunResult) -> None:
        if run_result.status != "ERROR":
            return
        if run_result.error:
            error_text = str(run_result.error).replace("\n", " | ")
            print(f"      Error: {error_text}")

    # Load configuration
    config_path = PROJECT_ROOT / args.config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Get suite settings
    suite_config = config.get("suites", {}).get(args.suite, {})
    timeout = args.timeout or suite_config.get("timeout", config["settings"]["timeout"])
    repetitions = args.repetitions or suite_config.get(
        "repetitions", config["settings"]["repetitions"]
    )
    if args.repetition_offset < 0:
        print("Error: --repetition-offset must be >= 0")
        sys.exit(1)

    # Determine which models to run
    models_to_run = config["models"]
    if args.model:
        if args.model not in models_to_run:
            print(f"Error: Model '{args.model}' not found in config")
            print(f"Available models: {', '.join(models_to_run.keys())}")
            sys.exit(1)
        models_to_run = {args.model: models_to_run[args.model]}
    elif args.instance:
        print("Error: --instance requires --model")
        sys.exit(1)

    # Create output directory
    output_dir = PROJECT_ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total_models = len(models_to_run)

    for idx, (model_name, model_config) in enumerate(models_to_run.items(), 1):
        print(f"\n[{idx}/{total_models}] Running {model_name}...")

        instances = model_config.get("instances", [])
        if suite_config.get("instances_per_model") == 1:
            instances = instances[:1]
        if args.instance:
            if args.instance not in instances:
                print(
                    f"Error: Instance '{args.instance}' not found for model '{model_name}'"
                )
                print(f"Available instances: {', '.join(instances[:10])}...")
                sys.exit(1)
            instances = [args.instance]

        data_format = model_config.get("data_format", "auto")

        for instance in instances:
            print(f"  Instance: {instance}")

            for rep in range(repetitions):
                rep_index = args.repetition_offset + rep
                rep_str = (
                    f" (rep {rep_index + 1})"
                    if repetitions > 1 or args.repetition_offset > 0
                    else ""
                )

                # Run classical model
                print(f"    Classical{rep_str}...", end=" ", flush=True)
                classical_result = run_model(
                    model_path=model_config["classical"],
                    data_file=instance,
                    data_dir=model_config["data_dir"],
                    model_name=model_name,
                    instance=instance,
                    timeout=timeout,
                    is_scheduling=False,
                    repetition=rep_index,
                    data_format=data_format,
                )
                results.append(classical_result.to_dict())
                obj_str = (
                    f", obj={classical_result.objective}"
                    if classical_result.objective is not None
                    else ""
                )
                print(
                    f"{classical_result.status} "
                    f"(vars={classical_result.n_vars}, "
                    f"ctrs={classical_result.n_constraints}, "
                    f"time={classical_result.solve_time:.2f}s{obj_str})"
                )
                _print_error_details(classical_result)

                # Run scheduling model
                print(f"    Scheduling{rep_str}...", end=" ", flush=True)
                scheduling_result = run_model(
                    model_path=model_config["scheduling"],
                    data_file=instance,
                    data_dir=model_config["data_dir"],
                    model_name=model_name,
                    instance=instance,
                    timeout=timeout,
                    is_scheduling=True,
                    repetition=rep_index,
                    data_format=data_format,
                )
                results.append(scheduling_result.to_dict())
                obj_str = (
                    f", obj={scheduling_result.objective}"
                    if scheduling_result.objective is not None
                    else ""
                )
                print(
                    f"{scheduling_result.status} "
                    f"(xcsp: vars={scheduling_result.n_vars}, ctrs={scheduling_result.n_constraints} | "
                    f"sched: ivars={scheduling_result.n_interval_vars}, seqs={scheduling_result.n_sequences}, "
                    f"time={scheduling_result.solve_time:.2f}s{obj_str})"
                )
                _print_error_details(scheduling_result)

                # Check objective match
                if (
                    classical_result.status == "OPTIMUM"
                    and scheduling_result.status == "OPTIMUM"
                    and classical_result.objective is not None
                    and scheduling_result.objective is not None
                ):
                    if classical_result.objective == scheduling_result.objective:
                        print(f"    Objectives match: {classical_result.objective}")
                    else:
                        print(
                            f"    WARNING: Objective mismatch! "
                            f"Classical={classical_result.objective}, "
                            f"Scheduling={scheduling_result.objective}"
                        )
                elif (
                    classical_result.objective is not None
                    and scheduling_result.objective is not None
                ):
                    better = compare_objective_values(
                        classical_result.objective,
                        scheduling_result.objective,
                    )
                    better_label = (
                        "Classical"
                        if better == "classical"
                        else ("Scheduling" if better == "scheduling" else "Tie")
                    )
                    print(
                        "    Objective snapshot: "
                        f"Classical={classical_result.objective} [{classical_result.status}], "
                        f"Scheduling={scheduling_result.objective} [{scheduling_result.status}] "
                        f"-> Better={better_label}"
                    )

    # Save results
    timestamp = now_iso().replace(":", "-").replace(".", "-")
    results_file = output_dir / f"results_{args.suite}_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

    latest_file = output_dir / "results_latest.json"
    with open(latest_file, "w") as f:
        json.dump(results, f, indent=2)

    # Generate reports
    if args.no_report:
        print("\nSkipping report generation (--no-report).")
    else:
        print("\nGenerating reports...")
        generate_comparison_report(results, output_dir)

    print("\nDone!")


if __name__ == "__main__":
    main()
