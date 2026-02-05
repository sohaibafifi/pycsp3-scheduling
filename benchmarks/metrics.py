"""
Metrics collection utilities for benchmark comparison.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

SUCCESS_STATUSES = {"SAT", "OPTIMUM", "UNSAT"}
OBJECTIVE_STATUSES = {"OPTIMUM"}
# For incumbent quality, objective snapshots are meaningful on these statuses.
OBJECTIVE_SNAPSHOT_STATUSES = {"SAT", "OPTIMUM", "TIMEOUT"}


def compare_objective_values(
    classical_objective: int, scheduling_objective: int
) -> str:
    """
    Compare objective values (minimization convention).

    Returns:
        "classical", "scheduling", or "tie"
    """
    if classical_objective < scheduling_objective:
        return "classical"
    if scheduling_objective < classical_objective:
        return "scheduling"
    return "tie"


@dataclass
class RunResult:
    """Result of a single benchmark run."""

    model_type: str  # "classical" or "scheduling"
    model_name: str
    instance: str
    status: str
    objective: int | None = None
    solve_time: float = 0.0
    build_time: float = 0.0
    total_time: float = 0.0
    n_vars: int = 0
    n_constraints: int = 0
    constraint_types: dict[str, int] = field(default_factory=dict)
    # Scheduling-specific metrics
    n_interval_vars: int = 0
    n_optional_intervals: int = 0
    n_sequences: int = 0
    n_cumul_functions: int = 0
    n_state_functions: int = 0
    # Code metrics
    loc: int = 0
    # Error info
    error: str | None = None
    # Metadata
    timestamp: str = ""
    repetition: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RunResult":
        """Create from dictionary."""
        return cls(**d)


@dataclass
class ComparisonResult:
    """Comparison between classical and scheduling versions."""

    model_name: str
    instance: str
    instance_count: int = 1
    # Classical metrics
    classical_vars: int = 0
    classical_constraints: int = 0
    classical_solve_time: float = 0.0
    classical_build_time: float = 0.0
    classical_total_time: float = 0.0
    classical_objective: float | None = None
    classical_status: str = ""
    classical_loc: int = 0
    # Scheduling metrics
    scheduling_vars: int = 0
    scheduling_constraints: int = 0
    scheduling_solve_time: float = 0.0
    scheduling_build_time: float = 0.0
    scheduling_total_time: float = 0.0
    scheduling_objective: float | None = None
    scheduling_status: str = ""
    scheduling_loc: int = 0
    scheduling_interval_vars: int = 0
    scheduling_sequences: int = 0
    # Derived metrics
    var_augmentation: float = 0.0
    constraint_augmentation: float = 0.0
    solve_speedup: float = 0.0
    total_speedup: float = 0.0
    loc_reduction: float = 0.0
    statuses_comparable: bool = False
    objective_snapshot_comparable: bool = False
    objective_better: str | None = None
    objectives_comparable: bool = False
    objectives_match: bool | None = None

    @classmethod
    def from_runs(
        cls, classical: RunResult, scheduling: RunResult
    ) -> "ComparisonResult":
        """Create comparison from two run results."""
        # Calculate augmentations (positive = scheduling has more vars/constraints).
        var_augmentation = 0.0
        if classical.n_vars > 0:
            var_augmentation = scheduling.n_vars / classical.n_vars - 1

        constraint_augmentation = 0.0
        if classical.n_constraints > 0:
            constraint_augmentation = (
                scheduling.n_constraints / classical.n_constraints - 1
            )

        solve_speedup = 0.0
        if scheduling.solve_time > 0:
            solve_speedup = classical.solve_time / scheduling.solve_time

        total_speedup = 0.0
        if scheduling.total_time > 0:
            total_speedup = classical.total_time / scheduling.total_time

        loc_reduction = 0.0
        if classical.loc > 0:
            loc_reduction = 1 - scheduling.loc / classical.loc

        statuses_comparable = (
            classical.status in SUCCESS_STATUSES
            and scheduling.status in SUCCESS_STATUSES
        )
        objective_snapshot_comparable = (
            classical.status in OBJECTIVE_SNAPSHOT_STATUSES
            and scheduling.status in OBJECTIVE_SNAPSHOT_STATUSES
            and classical.objective is not None
            and scheduling.objective is not None
        )
        objective_better = (
            compare_objective_values(classical.objective, scheduling.objective)
            if objective_snapshot_comparable
            else None
        )
        objectives_comparable = (
            classical.status in OBJECTIVE_STATUSES
            and scheduling.status in OBJECTIVE_STATUSES
            and classical.objective is not None
            and scheduling.objective is not None
        )
        objectives_match = (
            classical.objective == scheduling.objective if objectives_comparable else None
        )

        return cls(
            model_name=classical.model_name,
            instance=classical.instance,
            instance_count=1,
            classical_vars=classical.n_vars,
            classical_constraints=classical.n_constraints,
            classical_solve_time=classical.solve_time,
            classical_build_time=classical.build_time,
            classical_total_time=classical.total_time,
            classical_objective=classical.objective,
            classical_status=classical.status,
            classical_loc=classical.loc,
            scheduling_vars=scheduling.n_vars,
            scheduling_constraints=scheduling.n_constraints,
            scheduling_solve_time=scheduling.solve_time,
            scheduling_build_time=scheduling.build_time,
            scheduling_total_time=scheduling.total_time,
            scheduling_objective=scheduling.objective,
            scheduling_status=scheduling.status,
            scheduling_loc=scheduling.loc,
            scheduling_interval_vars=scheduling.n_interval_vars,
            scheduling_sequences=scheduling.n_sequences,
            var_augmentation=var_augmentation,
            constraint_augmentation=constraint_augmentation,
            solve_speedup=solve_speedup,
            total_speedup=total_speedup,
            loc_reduction=loc_reduction,
            statuses_comparable=statuses_comparable,
            objective_snapshot_comparable=objective_snapshot_comparable,
            objective_better=objective_better,
            objectives_comparable=objectives_comparable,
            objectives_match=objectives_match,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def count_loc(file_path: str | Path) -> int:
    """Count non-empty, non-comment lines of code."""
    path = Path(file_path)
    if not path.exists():
        return 0

    loc = 0
    in_docstring = False
    docstring_char = None

    with open(path) as f:
        for line in f:
            stripped = line.strip()

            # Handle docstrings
            if not in_docstring:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    docstring_char = stripped[:3]
                    # Check if docstring ends on same line
                    if stripped.count(docstring_char) >= 2:
                        continue  # Skip single-line docstring
                    in_docstring = True
                    continue
            else:
                if docstring_char and docstring_char in stripped:
                    in_docstring = False
                    docstring_char = None
                continue

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue

            loc += 1

    return loc


def now_iso() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()
