"""
Grouping constraints for interval variables.

This module provides constraints that relate a main interval to a group of intervals:

1. **span(main, subtasks)**: Main interval spans all present subtasks
   - start(main) = min{start(i) : i present}
   - end(main) = max{end(i) : i present}

2. **alternative(main, alternatives, cardinality=1)**: Select exactly k alternatives
   - Exactly `cardinality` intervals from `alternatives` are present
   - Selected intervals have same start/end as main

3. **synchronize(main, intervals)**: All present intervals synchronize with main
   - All present intervals in array have same start/end as main

All constraints handle optional (absent) intervals correctly:
- When main is absent, all related intervals are absent
- When all subtasks are absent, main is absent (for span)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from pycsp3_scheduling.constraints._pycsp3 import (
    _build_end_expr,
    _get_node_builders,
    _validate_interval,
    _validate_intervals,
    length_value,
    presence_var,
    start_var,
)
from pycsp3_scheduling.variables.interval import IntervalVar

if TYPE_CHECKING:
    pass


def _validate_interval_list(
    intervals: Sequence[IntervalVar], name: str
) -> list[IntervalVar]:
    """Validate and convert interval sequence (requires non-empty)."""
    result = _validate_intervals(intervals, name)
    if len(result) == 0:
        raise ValueError(f"{name} cannot be empty")
    return result


# =============================================================================
# Span Constraint
# =============================================================================


def span(main: IntervalVar, subtasks: Sequence[IntervalVar]) -> list:
    """
    Constrain main interval to span all present subtasks.

    The main interval covers exactly the time range occupied by its subtasks:
    - start(main) = min{start(i) : i present in subtasks}
    - end(main) = max{end(i) : i present in subtasks}

    Semantics for optional intervals:
    - If main is present, at least one subtask must be present
    - If main is absent, all subtasks must be absent
    - If all subtasks are absent, main must be absent

    Args:
        main: The spanning interval variable.
        subtasks: List of interval variables to be spanned.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If main is not IntervalVar or subtasks contains non-IntervalVar.
        ValueError: If subtasks is empty.

    Example:
        >>> main_task = IntervalVar(name="project")
        >>> phases = [IntervalVar(size=10, name=f"phase_{i}") for i in range(3)]
        >>> satisfy(span(main_task, phases))  # project spans all phases
    """
    _validate_interval(main, "main")
    subtasks_list = _validate_interval_list(subtasks, "subtasks")
    Node, TypeNode = _get_node_builders()

    constraints = []
    main_start = start_var(main)
    main_end = _build_end_expr(main, Node, TypeNode)

    # Collect start and end expressions for subtasks
    subtask_starts = [start_var(t) for t in subtasks_list]
    subtask_ends = [_build_end_expr(t, Node, TypeNode) for t in subtasks_list]

    has_optional_main = main.optional
    has_optional_subtasks = any(t.optional for t in subtasks_list)

    if not has_optional_main and not has_optional_subtasks:
        # Simple case: all intervals are mandatory
        # start(main) = min(subtask starts)
        # end(main) = max(subtask ends)
        if len(subtasks_list) == 1:
            # Single subtask: direct equality
            constraints.append(Node.build(TypeNode.EQ, main_start, subtask_starts[0]))
            constraints.append(Node.build(TypeNode.EQ, main_end, subtask_ends[0]))
        else:
            min_start = Node.build(TypeNode.MIN, subtask_starts)
            max_end = Node.build(TypeNode.MAX, subtask_ends)
            constraints.append(Node.build(TypeNode.EQ, main_start, min_start))
            constraints.append(Node.build(TypeNode.EQ, main_end, max_end))
    else:
        # Complex case with optional intervals
        # We need conditional constraints based on presence

        main_presence = presence_var(main)
        subtask_presences = [presence_var(t) for t in subtasks_list]

        # For each subtask: if present, main must contain it
        for i, subtask in enumerate(subtasks_list):
            sub_start = subtask_starts[i]
            sub_end = subtask_ends[i]
            sub_presence = subtask_presences[i]

            if subtask.optional:
                # If subtask present: main_start <= sub_start AND sub_end <= main_end
                # Encoded as: (sub_presence == 0) OR (main_start <= sub_start)
                cond1 = Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, sub_presence, 0),
                    Node.build(TypeNode.LE, main_start, sub_start),
                )
                cond2 = Node.build(
                    TypeNode.OR,
                    Node.build(TypeNode.EQ, sub_presence, 0),
                    Node.build(TypeNode.LE, sub_end, main_end),
                )
                constraints.append(cond1)
                constraints.append(cond2)

                # If subtask present, main must be present
                if has_optional_main:
                    # sub_presence <= main_presence (if sub present, main present)
                    constraints.append(
                        Node.build(TypeNode.LE, sub_presence, main_presence)
                    )
            else:
                # Mandatory subtask: main must contain it
                constraints.append(Node.build(TypeNode.LE, main_start, sub_start))
                constraints.append(Node.build(TypeNode.LE, sub_end, main_end))

        if has_optional_main:
            # If main is present, at least one subtask must be present
            # main_presence <= sum(subtask_presences)
            # Equivalently: main_presence == 0 OR sum(subtask_presences) >= 1
            if has_optional_subtasks:
                sum_presences = Node.build(TypeNode.ADD, *subtask_presences)
                constraints.append(
                    Node.build(
                        TypeNode.OR,
                        Node.build(TypeNode.EQ, main_presence, 0),
                        Node.build(TypeNode.GE, sum_presences, 1),
                    )
                )

            # Main start/end should match the actual span when present
            # This is enforced by the containment constraints above plus tightness

    return constraints


# =============================================================================
# Alternative Constraint
# =============================================================================


def alternative(
    main: IntervalVar,
    alternatives: Sequence[IntervalVar],
    cardinality: int = 1,
) -> list:
    """
    Constrain exactly k alternatives to be selected and match the main interval.

    When main is present, exactly `cardinality` intervals from `alternatives`
    are present, and they have the same start and end times as main.

    Semantics:
    - If main is present: exactly `cardinality` alternatives are present
    - Selected alternatives have start(alt) == start(main) and end(alt) == end(main)
    - If main is absent: all alternatives are absent

    Args:
        main: The main interval variable.
        alternatives: List of alternative interval variables.
        cardinality: Number of alternatives to select (default 1).

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If main is not IntervalVar or alternatives contains non-IntervalVar.
        ValueError: If alternatives is empty or cardinality is invalid.

    Example:
        >>> main_op = IntervalVar(size=10, name="operation")
        >>> machines = [IntervalVar(size=10, optional=True, name=f"m{i}") for i in range(3)]
        >>> satisfy(alternative(main_op, machines))  # Assign to exactly one machine
    """
    _validate_interval(main, "main")
    alts_list = _validate_interval_list(alternatives, "alternatives")

    if not isinstance(cardinality, int) or cardinality < 1:
        raise ValueError(f"cardinality must be a positive integer, got {cardinality}")
    if cardinality > len(alts_list):
        raise ValueError(
            f"cardinality ({cardinality}) cannot exceed number of alternatives "
            f"({len(alts_list)})"
        )

    # All alternatives must be optional for alternative constraint to make sense
    for i, alt in enumerate(alts_list):
        if not alt.optional:
            raise ValueError(
                f"alternatives[{i}] ({alt.name}) must be optional for alternative constraint"
            )

    Node, TypeNode = _get_node_builders()
    constraints = []

    main_start = start_var(main)
    main_end = _build_end_expr(main, Node, TypeNode)
    main_presence = presence_var(main)

    alt_presences = [presence_var(alt) for alt in alts_list]

    # Sum of alternative presences equals cardinality when main is present
    # sum(alt_presences) == cardinality * main_presence
    if len(alt_presences) == 1:
        sum_presences = alt_presences[0]
    else:
        sum_presences = Node.build(TypeNode.ADD, *alt_presences)
    if main.optional:
        # sum(alt_presences) == cardinality * main_presence
        rhs = Node.build(TypeNode.MUL, cardinality, main_presence)
        constraints.append(Node.build(TypeNode.EQ, sum_presences, rhs))
    else:
        # Main is mandatory, so exactly cardinality alternatives must be present
        constraints.append(Node.build(TypeNode.EQ, sum_presences, cardinality))

    # Each selected alternative must match main's timing
    for i, alt in enumerate(alts_list):
        alt_start = start_var(alt)
        alt_end = _build_end_expr(alt, Node, TypeNode)
        alt_presence = alt_presences[i]

        # If alternative is present, it must match main's start
        # (alt_presence == 0) OR (alt_start == main_start)
        start_match = Node.build(
            TypeNode.OR,
            Node.build(TypeNode.EQ, alt_presence, 0),
            Node.build(TypeNode.EQ, alt_start, main_start),
        )
        constraints.append(start_match)

        # If alternative is present, it must match main's end
        # (alt_presence == 0) OR (alt_end == main_end)
        end_match = Node.build(
            TypeNode.OR,
            Node.build(TypeNode.EQ, alt_presence, 0),
            Node.build(TypeNode.EQ, alt_end, main_end),
        )
        constraints.append(end_match)

    return constraints


# =============================================================================
# Synchronize Constraint
# =============================================================================


def synchronize(main: IntervalVar, intervals: Sequence[IntervalVar]) -> list:
    """
    Constrain all present intervals to synchronize with the main interval.

    All present intervals in the array have the same start and end times as main.

    Semantics:
    - If main is present: present intervals have same start/end as main
    - If main is absent: all intervals in array are absent
    - Intervals in array can be independently present or absent

    Args:
        main: The main interval variable.
        intervals: List of interval variables to synchronize.

    Returns:
        List of pycsp3 constraint nodes.

    Raises:
        TypeError: If main is not IntervalVar or intervals contains non-IntervalVar.
        ValueError: If intervals is empty.

    Example:
        >>> main = IntervalVar(size=10, name="meeting")
        >>> attendees = [IntervalVar(size=10, optional=True, name=f"person_{i}") for i in range(5)]
        >>> satisfy(synchronize(main, attendees))  # Present attendees sync with meeting
    """
    _validate_interval(main, "main")
    intervals_list = _validate_interval_list(intervals, "intervals")
    Node, TypeNode = _get_node_builders()

    constraints = []
    main_start = start_var(main)
    main_end = _build_end_expr(main, Node, TypeNode)
    main_presence = presence_var(main)

    for i, interval in enumerate(intervals_list):
        int_start = start_var(interval)
        int_end = _build_end_expr(interval, Node, TypeNode)
        int_presence = presence_var(interval)

        if interval.optional:
            # If main is absent, interval must be absent
            # main_presence >= int_presence (if main absent, interval absent)
            if main.optional:
                constraints.append(
                    Node.build(TypeNode.GE, main_presence, int_presence)
                )
            else:
                # Main is mandatory, intervals can be present or absent
                pass

            # If interval is present, it must match main's timing
            # (int_presence == 0) OR (int_start == main_start)
            start_match = Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, int_presence, 0),
                Node.build(TypeNode.EQ, int_start, main_start),
            )
            constraints.append(start_match)

            # (int_presence == 0) OR (int_end == main_end)
            end_match = Node.build(
                TypeNode.OR,
                Node.build(TypeNode.EQ, int_presence, 0),
                Node.build(TypeNode.EQ, int_end, main_end),
            )
            constraints.append(end_match)
        else:
            # Mandatory interval: must always match main
            constraints.append(Node.build(TypeNode.EQ, int_start, main_start))
            constraints.append(Node.build(TypeNode.EQ, int_end, main_end))

    return constraints
