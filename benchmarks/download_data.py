#!/usr/bin/env python3
"""
Data Download and Preparation Script

Downloads and prepares benchmark data from various sources:
- Extracts XCSP ZIP files in PyCSP3-models
- Downloads PSPLIB instances (RCPSP)
- Converts PSPLIB .sm format to JSON
- Converts AircraftLanding OR-Library .txt instances to JSON
- Converts CyclicRCPSP .dzn instances to JSON
- Converts SchedulingOS .dzn instances and copies xcsp25 JSON instances
- Converts MRCPSP .dzn instances to JSON
- Converts MSPSP .dzn instances to JSON
- Syncs data to classical model directories
- Auto-updates config.yaml with discovered instances
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import ssl
import urllib.request
import zipfile
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

# Create SSL context that doesn't verify certificates (for PSPLIB)
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CONFIG_PATH = PROJECT_ROOT / "benchmarks" / "config.yaml"

PSPLIB_URL = "https://www.om-db.wi.tum.de/psplib/files"


def extract_xcsp_zips(verbose: bool = True) -> int:
    """
    Extract all *.zip files in PyCSP3-models/realistic/*/data/.

    Returns:
        Number of files extracted.
    """
    pycsp3_models = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic"
    count = 0

    for zip_path in pycsp3_models.rglob("*.zip"):
        # Determine extraction directory
        extract_dir = zip_path.parent / zip_path.stem
        if extract_dir.exists():
            if verbose:
                print(f"  Already extracted: {zip_path.name}")
            continue

        try:
            if verbose:
                print(f"  Extracting: {zip_path}")
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(zip_path.parent)
            count += 1
        except zipfile.BadZipFile:
            print(f"  Warning: Bad ZIP file: {zip_path}")

    return count


def download_psplib(output_dir: Path, verbose: bool = True) -> int:
    """
    Download PSPLIB RCPSP instances (j30, j60, j90, j120).

    Returns:
        Number of files downloaded.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for setname in ["j30", "j60", "j90", "j120"]:
        url = f"{PSPLIB_URL}/{setname}.sm.zip"
        dest = output_dir / f"{setname}.sm.zip"

        if dest.exists():
            if verbose:
                print(f"  Already downloaded: {setname}.sm.zip")
            continue

        try:
            if verbose:
                print(f"  Downloading: {url}")
            # Use SSL context to handle certificate issues
            with urllib.request.urlopen(url, context=SSL_CONTEXT) as response:
                with open(dest, "wb") as f:
                    f.write(response.read())

            # Extract
            extract_dir = output_dir / setname
            extract_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(dest, "r") as z:
                z.extractall(extract_dir)
            count += 1
            if verbose:
                print(f"  Extracted: {setname}")
        except Exception as e:
            print(f"  Warning: Failed to download {setname}: {e}")

    return count


def parse_psplib_sm(sm_file: Path) -> dict | None:
    """
    Parse PSPLIB .sm format file.

    The .sm format structure:
    - Line 1-4: Header info
    - Line 5: #jobs (including dummy start/end), #resources
    - Line 6: horizon (often dummy)
    - Line 7: #renewable resources
    - Line 8: #nonrenewable resources
    - Line 9: #doubly constrained (usually 0)
    - Then precedence section
    - Then duration/resource usage section
    - Then resource availabilities

    Returns:
        Dictionary with jobs, horizon, renewable, or None if parsing fails.
    """
    try:
        with open(sm_file, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = [line.strip() for line in content.split("\n") if line.strip()]

        # Find key sections by looking for markers
        # Look for "jobs" line to get job count
        n_jobs = None
        n_resources = None
        horizon = None

        for i, line in enumerate(lines):
            if "jobs" in line.lower() and ":" in line:
                # Format: "jobs (incl. supersource/sink ):  32"
                match = re.search(r":\s*(\d+)", line)
                if match:
                    n_jobs = int(match.group(1))
            elif "horizon" in line.lower() and ":" in line:
                match = re.search(r":\s*(\d+)", line)
                if match:
                    horizon = int(match.group(1))
            elif "renewable" in line.lower() and ":" in line and n_resources is None:
                match = re.search(r":\s*(\d+)", line)
                if match:
                    n_resources = int(match.group(1))

        if n_jobs is None:
            return None

        # Find PRECEDENCE RELATIONS section
        prec_start = None
        for i, line in enumerate(lines):
            if "PRECEDENCE RELATIONS" in line.upper():
                prec_start = i + 2  # Skip header line
                break

        if prec_start is None:
            return None

        # Parse precedence: jobnr, #modes, #successors, successors...
        precedences = []
        for i in range(n_jobs):
            if prec_start + i >= len(lines):
                break
            parts = lines[prec_start + i].split()
            if len(parts) < 3:
                continue
            job_nr = int(parts[0])
            n_modes = int(parts[1])
            n_successors = int(parts[2])
            successors = [int(parts[3 + j]) - 1 for j in range(n_successors)]  # 0-indexed
            precedences.append({
                "job_nr": job_nr,
                "n_modes": n_modes,
                "successors": successors
            })

        # Find REQUESTS/DURATIONS section
        req_start = None
        for i, line in enumerate(lines):
            if "REQUESTS/DURATIONS" in line.upper():
                req_start = i + 3  # Skip header lines
                break

        if req_start is None:
            return None

        # Parse requests: jobnr, mode, duration, R1, R2, ...
        requests = []
        for i in range(n_jobs):
            if req_start + i >= len(lines):
                break
            parts = lines[req_start + i].split()
            if len(parts) < 3:
                continue
            job_nr = int(parts[0])
            mode = int(parts[1])
            duration = int(parts[2])
            usages = [int(parts[3 + j]) for j in range(len(parts) - 3)]
            requests.append({
                "job_nr": job_nr,
                "duration": duration,
                "usages": usages
            })

        # Find RESOURCE AVAILABILITIES section
        avail_start = None
        for i, line in enumerate(lines):
            if "RESOURCEAVAILABILITIES" in line.upper().replace(" ", ""):
                avail_start = i + 2  # Skip header line
                break

        capacities = []
        if avail_start is not None and avail_start < len(lines):
            parts = lines[avail_start].split()
            capacities = [int(x) for x in parts]

        # Build jobs list
        jobs = []
        for i in range(n_jobs):
            prec = precedences[i] if i < len(precedences) else {"successors": []}
            req = requests[i] if i < len(requests) else {"duration": 0, "usages": []}

            jobs.append({
                "duration": req["duration"],
                "successors": prec["successors"],
                "usages": req["usages"][:n_resources] if n_resources else req["usages"]
            })

        # Calculate horizon if not provided
        if horizon is None or horizon == 0:
            horizon = sum(j["duration"] for j in jobs)

        return {
            "jobs": jobs,
            "horizon": horizon,
            "renewable": capacities[:n_resources] if n_resources else capacities,
            "unrewable": []
        }

    except Exception as e:
        print(f"  Error parsing {sm_file.name}: {e}")
        return None


def convert_psplib_to_json(psplib_dir: Path, output_dir: Path, verbose: bool = True, limit: int = 10) -> int:
    """
    Convert PSPLIB .sm files to JSON format.

    Args:
        psplib_dir: Directory containing PSPLIB .sm files
        output_dir: Directory to write JSON files
        verbose: Print progress
        limit: Max files to convert per set (0 = all)

    Returns:
        Number of files converted.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for setname in ["j30", "j60", "j90", "j120"]:
        set_dir = psplib_dir / setname
        if not set_dir.exists():
            continue

        sm_files = sorted(set_dir.glob("*.sm"))
        if limit > 0:
            sm_files = sm_files[:limit]

        for sm_file in sm_files:
            json_file = output_dir / f"{sm_file.stem}.json"
            if json_file.exists():
                continue

            data = parse_psplib_sm(sm_file)
            if data is None:
                if verbose:
                    print(f"  Failed to parse: {sm_file.name}")
                continue

            with open(json_file, "w") as f:
                json.dump(data, f, indent=2)

            if verbose:
                print(f"  Converted: {sm_file.name} -> {json_file.name}")
            count += 1

    return count


def parse_airland_txt(txt_file: Path) -> dict | None:
    """
    Parse OR-Library Aircraft Landing .txt format to JSON structure.

    Format:
    - nPlanes freezing_time
    - For each plane:
      appearance earliest target latest early_penalty late_penalty
      followed by nPlanes separation integers
    """
    try:
        tokens = txt_file.read_text(encoding="utf-8", errors="ignore").split()
        if len(tokens) < 2:
            return None

        idx = 0
        n_planes = int(tokens[idx])
        idx += 1
        _freezing_time = int(tokens[idx])  # unused by the current model
        idx += 1

        times = []
        costs = []
        separations = []

        for _ in range(n_planes):
            _appearance_time = int(tokens[idx])  # unused by the current model
            idx += 1
            earliest = int(tokens[idx])
            idx += 1
            target = int(tokens[idx])
            idx += 1
            latest = int(tokens[idx])
            idx += 1
            early_penalty = int(float(tokens[idx]) * 100)
            idx += 1
            late_penalty = int(float(tokens[idx]) * 100)
            idx += 1

            sep = [int(tokens[idx + j]) for j in range(n_planes)]
            idx += n_planes

            times.append({"earliest": earliest, "target": target, "latest": latest})
            costs.append({"early_penalty": early_penalty, "late_penalty": late_penalty})
            separations.append(sep)

        if len(times) != n_planes or len(separations) != n_planes:
            return None

        return {
            "P": n_planes,
            "times": times,
            "costs": costs,
            "separations": separations,
        }
    except Exception as e:
        print(f"  Error parsing {txt_file.name}: {e}")
        return None


def convert_airlands_to_json(source_dir: Path, output_dir: Path, verbose: bool = True) -> int:
    """
    Convert AircraftLanding OR-Library .txt instances to JSON files.

    Returns:
        Number of files converted.
    """
    if not source_dir.exists():
        if verbose:
            print(f"  Source directory not found: {source_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for txt_file in sorted(source_dir.glob("airland*.txt")):
        json_file = output_dir / f"{txt_file.stem}.json"
        if json_file.exists():
            continue

        data = parse_airland_txt(txt_file)
        if data is None:
            if verbose:
                print(f"  Failed to parse: {txt_file.name}")
            continue

        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        if verbose:
            print(f"  Converted: {txt_file.name} -> {json_file.name}")
        count += 1

    return count


def parse_cyclic_rcpsp_dzn(dzn_file: Path) -> dict | None:
    """
    Parse CyclicRCPSP .dzn instances to JSON structure.

    Expected fields: n_res, rcap, n_tasks, rreq, n_prec, prec.
    """
    try:
        content = dzn_file.read_text(encoding="utf-8", errors="ignore")
        content = "\n".join(line.split("%", 1)[0] for line in content.splitlines())
        assignments = {k: v.strip() for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);", content, re.DOTALL)}

        required = ("n_res", "rcap", "n_tasks", "rreq", "n_prec", "prec")
        missing = [name for name in required if name not in assignments]
        if missing:
            print(f"  Missing fields in {dzn_file.name}: {', '.join(missing)}")
            return None

        def parse_int_list(expr: str) -> list[int]:
            expr = expr.strip()
            if not (expr.startswith("[") and expr.endswith("]")):
                raise ValueError(f"Expected list expression, got: {expr[:30]}")
            return [int(tok.strip()) for tok in expr[1:-1].split(",") if tok.strip()]

        def parse_matrix(expr: str) -> list[list[int]]:
            expr = expr.strip()
            if not (expr.startswith("[|") and expr.endswith("|]")):
                raise ValueError(f"Expected matrix expression, got: {expr[:30]}")
            rows_raw = [row.strip() for row in expr[2:-2].split("|") if row.strip()]
            rows = []
            for row in rows_raw:
                values = [int(tok.strip()) for tok in row.split(",") if tok.strip()]
                rows.append(values)
            return rows

        n_res = int(assignments["n_res"])
        capacities = parse_int_list(assignments["rcap"])
        n_tasks = int(assignments["n_tasks"])
        requirements = parse_matrix(assignments["rreq"])
        n_prec = int(assignments["n_prec"])
        precedences = parse_matrix(assignments["prec"])

        if len(capacities) != n_res:
            raise ValueError(f"Expected {n_res} capacities, found {len(capacities)}")
        if len(requirements) != n_tasks:
            raise ValueError(f"Expected {n_tasks} requirement rows, found {len(requirements)}")
        if any(len(row) != n_res for row in requirements):
            raise ValueError("Requirement matrix has invalid row width")
        if len(precedences) != n_prec:
            raise ValueError(f"Expected {n_prec} precedence rows, found {len(precedences)}")
        if any(len(row) != 4 for row in precedences):
            raise ValueError("Precedence matrix rows must have 4 integers")

        precedences = [[i - 1, j - 1, latency, distance] for i, j, latency, distance in precedences]
        if any(latency < 0 for _, _, latency, _ in precedences):
            raise ValueError("Found negative precedence latency")

        return {
            "capacities": capacities,
            "requirements": requirements,
            "precedences": precedences,
        }
    except Exception as e:
        print(f"  Error parsing {dzn_file.name}: {e}")
        return None


def convert_cyclic_rcpsp_to_json(source_dir: Path, output_dir: Path, verbose: bool = True) -> int:
    """
    Convert CyclicRCPSP .dzn instances to JSON files.

    Returns:
        Number of files converted.
    """
    if not source_dir.exists():
        if verbose:
            print(f"  Source directory not found: {source_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for dzn_file in sorted(source_dir.glob("*.dzn")):
        json_name = f"{dzn_file.stem.replace('_', '-')}.json"
        json_file = output_dir / json_name
        if json_file.exists():
            continue

        data = parse_cyclic_rcpsp_dzn(dzn_file)
        if data is None:
            if verbose:
                print(f"  Failed to parse: {dzn_file.name}")
            continue

        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        if verbose:
            print(f"  Converted: {dzn_file.name} -> {json_file.name}")
        count += 1

    return count


def parse_scheduling_os_dzn(dzn_file: Path) -> list[list[int]] | None:
    """
    Parse SchedulingOS .dzn instances into a durations matrix.

    Expected fields: n_jobs, n_machines, job_task_duration=array2d(jobs,tasks,[...]).
    """
    try:
        content = dzn_file.read_text(encoding="utf-8", errors="ignore")
        content = "\n".join(line.split("%", 1)[0] for line in content.splitlines())
        assignments = {k: v.strip() for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);", content, re.DOTALL)}

        required = ("n_jobs", "n_machines", "job_task_duration")
        missing = [name for name in required if name not in assignments]
        if missing:
            print(f"  Missing fields in {dzn_file.name}: {', '.join(missing)}")
            return None

        n_jobs = int(assignments["n_jobs"])
        n_machines = int(assignments["n_machines"])

        array_expr = assignments["job_task_duration"]
        match = re.search(r"array2d\s*\(\s*jobs\s*,\s*tasks\s*,\s*\[(.*)\]\s*\)\s*$", array_expr, re.DOTALL)
        if not match:
            raise ValueError("Unsupported job_task_duration expression")
        flat = [int(tok.strip()) for tok in match.group(1).split(",") if tok.strip()]

        expected = n_jobs * n_machines
        if len(flat) != expected:
            raise ValueError(f"Expected {expected} durations, found {len(flat)}")

        return [flat[i * n_machines:(i + 1) * n_machines] for i in range(n_jobs)]
    except Exception as e:
        print(f"  Error parsing {dzn_file.name}: {e}")
        return None


def convert_scheduling_os_data(source_dir: Path, output_dir: Path, verbose: bool = True) -> int:
    """
    Convert SchedulingOS datasets:
    - root .dzn files are converted to .json
    - xcsp25/*.json files are copied and normalized to matrix format

    Returns:
        Number of files written.
    """
    if not source_dir.exists():
        if verbose:
            print(f"  Source directory not found: {source_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for dzn_file in sorted(source_dir.glob("*.dzn")):
        json_file = output_dir / f"{dzn_file.stem}.json"
        if json_file.exists():
            continue

        durations = parse_scheduling_os_dzn(dzn_file)
        if durations is None:
            if verbose:
                print(f"  Failed to parse: {dzn_file.name}")
            continue

        with open(json_file, "w") as f:
            json.dump(durations, f, indent=2)
            f.write("\n")
        if verbose:
            print(f"  Converted: {dzn_file.name} -> {json_file.name}")
        count += 1

    xcsp25_dir = source_dir / "xcsp25"
    if xcsp25_dir.exists():
        for src_json in sorted(xcsp25_dir.glob("*.json")):
            dst_json = output_dir / src_json.name
            if dst_json.exists():
                continue

            payload = json.loads(src_json.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and "durations" in payload:
                payload = payload["durations"]

            with open(dst_json, "w") as f:
                json.dump(payload, f, indent=2)
                f.write("\n")
            if verbose:
                print(f"  Copied: {src_json.name} -> {dst_json.name}")
            count += 1

    return count


def parse_mrcpsp_dzn(dzn_file: Path) -> dict | None:
    """
    Parse MRCPSP .dzn instances to JSON structure.

    Expected fields: n_res, rcap, rtype, n_tasks, modes, succ, n_opt, dur, rreq.
    """
    try:
        content = dzn_file.read_text(encoding="utf-8", errors="ignore")
        content = "\n".join(line.split("%", 1)[0] for line in content.splitlines())
        assignments = {k: v.strip() for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);", content, re.DOTALL)}

        required = ("n_res", "rcap", "rtype", "n_tasks", "modes", "succ", "n_opt", "dur", "rreq")
        missing = [name for name in required if name not in assignments]
        if missing:
            print(f"  Missing fields in {dzn_file.name}: {', '.join(missing)}")
            return None

        def parse_int_list(expr: str) -> list[int]:
            expr = expr.strip()
            if not (expr.startswith("[") and expr.endswith("]")):
                raise ValueError(f"Expected list expression, got: {expr[:30]}")
            return [int(tok.strip()) for tok in expr[1:-1].split(",") if tok.strip()]

        def parse_set_list(expr: str) -> list[list[int]]:
            expr = expr.strip()
            if not (expr.startswith("[") and expr.endswith("]")):
                raise ValueError(f"Expected set-list expression, got: {expr[:30]}")
            sets = []
            for m in re.finditer(r"\{([^{}]*)\}", expr):
                inner = m.group(1).strip()
                values = [] if not inner else [int(tok.strip()) for tok in inner.split(",") if tok.strip()]
                sets.append(values)
            return sets

        def parse_matrix(expr: str) -> list[list[int]]:
            expr = expr.strip()
            if not (expr.startswith("[|") and expr.endswith("|]")):
                raise ValueError(f"Expected matrix expression, got: {expr[:30]}")
            rows_raw = [row.strip() for row in expr[2:-2].split("|") if row.strip()]
            rows = []
            for row in rows_raw:
                values = [int(tok.strip()) for tok in row.split(",") if tok.strip()]
                rows.append(values)
            return rows

        n_res = int(assignments["n_res"])
        capacities = parse_int_list(assignments["rcap"])
        types = parse_int_list(assignments["rtype"])
        n_tasks = int(assignments["n_tasks"])
        modes = parse_set_list(assignments["modes"])
        successors = parse_set_list(assignments["succ"])
        n_opt = int(assignments["n_opt"])
        mode_durations = parse_int_list(assignments["dur"])
        requirements = parse_matrix(assignments["rreq"])

        if len(capacities) != n_res or len(types) != n_res:
            raise ValueError("Resource capacities/types length mismatch")
        if len(modes) != n_tasks or len(successors) != n_tasks:
            raise ValueError("Tasks modes/successors length mismatch")
        if len(mode_durations) != n_opt:
            raise ValueError(f"Expected {n_opt} mode durations, found {len(mode_durations)}")
        if len(requirements) != n_res:
            raise ValueError(f"Expected {n_res} requirement rows, found {len(requirements)}")
        if any(len(row) != n_opt for row in requirements):
            raise ValueError("Requirement matrix has invalid row width")

        modes = [[v - 1 for v in row] for row in modes]
        successors = [[v - 1 for v in row] for row in successors]

        return {
            "resources": {
                "capacities": capacities,
                "types": types,
            },
            "mode_durations": mode_durations,
            "tasks": {
                "modes": modes,
                "successors": successors,
                "requirements": requirements,
            },
        }
    except Exception as e:
        print(f"  Error parsing {dzn_file.name}: {e}")
        return None


def _mrcpsp_json_name_from_dzn(dzn_stem: str) -> str:
    match = re.match(r"^(j\d+)_(\d+)_(\d+)$", dzn_stem)
    if match:
        prefix, a, b = match.groups()
        return f"{prefix}-{int(a):02d}-{int(b):02d}.json"
    return f"{dzn_stem.replace('_', '-')}.json"


def convert_mrcpsp_to_json(source_dir: Path, output_dir: Path, verbose: bool = True) -> int:
    """
    Convert MRCPSP .dzn instances to JSON files.

    Returns:
        Number of files converted.
    """
    if not source_dir.exists():
        if verbose:
            print(f"  Source directory not found: {source_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for dzn_file in sorted(source_dir.glob("*.dzn")):
        json_file = output_dir / _mrcpsp_json_name_from_dzn(dzn_file.stem)
        if json_file.exists():
            continue

        payload = parse_mrcpsp_dzn(dzn_file)
        if payload is None:
            if verbose:
                print(f"  Failed to parse: {dzn_file.name}")
            continue

        with open(json_file, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        if verbose:
            print(f"  Converted: {dzn_file.name} -> {json_file.name}")
        count += 1

    return count


def parse_mspsp_dzn(dzn_file: Path) -> dict | None:
    """
    Parse MSPSP .dzn instances to JSON structure.

    Expected fields: n_skills, n_workers, has_skills, n_tasks, d, rr, suc.
    """
    try:
        content = dzn_file.read_text(encoding="utf-8", errors="ignore")
        content = "\n".join(line.split("%", 1)[0] for line in content.splitlines())
        assignments = {k: v.strip() for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?);", content, re.DOTALL)}

        required = ("n_skills", "n_workers", "has_skills", "n_tasks", "d", "rr", "suc")
        missing = [name for name in required if name not in assignments]
        if missing:
            print(f"  Missing fields in {dzn_file.name}: {', '.join(missing)}")
            return None

        def parse_int_list(expr: str) -> list[int]:
            expr = expr.strip()
            if not (expr.startswith("[") and expr.endswith("]")):
                raise ValueError(f"Expected list expression, got: {expr[:30]}")
            return [int(tok.strip()) for tok in expr[1:-1].split(",") if tok.strip()]

        def parse_set_list(expr: str) -> list[list[int]]:
            expr = expr.strip()
            if not (expr.startswith("[") and expr.endswith("]")):
                raise ValueError(f"Expected set-list expression, got: {expr[:30]}")
            sets = []
            for m in re.finditer(r"\{([^{}]*)\}", expr):
                inner = m.group(1).strip()
                values = [] if not inner else [int(tok.strip()) for tok in inner.split(",") if tok.strip()]
                sets.append(values)
            return sets

        def parse_matrix(expr: str) -> list[list[int]]:
            expr = expr.strip()
            if not (expr.startswith("[|") and expr.endswith("|]")):
                raise ValueError(f"Expected matrix expression, got: {expr[:30]}")
            rows_raw = [row.strip() for row in expr[2:-2].split("|") if row.strip()]
            rows = []
            for row in rows_raw:
                values = [int(tok.strip()) for tok in row.split(",") if tok.strip()]
                rows.append(values)
            return rows

        n_skills = int(assignments["n_skills"])
        n_workers = int(assignments["n_workers"])
        skills = parse_set_list(assignments["has_skills"])
        n_tasks = int(assignments["n_tasks"])
        durations = parse_int_list(assignments["d"])
        requirements = parse_matrix(assignments["rr"])
        successors = parse_set_list(assignments["suc"])

        if len(skills) != n_workers:
            raise ValueError(f"Expected {n_workers} workers, found {len(skills)}")
        if len(durations) != n_tasks:
            raise ValueError(f"Expected {n_tasks} durations, found {len(durations)}")
        if len(requirements) != n_skills:
            raise ValueError(f"Expected {n_skills} requirement rows, found {len(requirements)}")
        if any(len(row) != n_tasks for row in requirements):
            raise ValueError("Requirement matrix has invalid row width")
        if len(successors) != n_tasks:
            raise ValueError(f"Expected {n_tasks} successor rows, found {len(successors)}")

        skills = [[v - 1 for v in row] for row in skills]
        successors = [[v - 1 for v in row] for row in successors]

        return {
            "skills": skills,
            "durations": durations,
            "requirements": requirements,
            "successors": successors,
        }
    except Exception as e:
        print(f"  Error parsing {dzn_file.name}: {e}")
        return None


def _mspsp_json_name_from_dzn(dzn_stem: str) -> str:
    return f"{dzn_stem.replace('_', '-')}.json"


def convert_mspsp_to_json(source_dir: Path, output_dir: Path, verbose: bool = True) -> int:
    """
    Convert MSPSP .dzn instances to JSON files.

    Returns:
        Number of files converted.
    """
    if not source_dir.exists():
        if verbose:
            print(f"  Source directory not found: {source_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    for dzn_file in sorted(source_dir.glob("*.dzn")):
        json_file = output_dir / _mspsp_json_name_from_dzn(dzn_file.stem)
        if json_file.exists():
            continue

        payload = parse_mspsp_dzn(dzn_file)
        if payload is None:
            if verbose:
                print(f"  Failed to parse: {dzn_file.name}")
            continue

        with open(json_file, "w") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        if verbose:
            print(f"  Converted: {dzn_file.name} -> {json_file.name}")
        count += 1

    return count


def sync_data_to_classical(verbose: bool = True) -> int:
    """
    Sync JSON data files from scheduling models to classical model directories.

    Creates symlinks (or copies on Windows) so classical models can find the data.

    Returns:
        Number of files synced.
    """
    scheduling_models = PROJECT_ROOT / "examples" / "models" / "realistic"
    classical_models = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic"
    count = 0

    for scheduling_data_dir in scheduling_models.glob("*/data"):
        model_name = scheduling_data_dir.parent.name

        # Find corresponding classical model directory
        classical_model_dir = classical_models / model_name
        if not classical_model_dir.exists():
            # Try common name mappings
            mappings = {
                "SchedulingOS": "SchedulingOS",
                "SchedulingJS": "SchedulingJS",
                "SchedulingFS": "SchedulingFS",
            }
            mapped_name = mappings.get(model_name)
            if mapped_name:
                classical_model_dir = classical_models / mapped_name

        if not classical_model_dir.exists():
            if verbose:
                print(f"  No classical model found for: {model_name}")
            continue

        # Create data directory in classical if needed
        classical_data_dir = classical_model_dir / "data"
        classical_data_dir.mkdir(exist_ok=True)

        # Sync JSON files
        for json_file in scheduling_data_dir.glob("*.json"):
            dest = classical_data_dir / json_file.name
            if dest.exists():
                continue

            try:
                # Try symlink first (faster, saves space)
                dest.symlink_to(json_file.resolve())
                if verbose:
                    print(f"  Linked: {json_file.name} -> {classical_model_dir.name}/data/")
                count += 1
            except OSError:
                # Fall back to copy on Windows or permission issues
                shutil.copy(json_file, dest)
                if verbose:
                    print(f"  Copied: {json_file.name} -> {classical_model_dir.name}/data/")
                count += 1

    return count


def discover_model_pairs() -> dict[str, dict]:
    """
    Discover all model pairs that have both classical and scheduling versions.

    Returns:
        Dictionary mapping model name to configuration.
    """
    scheduling_models = PROJECT_ROOT / "examples" / "models" / "realistic"
    classical_models = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic"

    pairs = {}

    for scheduling_dir in sorted(scheduling_models.iterdir()):
        if not scheduling_dir.is_dir():
            continue

        model_name = scheduling_dir.name
        scheduling_py = scheduling_dir / f"{model_name}.py"
        scheduling_data = scheduling_dir / "data"

        if not scheduling_py.exists():
            continue

        # Find classical counterpart
        classical_dir = classical_models / model_name
        if not classical_dir.exists():
            continue

        classical_py = classical_dir / f"{model_name}.py"
        if not classical_py.exists():
            continue

        # Collect instances
        instances = []
        if scheduling_data.exists():
            instances = sorted([f.name for f in scheduling_data.glob("*.json")])

        if not instances:
            continue

        pairs[model_name] = {
            "classical": f"examples/PyCSP3-models/realistic/{model_name}/{model_name}.py",
            "scheduling": f"examples/models/realistic/{model_name}/{model_name}.py",
            "data_dir": f"examples/models/realistic/{model_name}/data",
            "instances": instances
        }

    return pairs


def update_config(verbose: bool = True) -> int:
    """
    Update config.yaml with all discovered model pairs and instances.

    Returns:
        Number of models updated.
    """
    if yaml is None:
        raise RuntimeError("PyYAML is required for --update-config (try: uv run python benchmarks/download_data.py --update-config)")

    # Load existing config
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {}

    # Preserve settings and suites
    settings = config.get("settings", {
        "timeout": 300,
        "repetitions": 1,
        "solver": "ace"
    })
    suites = config.get("suites", {
        "quick": {
            "models": "all",
            "instances_per_model": 1,
            "repetitions": 1,
            "timeout": 60
        },
        "full": {
            "models": "all",
            "instances_per_model": "all",
            "repetitions": 3,
            "timeout": 300
        }
    })

    # Discover model pairs
    pairs = discover_model_pairs()

    if verbose:
        print(f"  Discovered {len(pairs)} model pairs:")
        for name, cfg in pairs.items():
            print(f"    {name}: {len(cfg['instances'])} instances")

    # Build new config
    new_config = {
        "models": pairs,
        "settings": settings,
        "suites": suites
    }

    # Write config with nice formatting
    with open(CONFIG_PATH, "w") as f:
        f.write("# Benchmark Configuration for pycsp3-scheduling comparison\n")
        f.write("# Auto-generated by download_data.py --update-config\n")
        f.write("# Compares classical pycsp3 models vs pycsp3-scheduling models\n\n")
        yaml.dump(new_config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return len(pairs)


def list_available_data(verbose: bool = True) -> None:
    """List all available benchmark data files."""
    if yaml is None:
        raise RuntimeError("PyYAML is required for --list (try: uv run python benchmarks/download_data.py --list)")

    scheduling_models = PROJECT_ROOT / "examples" / "models" / "realistic"
    classical_models = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic"
    psplib_dir = PROJECT_ROOT / "examples" / "data" / "psplib"

    def count_files(directory: Path, pattern: str = "*.json") -> tuple[list[Path], int]:
        """Count files matching pattern in directory."""
        files = sorted(directory.glob(pattern)) if directory.exists() else []
        return files, len(files)

    def print_files(files: list[Path], max_show: int = 5) -> None:
        """Print file list with truncation."""
        for f in files[:max_show]:
            print(f"    - {f.name}")
        if len(files) > max_show:
            print(f"    ... and {len(files) - max_show} more")

    # Scheduling Models
    print("\n" + "=" * 60)
    print("SCHEDULING MODELS (examples/models/realistic/)")
    print("=" * 60)

    total_scheduling = 0
    for model_dir in sorted(scheduling_models.iterdir()):
        if not model_dir.is_dir():
            continue

        data_dir = model_dir / "data"
        json_files, count = count_files(data_dir, "*.json")
        if count > 0:
            print(f"\n  {model_dir.name}: ({count} instances)")
            print_files(json_files)
            total_scheduling += count

    print(f"\n  Total: {total_scheduling} instances")

    # Classical Models
    print("\n" + "=" * 60)
    print("CLASSICAL MODELS (examples/PyCSP3-models/realistic/)")
    print("=" * 60)

    total_classical = 0
    for model_dir in sorted(classical_models.iterdir()):
        if not model_dir.is_dir():
            continue

        data_dir = model_dir / "data"
        if not data_dir.exists():
            continue

        # Count JSON files
        json_files, json_count = count_files(data_dir, "*.json")

        # Count extracted XCSP directories (from ZIP files)
        xcsp_dirs = [d for d in data_dir.iterdir() if d.is_dir()]
        xcsp_count = 0
        for xcsp_dir in xcsp_dirs:
            xcsp_files = list(xcsp_dir.glob("*.xml")) + list(xcsp_dir.glob("*.json"))
            xcsp_count += len(xcsp_files)

        # Count ZIP files (not yet extracted)
        zip_files, zip_count = count_files(data_dir, "*.zip")

        total = json_count + xcsp_count
        if total > 0 or zip_count > 0:
            extras = []
            if xcsp_count > 0:
                extras.append(f"{xcsp_count} in subdirs")
            if zip_count > 0:
                extras.append(f"{zip_count} zips")
            extra_str = f" + {', '.join(extras)}" if extras else ""

            print(f"\n  {model_dir.name}: ({json_count} JSON{extra_str})")
            if json_files:
                print_files(json_files)
            for xcsp_dir in xcsp_dirs[:3]:
                subfiles = list(xcsp_dir.glob("*.xml")) + list(xcsp_dir.glob("*.json"))
                if subfiles:
                    print(f"    [{xcsp_dir.name}/]: {len(subfiles)} files")
            if len(xcsp_dirs) > 3:
                print(f"    ... and {len(xcsp_dirs) - 3} more directories")

            total_classical += total

    print(f"\n  Total: {total_classical} instances")

    # PSPLIB
    print("\n" + "=" * 60)
    print("PSPLIB DATA (examples/data/psplib/)")
    print("=" * 60)

    total_psplib = 0
    if psplib_dir.exists():
        for setname in ["j30", "j60", "j90", "j120"]:
            set_dir = psplib_dir / setname
            if set_dir.exists():
                sm_files = list(set_dir.glob("*.sm"))
                json_files = list(set_dir.glob("*.json"))
                extras = f" ({len(json_files)} converted)" if json_files else ""
                print(f"\n  {setname}: ({len(sm_files)} .sm files{extras})")
                total_psplib += len(sm_files)
        print(f"\n  Total: {total_psplib} instances")
    else:
        print("\n  Not downloaded. Run: --psplib to download")

    # Config status
    print("\n" + "=" * 60)
    print("CONFIG STATUS")
    print("=" * 60)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
        models = config.get("models", {})
        total_config_instances = sum(len(m.get("instances", [])) for m in models.values())
        print(f"\n  Models in config: {len(models)}")
        print(f"  Instances in config: {total_config_instances}")
        print("\n  Run --update-config to refresh")
    else:
        print("\n  Config not found. Run --update-config to create")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Scheduling model instances: {total_scheduling}")
    print(f"  Classical model instances:  {total_classical}")
    if psplib_dir.exists():
        print(f"  PSPLIB instances:           {total_psplib}")


def main():
    parser = argparse.ArgumentParser(
        description="Download and prepare benchmark data"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Perform all data preparation steps (extract, download, sync, update-config)",
    )
    parser.add_argument(
        "--extract-zips",
        action="store_true",
        help="Extract XCSP ZIP files in PyCSP3-models",
    )
    parser.add_argument(
        "--psplib",
        action="store_true",
        help="Download PSPLIB RCPSP instances",
    )
    parser.add_argument(
        "--convert-psplib",
        action="store_true",
        help="Convert PSPLIB .sm files to JSON",
    )
    parser.add_argument(
        "--psplib-limit",
        type=int,
        default=10,
        help="Max PSPLIB instances to convert per set (0=all, default=10)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Sync data files to classical model directories",
    )
    parser.add_argument(
        "--convert-airlands",
        action="store_true",
        help="Convert AircraftLanding OR-Library .txt files to JSON",
    )
    parser.add_argument(
        "--convert-cyclic-rcpsp",
        action="store_true",
        help="Convert CyclicRCPSP .dzn files to JSON",
    )
    parser.add_argument(
        "--convert-scheduling-os",
        action="store_true",
        help="Convert SchedulingOS .dzn and copy xcsp25 JSON files",
    )
    parser.add_argument(
        "--convert-mrcpsp",
        action="store_true",
        help="Convert MRCPSP .dzn files to JSON",
    )
    parser.add_argument(
        "--convert-mspsp",
        action="store_true",
        help="Convert MSPSP .dzn files to JSON",
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Update config.yaml with discovered model pairs and instances",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available benchmark data",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output",
    )
    args = parser.parse_args()

    verbose = not args.quiet

    if args.list:
        list_available_data(verbose)
        return 0

    # If no specific action, show help
    if not (args.all or args.extract_zips or args.psplib or args.convert_psplib
            or args.convert_airlands or args.convert_cyclic_rcpsp
            or args.convert_scheduling_os or args.convert_mrcpsp or args.convert_mspsp
            or args.sync or args.update_config):
        parser.print_help()
        print("\nTip: Use --all to perform all preparation steps")
        return 0

    # Perform requested actions
    if args.all or args.extract_zips:
        print("\nExtracting XCSP ZIP files...")
        count = extract_xcsp_zips(verbose)
        print(f"  Extracted {count} new files")

    if args.all or args.psplib:
        print("\nDownloading PSPLIB instances...")
        output_dir = PROJECT_ROOT / "examples" / "data" / "psplib"
        count = download_psplib(output_dir, verbose)
        print(f"  Downloaded {count} new files")

    if args.all or args.convert_psplib:
        print("\nConverting PSPLIB .sm files to JSON...")
        psplib_dir = PROJECT_ROOT / "examples" / "data" / "psplib"
        rcpsp_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "RCPSP" / "data"
        limit = 0 if args.all else args.psplib_limit
        count = convert_psplib_to_json(psplib_dir, rcpsp_data, verbose, limit=limit)
        print(f"  Converted {count} new files")

    if args.all or args.convert_airlands:
        print("\nConverting AircraftLanding airlands .txt files to JSON...")
        airlands_src = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic" / "AircraftLanding" / "data" / "airlands"
        aircraft_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "AircraftLanding" / "data"
        count = convert_airlands_to_json(airlands_src, aircraft_data, verbose)
        print(f"  Converted {count} new files")

    if args.all or args.convert_cyclic_rcpsp:
        print("\nConverting CyclicRCPSP .dzn files to JSON...")
        cyclic_src = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic" / "CyclicRCPSP" / "data"
        cyclic_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "CyclicRCPSP" / "data"
        count = convert_cyclic_rcpsp_to_json(cyclic_src, cyclic_data, verbose)
        print(f"  Converted {count} new files")

    if args.all or args.convert_scheduling_os:
        print("\nConverting SchedulingOS data files...")
        scheduling_os_src = PROJECT_ROOT / "examples" / "PyCSP3-models" / "realistic" / "SchedulingOS" / "data"
        scheduling_os_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "SchedulingOS" / "data"
        count = convert_scheduling_os_data(scheduling_os_src, scheduling_os_data, verbose)
        print(f"  Converted/Copied {count} new files")

    if args.all or args.convert_mrcpsp:
        print("\nConverting MRCPSP .dzn files to JSON...")
        mrcpsp_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "MRCPSP" / "data"
        count = convert_mrcpsp_to_json(mrcpsp_data, mrcpsp_data, verbose)
        print(f"  Converted {count} new files")

    if args.all or args.convert_mspsp:
        print("\nConverting MSPSP .dzn files to JSON...")
        mspsp_data = PROJECT_ROOT / "examples" / "models" / "realistic" / "MSPSP" / "data"
        count = convert_mspsp_to_json(mspsp_data, mspsp_data, verbose)
        print(f"  Converted {count} new files")

    if args.all or args.sync:
        print("\nSyncing data to classical model directories...")
        count = sync_data_to_classical(verbose)
        print(f"  Synced {count} new files")

    if args.all or args.update_config:
        print("\nUpdating config.yaml...")
        count = update_config(verbose)
        print(f"  Config updated with {count} model pairs")

    print("\nData preparation complete!")
    return 0


if __name__ == "__main__":
    exit(main())
