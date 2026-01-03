"""
Helpers for bridging IntervalVar objects to pycsp3 variables.

This module handles the translation of high-level IntervalVar scheduling objects
into low-level pycsp3 integer variables and constraints that can be exported to
XCSP3 XML format.

Key concepts:
- Each IntervalVar is decomposed into integer variables: start, length, presence
- Intensity functions (variable work rates) are discretized into table constraints
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pycsp3_scheduling.variables.interval import (
    INTERVAL_MAX,
    INTERVAL_MIN,
    IntervalVar,
    Step,
    get_registered_intervals,
)

if TYPE_CHECKING:
    from pycsp3.classes.main.variables import Variable

_start_vars: dict[IntervalVar, Any] = {}
_length_vars: dict[IntervalVar, Any] = {}
_presence_vars: dict[IntervalVar, Any] = {}
# Track which intervals have had their intensity constraints posted
_intensity_constraints_posted: set[IntervalVar] = set()


# =============================================================================
# INTENSITY FUNCTION DISCRETIZATION
# =============================================================================
#
# Intensity functions model variable work rates over time. They relate three
# quantities for an interval:
#
#   - size: the amount of "work" to be done (e.g., 10 units of processing)
#   - length: the elapsed time (e.g., 20 time units)
#   - intensity: the work rate at each time point (0 to granularity)
#
# The fundamental equation is:
#
#   size * granularity = sum of intensity(t) for t in [start, start + length)
#
# Example: A task with size=10 and granularity=100
#   - At 100% intensity (value=100): length = 10 (10 * 100 = 10 * 100)
#   - At 50% intensity (value=50): length = 20 (10 * 100 = 20 * 50)
#
# For XCSP3, we discretize this relationship into a table constraint that
# maps (start, size) -> length, precomputing valid combinations.
# =============================================================================


def _intensity_at(steps: list[Step], t: int) -> int:
    """
    Evaluate the stepwise intensity function at time t.

    A stepwise function is defined by a list of (x, value) pairs where:
    - The function equals 0 for t < first step's x
    - The function equals the step's value for t >= step's x until the next step

    Example:
        steps = [(5, 80), (10, 50)]
        - t < 5: returns 0 (default before first step)
        - 5 <= t < 10: returns 80
        - t >= 10: returns 50

    Args:
        steps: List of (x, value) pairs defining the stepwise function.
               Must be sorted by x in strictly increasing order.
        t: The time point to evaluate.

    Returns:
        The intensity value at time t.
    """
    # Default intensity is 0 before the first step
    result = 0

    # Walk through steps to find the applicable value
    # Each step sets the value from its x position onwards
    for x, value in steps:
        if t >= x:
            result = value
        else:
            # Steps are sorted, so we can stop once t < x
            break

    return result


def _integrate_intensity(steps: list[Step], start: int, end: int) -> int:
    """
    Compute the integral (sum) of intensity over the interval [start, end).

    For discrete time, this is the sum of intensity(t) for t in [start, end).
    This represents the total "work" that can be done in this time window.

    Example:
        steps = [(0, 100), (10, 50)]  # 100% until t=10, then 50%
        _integrate_intensity(steps, 0, 20) = 10*100 + 10*50 = 1500

    The algorithm walks through time, accumulating intensity values.
    For efficiency with large ranges, it processes step boundaries
    rather than iterating over every time point.

    Args:
        steps: The stepwise intensity function.
        start: Start of the integration interval (inclusive).
        end: End of the integration interval (exclusive).

    Returns:
        The sum of intensity values over [start, end).
    """
    if end <= start:
        return 0

    # Build a list of "change points" where intensity changes
    # Include start and end to properly bound the integration
    change_points = [start]
    for x, _ in steps:
        if start < x < end:
            change_points.append(x)
    change_points.append(end)

    # Remove duplicates and sort
    change_points = sorted(set(change_points))

    # Integrate segment by segment
    # Between change points, intensity is constant
    total = 0
    for i in range(len(change_points) - 1):
        seg_start = change_points[i]
        seg_end = change_points[i + 1]
        # Intensity is constant in this segment, evaluate at segment start
        intensity = _intensity_at(steps, seg_start)
        # Add contribution: intensity * segment_length
        total += intensity * (seg_end - seg_start)

    return total


def _find_length_for_work(
    steps: list[Step],
    start: int,
    target_work: int,
    max_length: int,
) -> int | None:
    """
    Find the length needed to complete target_work starting at time start.

    Given the intensity function, we need to find length such that:
        sum of intensity(t) for t in [start, start + length) = target_work

    This is the inverse of integration: given the target integral, find the
    upper bound of the integration interval.

    Algorithm:
        We incrementally extend the interval until we accumulate enough work.
        For efficiency, we jump between step boundaries rather than iterating
        one time unit at a time.

    Args:
        steps: The stepwise intensity function.
        start: The start time of the interval.
        target_work: The work to complete (size * granularity).
        max_length: Maximum allowed length (to bound the search).

    Returns:
        The length needed, or None if target_work cannot be achieved
        within max_length (e.g., if intensity is 0).
    """
    if target_work <= 0:
        return 0

    # Build list of step boundaries after start
    future_steps = [(x, val) for x, val in steps if x > start]
    future_steps.sort()

    accumulated_work = 0
    current_pos = start

    # Process segment by segment
    while current_pos < start + max_length:
        # Find intensity at current position
        current_intensity = _intensity_at(steps, current_pos)

        # Find the next change point (either a step boundary or max_length)
        next_boundary = start + max_length
        for x, _ in future_steps:
            if x > current_pos:
                next_boundary = min(next_boundary, x)
                break

        # How much work can we do in this segment?
        segment_length = next_boundary - current_pos
        segment_work = current_intensity * segment_length

        # Check if we can finish within this segment
        remaining_work = target_work - accumulated_work
        if current_intensity > 0 and segment_work >= remaining_work:
            # We can finish in this segment
            # Find exact length: remaining_work = current_intensity * extra_length
            # extra_length = remaining_work / current_intensity (ceiling division)
            extra_length = (remaining_work + current_intensity - 1) // current_intensity
            return current_pos - start + extra_length

        # Accumulate and move to next segment
        accumulated_work += segment_work
        current_pos = next_boundary

        # Remove processed step from future_steps
        future_steps = [(x, val) for x, val in future_steps if x > current_pos]

    # Couldn't complete the work within max_length
    return None


def _compute_intensity_table(
    interval: IntervalVar,
    horizon: int,
) -> list[tuple[int, int, int]] | list[tuple[int, int]] | None:
    """
    Compute the discretized (start, [size,] length) table for an interval with intensity.

    This is the core discretization function. For each valid (start, size) combination,
    it computes the required length to complete the work given the intensity function.

    The relationship is:
        size * granularity = integral of intensity over [start, start + length)

    For fixed size intervals, returns list of (start, length) tuples.
    For variable size intervals, returns list of (start, size, length) tuples.

    Args:
        interval: The interval variable with intensity function.
        horizon: The scheduling horizon (max end time).

    Returns:
        List of valid tuples, or None if no intensity function is defined.
    """
    if interval.intensity is None:
        return None

    steps = interval.intensity
    granularity = interval.granularity

    # Determine the domain bounds
    start_min = interval.start_min
    start_max = min(interval.start_max, horizon)
    size_min = interval.size_min
    size_max = interval.size_max
    length_max = interval.length_max

    # Check if size is fixed (common case, more efficient)
    size_is_fixed = size_min == size_max

    table: list[tuple[int, ...]] = []

    if size_is_fixed:
        # Fixed size: compute (start, length) pairs
        size = size_min
        target_work = size * granularity

        for start in range(start_min, start_max + 1):
            length = _find_length_for_work(steps, start, target_work, length_max)
            if length is not None:
                # Verify the length is within bounds
                if interval.length_min <= length <= length_max:
                    # Verify end time is within horizon
                    if start + length <= horizon:
                        table.append((start, length))
    else:
        # Variable size: compute (start, size, length) triples
        for start in range(start_min, start_max + 1):
            for size in range(size_min, size_max + 1):
                target_work = size * granularity
                length = _find_length_for_work(steps, start, target_work, length_max)
                if length is not None:
                    if interval.length_min <= length <= length_max:
                        if start + length <= horizon:
                            table.append((start, size, length))

    return table


def _post_intensity_constraint(interval: IntervalVar, horizon: int) -> None:
    """
    Post the table constraint linking start, size, and length via intensity.

    This creates a pycsp3 table constraint (extension constraint) that restricts
    the valid combinations of (start, length) or (start, size, length) based on
    the intensity function.

    The constraint is only posted once per interval (tracked via _intensity_constraints_posted).

    For XCSP3, this becomes an <extension> constraint with <supports> listing
    all valid tuples:

        <extension>
            <list> start length </list>
            <supports> (0,12)(1,12)(2,13)... </supports>
        </extension>

    Args:
        interval: The interval variable with intensity function.
        horizon: The scheduling horizon.
    """
    if interval in _intensity_constraints_posted:
        return
    if interval.intensity is None:
        return

    # Import pycsp3 functions for posting constraints
    # pycsp3 uses Table() for table/extension constraints
    try:
        from pycsp3 import Table, satisfy
    except ImportError:
        return

    # Compute the discretized table
    table = _compute_intensity_table(interval, horizon)
    if not table:
        # No valid combinations - this interval is infeasible
        # Post a false constraint to signal infeasibility
        satisfy(False)
        _intensity_constraints_posted.add(interval)
        return

    # Get the variables
    start = start_var(interval)
    length = length_var(interval)

    # Check if we need size variable
    size_is_fixed = interval.size_min == interval.size_max

    if size_is_fixed:
        # Table is (start, length) pairs
        # Use pycsp3 Table constraint with the list of valid tuples
        satisfy(
            Table(
                scope=[start, length],
                supports=table,
            )
        )
    else:
        # Table is (start, size, length) triples
        # We need a size variable
        Var, _ = _require_pycsp3()
        size = Var(
            dom=range(interval.size_min, interval.size_max + 1),
            id=_var_id("iv_sz_", interval),
        )
        satisfy(
            Table(
                scope=[start, size, length],
                supports=table,
            )
        )

    _intensity_constraints_posted.add(interval)


def _var_id(prefix: str, interval: IntervalVar) -> str:
    return f"{prefix}{interval._id}"


def _default_horizon(intervals: list[IntervalVar]) -> int:
    horizon = 0
    for interval in intervals:
        if interval.end_max != INTERVAL_MAX:
            horizon = max(horizon, interval.end_max)
        elif interval.start_max != INTERVAL_MAX:
            horizon = max(horizon, interval.start_max + interval.length_max)
        else:
            horizon += interval.length_max
    return max(horizon, 0)


def _range_from_bounds(min_val: int, max_val: int, horizon: int) -> range:
    if max_val == INTERVAL_MAX:
        max_val = horizon
    if max_val < min_val:
        max_val = min_val
    return range(min_val, max_val + 1)


def _ensure_options(options) -> None:
    if hasattr(options, "checker"):
        return
    options.set_values(
        "data",
        "dataparser",
        "dataexport",
        "dataformat",
        "variant",
        "tocsp",
        "checker",
        "solver",
        "output",
        "suffix",
        "callback",
    )
    options.set_flags(
        "dataexport",
        "datasober",
        "solve",
        "display",
        "verbose",
        "lzma",
        "sober",
        "ev",
        "safe",
        "recognizeSlides",
        "keepHybrid",
        "keepSmartTransitions",
        "keepsum",
        "unchangescalar",
        "restrictTablesWrtDomains",
        "dontruncompactor",
        "dontcompactValues",
        "groupsumcoeffs",
        "usemeta",
        "dontuseauxcache",
        "dontadjustindexing",
        "dontbuildsimilarconstraints",
        "debug",
        "mini",
        "uncurse",
        "existbyelement",
        "safetables",
    )
    if options.checker is None:
        options.checker = "fast"


def _require_pycsp3():
    try:
        from pycsp3 import Var
        from pycsp3.dashboard import options
        from pycsp3.classes.main.variables import Variable
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise ImportError(
            "pycsp3 is required to build scheduling constraints. "
            "Install a compatible version and Python runtime."
        ) from exc
    _ensure_options(options)
    return Var, Variable


def presence_var(interval: IntervalVar) -> Any:
    """Return (or create) a pycsp3 boolean variable for the interval presence."""
    if not interval.optional:
        # Non-optional intervals are always present - return constant 1
        return 1
    if interval in _presence_vars:
        return _presence_vars[interval]
    Var, _ = _require_pycsp3()
    var = Var(dom={0, 1}, id=_var_id("iv_p_", interval))
    _presence_vars[interval] = var
    return var


def start_var(interval: IntervalVar) -> Any:
    """Return (or create) a pycsp3 variable for the interval start time."""
    if interval in _start_vars:
        return _start_vars[interval]
    Var, _ = _require_pycsp3()
    intervals = get_registered_intervals() or [interval]
    horizon = _default_horizon(intervals)
    dom = _range_from_bounds(interval.start_min, interval.start_max, horizon)
    var = Var(dom=dom, id=_var_id("iv_s_", interval))
    _start_vars[interval] = var
    return var


def length_var(interval: IntervalVar) -> Any:
    """
    Return (or create) a pycsp3 variable for the interval length.

    Unlike length_value(), this always returns a variable, never a constant.
    This is needed for intensity constraints where length must be a variable
    to participate in table constraints.

    If the interval has an intensity function, this also triggers posting
    the intensity discretization constraint linking start and length.

    Args:
        interval: The interval variable.

    Returns:
        A pycsp3 variable representing the length.
    """
    if interval in _length_vars:
        return _length_vars[interval]

    Var, _ = _require_pycsp3()

    # For intervals with intensity, the length domain may need adjustment
    # based on what's actually achievable given the intensity function
    if interval.intensity is not None:
        # Compute the valid lengths from the intensity table
        intervals = get_registered_intervals() or [interval]
        horizon = _default_horizon(intervals)
        table = _compute_intensity_table(interval, horizon)

        if table:
            # Extract valid lengths from the table
            # Table is either (start, length) or (start, size, length)
            size_is_fixed = interval.size_min == interval.size_max
            if size_is_fixed:
                valid_lengths = sorted(set(t[1] for t in table))
            else:
                valid_lengths = sorted(set(t[2] for t in table))
            dom = set(valid_lengths)
        else:
            # No valid combinations, use full range (will be infeasible)
            dom = range(interval.length_min, interval.length_max + 1)
    else:
        dom = range(interval.length_min, interval.length_max + 1)

    var = Var(dom=dom, id=_var_id("iv_l_", interval))
    _length_vars[interval] = var

    # Post intensity constraint if applicable
    # This links the start and length variables via the intensity function
    if interval.intensity is not None:
        intervals = get_registered_intervals() or [interval]
        horizon = _default_horizon(intervals)
        _post_intensity_constraint(interval, horizon)

    return var


def length_value(interval: IntervalVar) -> Any:
    """
    Return a fixed length or a pycsp3 variable for interval length.

    This is the main entry point for getting the length of an interval.
    It returns:
    - An integer constant if length is fixed AND no intensity function is defined
    - A pycsp3 variable otherwise

    When an intensity function is defined, length becomes a decision variable
    because it depends on where the interval is scheduled (the start time).

    Args:
        interval: The interval variable.

    Returns:
        Either an integer (fixed length) or a pycsp3 variable.
    """
    # If intensity is defined, length depends on start, so we need a variable
    # even if length bounds are fixed, because the actual length varies with start
    if interval.intensity is not None:
        return length_var(interval)

    # No intensity: check if length is fixed
    if interval.length_min == interval.length_max:
        return interval.length_min

    # Variable length without intensity
    return length_var(interval)


def clear_pycsp3_cache() -> None:
    """Clear cached pycsp3 variables and constraints for intervals."""
    _start_vars.clear()
    _length_vars.clear()
    _presence_vars.clear()
    _intensity_constraints_posted.clear()
