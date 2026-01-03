"""
Cumulative functions for resource modeling in scheduling.

A cumulative function represents the usage of a resource over time.
It is built by summing elementary cumulative expressions:
- pulse(interval, height): Rectangular usage during interval
- step_at(time, height): Permanent step change at a time point
- step_at_start(interval, height): Step change at interval start
- step_at_end(interval, height): Step change at interval end

Cumulative functions can be constrained:
- cumul <= max_capacity: Never exceed capacity
- cumul >= min_level: Always maintain minimum level
- always_in(cumul, interval, min, max): Bound within time range

Example:
    >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
    >>> resource_usage = sum(pulse(t, height=2) for t in tasks)
    >>> satisfy(resource_usage <= 4)  # Capacity constraint
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Sequence, Union

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar


class CumulExprType(Enum):
    """Types of cumulative expressions."""

    PULSE = auto()  # Rectangular pulse during interval
    STEP_AT = auto()  # Step at fixed time
    STEP_AT_START = auto()  # Step at interval start
    STEP_AT_END = auto()  # Step at interval end
    SUM = auto()  # Sum of cumul expressions
    NEG = auto()  # Negation


@dataclass
class CumulExpr:
    """
    Elementary cumulative expression.

    Represents a contribution to a cumulative function from a single
    interval or time point.

    Attributes:
        expr_type: Type of cumulative expression.
        interval: Associated interval (for pulse, step_at_start, step_at_end).
        time: Fixed time point (for step_at).
        height: Fixed height value.
        height_min: Minimum height (for variable height).
        height_max: Maximum height (for variable height).
        operands: Child expressions (for SUM).
    """

    expr_type: CumulExprType
    interval: IntervalVar | None = None
    time: int | None = None
    height: int | None = None
    height_min: int | None = None
    height_max: int | None = None
    operands: list[CumulExpr] = field(default_factory=list)
    _id: int = field(default=-1, repr=False)

    def __post_init__(self) -> None:
        """Assign unique ID."""
        if self._id == -1:
            self._id = CumulExpr._get_next_id()

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID."""
        current = getattr(CumulExpr, "_id_counter", 0)
        CumulExpr._id_counter = current + 1
        return current

    @property
    def is_variable_height(self) -> bool:
        """Whether this expression has variable height."""
        return self.height_min is not None and self.height_min != self.height_max

    @property
    def fixed_height(self) -> int | None:
        """Return fixed height if constant, else None."""
        if self.height is not None:
            return self.height
        if self.height_min is not None and self.height_min == self.height_max:
            return self.height_min
        return None

    def __add__(self, other: Union[CumulExpr, CumulFunction, int]) -> CumulFunction:
        """Add cumulative expressions."""
        if isinstance(other, int):
            if other == 0:
                return CumulFunction(expressions=[self])
            raise TypeError("Cannot add non-zero integer to CumulExpr")
        if isinstance(other, CumulExpr):
            return CumulFunction(expressions=[self, other])
        if isinstance(other, CumulFunction):
            return CumulFunction(expressions=[self] + other.expressions)
        return NotImplemented

    def __radd__(self, other: Union[CumulExpr, CumulFunction, int]) -> CumulFunction:
        """Right addition (supports sum() starting with 0)."""
        if isinstance(other, int) and other == 0:
            return CumulFunction(expressions=[self])
        return self.__add__(other)

    def __neg__(self) -> CumulExpr:
        """Negate the cumulative expression."""
        return CumulExpr(
            expr_type=CumulExprType.NEG,
            operands=[self],
        )

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        if self.expr_type == CumulExprType.PULSE:
            name = self.interval.name if self.interval else "?"
            h = self.height if self.height is not None else f"[{self.height_min},{self.height_max}]"
            return f"pulse({name}, {h})"
        elif self.expr_type == CumulExprType.STEP_AT:
            return f"step_at({self.time}, {self.height})"
        elif self.expr_type == CumulExprType.STEP_AT_START:
            name = self.interval.name if self.interval else "?"
            h = self.height if self.height is not None else f"[{self.height_min},{self.height_max}]"
            return f"step_at_start({name}, {h})"
        elif self.expr_type == CumulExprType.STEP_AT_END:
            name = self.interval.name if self.interval else "?"
            h = self.height if self.height is not None else f"[{self.height_min},{self.height_max}]"
            return f"step_at_end({name}, {h})"
        elif self.expr_type == CumulExprType.NEG:
            return f"-({self.operands[0]})"
        elif self.expr_type == CumulExprType.SUM:
            return " + ".join(str(op) for op in self.operands)
        return f"CumulExpr({self.expr_type})"


@dataclass
class CumulFunction:
    """
    Cumulative function representing resource usage over time.

    A cumulative function is the sum of elementary cumulative expressions
    (pulse, step_at_start, step_at_end, step_at). It can be constrained
    using comparison operators.

    Attributes:
        expressions: List of elementary cumulative expressions.
        name: Optional name for the function.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> demands = [2, 3, 1]
        >>> usage = CumulFunction()
        >>> for task, d in zip(tasks, demands):
        ...     usage += pulse(task, d)
        >>> satisfy(usage <= 5)  # Capacity 5
    """

    expressions: list[CumulExpr] = field(default_factory=list)
    name: str | None = None
    _id: int = field(default=-1, repr=False)

    def __post_init__(self) -> None:
        """Assign unique ID."""
        if self._id == -1:
            self._id = CumulFunction._get_next_id()

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID."""
        current = getattr(CumulFunction, "_id_counter", 0)
        CumulFunction._id_counter = current + 1
        return current

    def __add__(self, other: Union[CumulExpr, CumulFunction, int]) -> CumulFunction:
        """Add cumulative expression or function."""
        if isinstance(other, int):
            if other == 0:
                return self
            raise TypeError("Cannot add non-zero integer to CumulFunction")
        if isinstance(other, CumulExpr):
            return CumulFunction(
                expressions=self.expressions + [other],
                name=self.name,
            )
        if isinstance(other, CumulFunction):
            return CumulFunction(
                expressions=self.expressions + other.expressions,
                name=self.name,
            )
        return NotImplemented

    def __radd__(self, other: Union[CumulExpr, CumulFunction, int]) -> CumulFunction:
        """Right addition (supports sum())."""
        if isinstance(other, int) and other == 0:
            return self
        return self.__add__(other)

    def __iadd__(self, other: Union[CumulExpr, CumulFunction]) -> CumulFunction:
        """In-place addition."""
        if isinstance(other, CumulExpr):
            self.expressions.append(other)
            return self
        if isinstance(other, CumulFunction):
            self.expressions.extend(other.expressions)
            return self
        return NotImplemented

    def __neg__(self) -> CumulFunction:
        """Negate all expressions."""
        return CumulFunction(
            expressions=[-expr for expr in self.expressions],
            name=self.name,
        )

    # Comparison operators for constraints
    def __le__(self, other: int):
        """cumul <= capacity constraint. Returns pycsp3-compatible constraint."""
        if not isinstance(other, int):
            raise TypeError(f"CumulFunction can only be compared with int, got {type(other)}")
        return self._build_capacity_constraint(other)

    def __ge__(self, other: int) -> CumulConstraint:
        """cumul >= level constraint."""
        if not isinstance(other, int):
            raise TypeError(f"CumulFunction can only be compared with int, got {type(other)}")
        return CumulConstraint(
            cumul=self,
            constraint_type=CumulConstraintType.GE,
            bound=other,
        )

    def __lt__(self, other: int) -> CumulConstraint:
        """cumul < bound constraint."""
        if not isinstance(other, int):
            raise TypeError(f"CumulFunction can only be compared with int, got {type(other)}")
        return CumulConstraint(
            cumul=self,
            constraint_type=CumulConstraintType.LT,
            bound=other,
        )

    def __gt__(self, other: int) -> CumulConstraint:
        """cumul > bound constraint."""
        if not isinstance(other, int):
            raise TypeError(f"CumulFunction can only be compared with int, got {type(other)}")
        return CumulConstraint(
            cumul=self,
            constraint_type=CumulConstraintType.GT,
            bound=other,
        )

    def _build_capacity_constraint(self, capacity: int):
        """
        Build pycsp3 Cumulative constraint for simple pulse-based functions.
        
        For cumulative functions that are sums of pulses with fixed heights,
        this returns a pycsp3 Cumulative constraint directly.
        """
        from pycsp3 import Cumulative
        from pycsp3_scheduling.constraints._pycsp3 import length_value, start_var
        
        # Check if all expressions are simple pulses
        intervals = []
        heights = []
        
        for expr in self.expressions:
            if expr.expr_type == CumulExprType.NEG:
                # Negated pulse
                if expr.operands and expr.operands[0].expr_type == CumulExprType.PULSE:
                    inner = expr.operands[0]
                    if inner.is_variable_height:
                        # Variable height not supported by simple Cumulative
                        return CumulConstraint(
                            cumul=self,
                            constraint_type=CumulConstraintType.LE,
                            bound=capacity,
                        )
                    intervals.append(inner.interval)
                    heights.append(-(inner.height or inner.height_min))
                else:
                    return CumulConstraint(
                        cumul=self,
                        constraint_type=CumulConstraintType.LE,
                        bound=capacity,
                    )
            elif expr.expr_type == CumulExprType.PULSE:
                if expr.is_variable_height:
                    return CumulConstraint(
                        cumul=self,
                        constraint_type=CumulConstraintType.LE,
                        bound=capacity,
                    )
                intervals.append(expr.interval)
                heights.append(expr.height or expr.height_min)
            else:
                # Non-pulse expression, fall back to CumulConstraint
                return CumulConstraint(
                    cumul=self,
                    constraint_type=CumulConstraintType.LE,
                    bound=capacity,
                )
        
        # Filter out negative heights (not supported by standard Cumulative)
        if any(h < 0 for h in heights):
            return CumulConstraint(
                cumul=self,
                constraint_type=CumulConstraintType.LE,
                bound=capacity,
            )
        
        # Filter out zero heights
        filtered = [(iv, h) for iv, h in zip(intervals, heights) if h > 0]
        if not filtered:
            # No actual resource usage, constraint is trivially satisfied
            return []
        
        intervals, heights = zip(*filtered)
        
        # Build pycsp3 Cumulative constraint
        origins = [start_var(iv) for iv in intervals]
        lengths = [length_value(iv) for iv in intervals]
        
        return Cumulative(origins=origins, lengths=lengths, heights=list(heights)) <= capacity

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        if self.name:
            return f"CumulFunction({self.name})"
        if not self.expressions:
            return "CumulFunction()"
        return f"CumulFunction({' + '.join(str(e) for e in self.expressions)})"

    def get_intervals(self) -> list[IntervalVar]:
        """Get all intervals referenced by this cumulative function."""
        intervals = []
        for expr in self.expressions:
            if expr.interval is not None:
                intervals.append(expr.interval)
            for op in expr.operands:
                if op.interval is not None:
                    intervals.append(op.interval)
        return intervals


class CumulConstraintType(Enum):
    """Types of cumulative constraints."""

    LE = auto()  # <=
    GE = auto()  # >=
    LT = auto()  # <
    GT = auto()  # >
    RANGE = auto()  # min <= cumul <= max
    ALWAYS_IN = auto()  # always_in over time range


@dataclass
class CumulConstraint:
    """
    Constraint on a cumulative function.

    Attributes:
        cumul: The cumulative function being constrained.
        constraint_type: Type of constraint (LE, GE, RANGE, etc.).
        bound: Upper or lower bound (for LE, GE, LT, GT).
        min_bound: Minimum bound (for RANGE, ALWAYS_IN).
        max_bound: Maximum bound (for RANGE, ALWAYS_IN).
        interval: Time interval for ALWAYS_IN constraint.
        start_time: Start time for fixed time range.
        end_time: End time for fixed time range.
    """

    cumul: CumulFunction
    constraint_type: CumulConstraintType
    bound: int | None = None
    min_bound: int | None = None
    max_bound: int | None = None
    interval: IntervalVar | None = None
    start_time: int | None = None
    end_time: int | None = None

    def __repr__(self) -> str:
        """String representation."""
        if self.constraint_type == CumulConstraintType.LE:
            return f"{self.cumul} <= {self.bound}"
        elif self.constraint_type == CumulConstraintType.GE:
            return f"{self.cumul} >= {self.bound}"
        elif self.constraint_type == CumulConstraintType.LT:
            return f"{self.cumul} < {self.bound}"
        elif self.constraint_type == CumulConstraintType.GT:
            return f"{self.cumul} > {self.bound}"
        elif self.constraint_type == CumulConstraintType.RANGE:
            return f"{self.min_bound} <= {self.cumul} <= {self.max_bound}"
        elif self.constraint_type == CumulConstraintType.ALWAYS_IN:
            if self.interval:
                return f"always_in({self.cumul}, {self.interval.name}, {self.min_bound}, {self.max_bound})"
            else:
                return f"always_in({self.cumul}, ({self.start_time}, {self.end_time}), {self.min_bound}, {self.max_bound})"
        return f"CumulConstraint({self.constraint_type})"


# =============================================================================
# Elementary Cumulative Functions
# =============================================================================


def pulse(
    interval: IntervalVar,
    height: int | None = None,
    height_min: int | None = None,
    height_max: int | None = None,
) -> CumulExpr:
    """
    Create a pulse contribution to a cumulative function.

    A pulse represents resource usage during the execution of an interval.
    The resource is consumed at the specified height from the start to
    the end of the interval.

    Args:
        interval: The interval variable.
        height: Fixed height (resource consumption).
        height_min: Minimum height for variable consumption.
        height_max: Maximum height for variable consumption.

    Returns:
        A CumulExpr representing the pulse.

    Raises:
        TypeError: If interval is not an IntervalVar.
        ValueError: If height specification is invalid.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> p = pulse(task, height=3)  # Fixed height 3
        >>> p = pulse(task, height_min=1, height_max=5)  # Variable height
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")

    # Validate height specification
    if height is not None:
        if height_min is not None or height_max is not None:
            raise ValueError("Cannot specify both height and height_min/height_max")
        if not isinstance(height, int):
            raise TypeError(f"height must be an int, got {type(height).__name__}")
        return CumulExpr(
            expr_type=CumulExprType.PULSE,
            interval=interval,
            height=height,
        )
    elif height_min is not None and height_max is not None:
        if not isinstance(height_min, int) or not isinstance(height_max, int):
            raise TypeError("height_min and height_max must be integers")
        if height_min > height_max:
            raise ValueError(f"height_min ({height_min}) cannot exceed height_max ({height_max})")
        return CumulExpr(
            expr_type=CumulExprType.PULSE,
            interval=interval,
            height_min=height_min,
            height_max=height_max,
        )
    else:
        raise ValueError("Must specify either height or both height_min and height_max")


def step_at(time: int, height: int) -> CumulExpr:
    """
    Create a step contribution at a fixed time point.

    The cumulative function increases (or decreases if negative) by the
    specified height at the given time point and stays at that level.

    Args:
        time: The time point for the step.
        height: The step height (positive for increase, negative for decrease).

    Returns:
        A CumulExpr representing the step.

    Raises:
        TypeError: If time or height are not integers.

    Example:
        >>> s = step_at(10, 5)  # Increase by 5 at time 10
        >>> s = step_at(20, -3)  # Decrease by 3 at time 20
    """
    if not isinstance(time, int):
        raise TypeError(f"time must be an int, got {type(time).__name__}")
    if not isinstance(height, int):
        raise TypeError(f"height must be an int, got {type(height).__name__}")

    return CumulExpr(
        expr_type=CumulExprType.STEP_AT,
        time=time,
        height=height,
    )


def step_at_start(
    interval: IntervalVar,
    height: int | None = None,
    height_min: int | None = None,
    height_max: int | None = None,
) -> CumulExpr:
    """
    Create a step contribution at the start of an interval.

    The cumulative function increases (or decreases) by the specified
    height at the start of the interval. The change is permanent.

    Args:
        interval: The interval variable.
        height: Fixed step height.
        height_min: Minimum height for variable step.
        height_max: Maximum height for variable step.

    Returns:
        A CumulExpr representing the step at start.

    Raises:
        TypeError: If interval is not an IntervalVar.
        ValueError: If height specification is invalid.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> s = step_at_start(task, height=2)  # Increase by 2 at start
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")

    if height is not None:
        if height_min is not None or height_max is not None:
            raise ValueError("Cannot specify both height and height_min/height_max")
        if not isinstance(height, int):
            raise TypeError(f"height must be an int, got {type(height).__name__}")
        return CumulExpr(
            expr_type=CumulExprType.STEP_AT_START,
            interval=interval,
            height=height,
        )
    elif height_min is not None and height_max is not None:
        if not isinstance(height_min, int) or not isinstance(height_max, int):
            raise TypeError("height_min and height_max must be integers")
        if height_min > height_max:
            raise ValueError(f"height_min ({height_min}) cannot exceed height_max ({height_max})")
        return CumulExpr(
            expr_type=CumulExprType.STEP_AT_START,
            interval=interval,
            height_min=height_min,
            height_max=height_max,
        )
    else:
        raise ValueError("Must specify either height or both height_min and height_max")


def step_at_end(
    interval: IntervalVar,
    height: int | None = None,
    height_min: int | None = None,
    height_max: int | None = None,
) -> CumulExpr:
    """
    Create a step contribution at the end of an interval.

    The cumulative function increases (or decreases) by the specified
    height at the end of the interval. The change is permanent.

    Args:
        interval: The interval variable.
        height: Fixed step height.
        height_min: Minimum height for variable step.
        height_max: Maximum height for variable step.

    Returns:
        A CumulExpr representing the step at end.

    Raises:
        TypeError: If interval is not an IntervalVar.
        ValueError: If height specification is invalid.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> # Model reservoir: +2 at start (acquire), -2 at end (release)
        >>> usage = step_at_start(task, 2) + step_at_end(task, -2)
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")

    if height is not None:
        if height_min is not None or height_max is not None:
            raise ValueError("Cannot specify both height and height_min/height_max")
        if not isinstance(height, int):
            raise TypeError(f"height must be an int, got {type(height).__name__}")
        return CumulExpr(
            expr_type=CumulExprType.STEP_AT_END,
            interval=interval,
            height=height,
        )
    elif height_min is not None and height_max is not None:
        if not isinstance(height_min, int) or not isinstance(height_max, int):
            raise TypeError("height_min and height_max must be integers")
        if height_min > height_max:
            raise ValueError(f"height_min ({height_min}) cannot exceed height_max ({height_max})")
        return CumulExpr(
            expr_type=CumulExprType.STEP_AT_END,
            interval=interval,
            height_min=height_min,
            height_max=height_max,
        )
    else:
        raise ValueError("Must specify either height or both height_min and height_max")


# =============================================================================
# Cumulative Constraint Functions
# =============================================================================


def cumul_range(cumul: CumulFunction, min_val: int, max_val: int):
    """
    Constrain a cumulative function to stay within a range.

    The cumulative function must satisfy min_val <= cumul <= max_val
    at all time points.

    Args:
        cumul: The cumulative function.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.

    Returns:
        A pycsp3-compatible constraint when possible (for simple pulse-based
        cumulative functions with min_val=0), otherwise a CumulConstraint.

    Raises:
        TypeError: If cumul is not a CumulFunction.
        ValueError: If min_val > max_val.

    Example:
        >>> tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        >>> usage = sum(pulse(t, 2) for t in tasks)
        >>> satisfy(cumul_range(usage, 0, 4))  # Between 0 and 4
    """
    if not isinstance(cumul, CumulFunction):
        raise TypeError(f"cumul must be a CumulFunction, got {type(cumul).__name__}")
    if not isinstance(min_val, int) or not isinstance(max_val, int):
        raise TypeError("min_val and max_val must be integers")
    if min_val > max_val:
        raise ValueError(f"min_val ({min_val}) cannot exceed max_val ({max_val})")

    # For simple case min_val=0, use the <= operator which returns pycsp3 constraint
    if min_val == 0:
        return cumul <= max_val

    # For general range constraints, return CumulConstraint
    return CumulConstraint(
        cumul=cumul,
        constraint_type=CumulConstraintType.RANGE,
        min_bound=min_val,
        max_bound=max_val,
    )


def always_in(
    cumul: CumulFunction,
    interval_or_range: IntervalVar | tuple[int, int],
    min_val: int,
    max_val: int,
) -> CumulConstraint:
    """
    Constrain cumulative function within a time range.

    The cumulative function must satisfy min_val <= cumul <= max_val
    during the specified interval or fixed time range.

    Args:
        cumul: The cumulative function.
        interval_or_range: Either an IntervalVar or a (start, end) tuple.
        min_val: Minimum allowed value during the range.
        max_val: Maximum allowed value during the range.

    Returns:
        A CumulConstraint representing the always_in constraint.

    Raises:
        TypeError: If arguments have wrong types.
        ValueError: If min_val > max_val.

    Example:
        >>> usage = sum(pulse(t, 2) for t in tasks)
        >>> # During maintenance window, only 2 units available
        >>> satisfy(always_in(usage, (100, 200), 0, 2))
        >>> # During task execution, keep minimum level
        >>> satisfy(always_in(usage, task, 1, 5))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(cumul, CumulFunction):
        raise TypeError(f"cumul must be a CumulFunction, got {type(cumul).__name__}")
    if not isinstance(min_val, int) or not isinstance(max_val, int):
        raise TypeError("min_val and max_val must be integers")
    if min_val > max_val:
        raise ValueError(f"min_val ({min_val}) cannot exceed max_val ({max_val})")

    if isinstance(interval_or_range, IntervalVar):
        return CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.ALWAYS_IN,
            min_bound=min_val,
            max_bound=max_val,
            interval=interval_or_range,
        )
    elif isinstance(interval_or_range, tuple) and len(interval_or_range) == 2:
        start, end = interval_or_range
        if not isinstance(start, int) or not isinstance(end, int):
            raise TypeError("Time range must be a tuple of integers")
        if start > end:
            raise ValueError(f"start ({start}) cannot exceed end ({end})")
        return CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.ALWAYS_IN,
            min_bound=min_val,
            max_bound=max_val,
            start_time=start,
            end_time=end,
        )
    else:
        raise TypeError(
            "interval_or_range must be an IntervalVar or (start, end) tuple"
        )


# =============================================================================
# Cumulative Accessor Functions
# =============================================================================


def height_at_start(
    interval: IntervalVar,
    cumul: CumulFunction,
    absent_value: int = 0,
) -> CumulHeightExpr:
    """
    Get the cumulative function height at the start of an interval.

    Returns an expression representing the value of the cumulative
    function at the start time of the interval.

    Args:
        interval: The interval variable.
        cumul: The cumulative function.
        absent_value: Value to use if interval is absent (default: 0).

    Returns:
        An expression for the height at interval start.

    Example:
        >>> usage = sum(pulse(t, 2) for t in tasks)
        >>> h = height_at_start(task, usage)
        >>> # h represents the resource level when task starts
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")
    if not isinstance(cumul, CumulFunction):
        raise TypeError(f"cumul must be a CumulFunction, got {type(cumul).__name__}")

    return CumulHeightExpr(
        expr_type=CumulHeightType.AT_START,
        interval=interval,
        cumul=cumul,
        absent_value=absent_value,
    )


def height_at_end(
    interval: IntervalVar,
    cumul: CumulFunction,
    absent_value: int = 0,
) -> CumulHeightExpr:
    """
    Get the cumulative function height at the end of an interval.

    Returns an expression representing the value of the cumulative
    function at the end time of the interval.

    Args:
        interval: The interval variable.
        cumul: The cumulative function.
        absent_value: Value to use if interval is absent (default: 0).

    Returns:
        An expression for the height at interval end.

    Example:
        >>> usage = sum(pulse(t, 2) for t in tasks)
        >>> h = height_at_end(task, usage)
        >>> # h represents the resource level when task ends
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(interval, IntervalVar):
        raise TypeError(f"interval must be an IntervalVar, got {type(interval).__name__}")
    if not isinstance(cumul, CumulFunction):
        raise TypeError(f"cumul must be a CumulFunction, got {type(cumul).__name__}")

    return CumulHeightExpr(
        expr_type=CumulHeightType.AT_END,
        interval=interval,
        cumul=cumul,
        absent_value=absent_value,
    )


class CumulHeightType(Enum):
    """Types of cumulative height expressions."""

    AT_START = auto()
    AT_END = auto()


@dataclass
class CumulHeightExpr:
    """
    Expression for cumulative function height at a point.

    Represents the value of a cumulative function at the start or
    end of an interval.
    """

    expr_type: CumulHeightType
    interval: IntervalVar
    cumul: CumulFunction
    absent_value: int = 0

    def __repr__(self) -> str:
        """String representation."""
        name = self.interval.name if self.interval else "?"
        if self.expr_type == CumulHeightType.AT_START:
            return f"height_at_start({name}, {self.cumul})"
        else:
            return f"height_at_end({name}, {self.cumul})"


# =============================================================================
# Registry for Cumulative Functions
# =============================================================================


_cumul_registry: list[CumulFunction] = []


def register_cumul(cumul: CumulFunction) -> None:
    """Register a cumulative function."""
    if cumul not in _cumul_registry:
        _cumul_registry.append(cumul)


def get_registered_cumuls() -> list[CumulFunction]:
    """Get all registered cumulative functions."""
    return list(_cumul_registry)


def clear_cumul_registry() -> None:
    """Clear the cumulative function registry."""
    _cumul_registry.clear()
    CumulFunction._id_counter = 0
    CumulExpr._id_counter = 0
