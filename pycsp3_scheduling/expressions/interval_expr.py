"""
Interval expression functions for scheduling models.

These functions return expression objects that can be used in constraints
and objectives. They extract properties from interval variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Union

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar


class ExprType(Enum):
    """Types of interval expressions."""

    START_OF = auto()
    END_OF = auto()
    SIZE_OF = auto()
    LENGTH_OF = auto()
    PRESENCE_OF = auto()
    OVERLAP_LENGTH = auto()
    # Arithmetic combinations
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    NEG = auto()
    ABS = auto()
    MIN = auto()
    MAX = auto()
    # Comparison (for constraints)
    EQ = auto()
    NE = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()


@dataclass
class IntervalExpr:
    """
    Base class for interval-related expressions.

    These expressions represent values derived from interval variables
    that can be used in constraints and objectives.

    Attributes:
        expr_type: The type of expression.
        interval: The interval variable (if applicable).
        absent_value: Value to use when interval is absent.
        operands: Child expressions for compound expressions.
        value: Constant value (for literals).
    """

    expr_type: ExprType
    interval: IntervalVar | None = None
    absent_value: int = 0
    operands: list[IntervalExpr] = field(default_factory=list)
    value: int | None = None
    _id: int = field(default=-1, repr=False)

    def __post_init__(self) -> None:
        """Assign unique ID."""
        if self._id == -1:
            self._id = IntervalExpr._get_next_id()

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID."""
        current = getattr(IntervalExpr, "_id_counter", 0)
        IntervalExpr._id_counter = current + 1
        return current

    # Arithmetic operators
    def __add__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Add two expressions or expression and constant."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.ADD,
            operands=[self, other_expr],
        )

    def __radd__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Right addition."""
        return self.__add__(other)

    def __sub__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Subtract two expressions or expression and constant."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.SUB,
            operands=[self, other_expr],
        )

    def __rsub__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Right subtraction."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.SUB,
            operands=[other_expr, self],
        )

    def __mul__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Multiply two expressions or expression and constant."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.MUL,
            operands=[self, other_expr],
        )

    def __rmul__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Right multiplication."""
        return self.__mul__(other)

    def __truediv__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Divide two expressions or expression and constant."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.DIV,
            operands=[self, other_expr],
        )

    def __neg__(self) -> IntervalExpr:
        """Negate expression."""
        return IntervalExpr(
            expr_type=ExprType.NEG,
            operands=[self],
        )

    def __abs__(self) -> IntervalExpr:
        """Absolute value of expression."""
        return IntervalExpr(
            expr_type=ExprType.ABS,
            operands=[self],
        )

    # Comparison operators (return constraint expressions)
    def __eq__(self, other: object) -> IntervalExpr:  # type: ignore[override]
        """Equality comparison."""
        if isinstance(other, (IntervalExpr, int)):
            other_expr = _to_expr(other)
            return IntervalExpr(
                expr_type=ExprType.EQ,
                operands=[self, other_expr],
            )
        return NotImplemented

    def __ne__(self, other: object) -> IntervalExpr:  # type: ignore[override]
        """Inequality comparison."""
        if isinstance(other, (IntervalExpr, int)):
            other_expr = _to_expr(other)
            return IntervalExpr(
                expr_type=ExprType.NE,
                operands=[self, other_expr],
            )
        return NotImplemented

    def __lt__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Less than comparison."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.LT,
            operands=[self, other_expr],
        )

    def __le__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Less than or equal comparison."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.LE,
            operands=[self, other_expr],
        )

    def __gt__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Greater than comparison."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.GT,
            operands=[self, other_expr],
        )

    def __ge__(self, other: Union[IntervalExpr, int]) -> IntervalExpr:
        """Greater than or equal comparison."""
        other_expr = _to_expr(other)
        return IntervalExpr(
            expr_type=ExprType.GE,
            operands=[self, other_expr],
        )

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        # Check for constant value first
        if self.value is not None:
            return str(self.value)
        if self.expr_type == ExprType.START_OF:
            return f"start_of({self.interval.name if self.interval else '?'})"
        elif self.expr_type == ExprType.END_OF:
            return f"end_of({self.interval.name if self.interval else '?'})"
        elif self.expr_type == ExprType.SIZE_OF:
            return f"size_of({self.interval.name if self.interval else '?'})"
        elif self.expr_type == ExprType.LENGTH_OF:
            return f"length_of({self.interval.name if self.interval else '?'})"
        elif self.expr_type == ExprType.PRESENCE_OF:
            return f"presence_of({self.interval.name if self.interval else '?'})"
        elif self.expr_type == ExprType.OVERLAP_LENGTH:
            names = [op.interval.name if op.interval else '?' for op in self.operands]
            return f"overlap_length({names[0]}, {names[1]})"
        elif self.expr_type == ExprType.ADD:
            return f"({self.operands[0]} + {self.operands[1]})"
        elif self.expr_type == ExprType.SUB:
            return f"({self.operands[0]} - {self.operands[1]})"
        elif self.expr_type == ExprType.MUL:
            return f"({self.operands[0]} * {self.operands[1]})"
        elif self.expr_type == ExprType.DIV:
            return f"({self.operands[0]} / {self.operands[1]})"
        elif self.expr_type == ExprType.NEG:
            return f"(-{self.operands[0]})"
        elif self.expr_type == ExprType.MIN:
            return f"min({', '.join(str(op) for op in self.operands)})"
        elif self.expr_type == ExprType.MAX:
            return f"max({', '.join(str(op) for op in self.operands)})"
        elif self.expr_type == ExprType.ABS:
            return f"abs({self.operands[0]})"
        elif self.expr_type == ExprType.EQ:
            return f"({self.operands[0]} == {self.operands[1]})"
        elif self.expr_type == ExprType.NE:
            return f"({self.operands[0]} != {self.operands[1]})"
        elif self.expr_type == ExprType.LT:
            return f"({self.operands[0]} < {self.operands[1]})"
        elif self.expr_type == ExprType.LE:
            return f"({self.operands[0]} <= {self.operands[1]})"
        elif self.expr_type == ExprType.GT:
            return f"({self.operands[0]} > {self.operands[1]})"
        elif self.expr_type == ExprType.GE:
            return f"({self.operands[0]} >= {self.operands[1]})"
        return f"IntervalExpr({self.expr_type})"

    def get_intervals(self) -> list[IntervalVar]:
        """Get all interval variables referenced by this expression."""
        intervals = []
        if self.interval is not None:
            intervals.append(self.interval)
        for operand in self.operands:
            intervals.extend(operand.get_intervals())
        return intervals

    def is_comparison(self) -> bool:
        """Check if this is a comparison expression (constraint)."""
        return self.expr_type in (
            ExprType.EQ,
            ExprType.NE,
            ExprType.LT,
            ExprType.LE,
            ExprType.GT,
            ExprType.GE,
        )


def _to_expr(value: Union[IntervalExpr, int]) -> IntervalExpr:
    """Convert value to IntervalExpr."""
    if isinstance(value, IntervalExpr):
        return value
    if isinstance(value, int):
        # Create a constant expression
        return IntervalExpr(
            expr_type=ExprType.ADD,  # Dummy type for constants
            value=value,
        )
    raise TypeError(f"Cannot convert {type(value)} to IntervalExpr")


# ============================================================================
# Public API Functions
# ============================================================================


def start_of(interval: IntervalVar, absent_value: int = 0) -> IntervalExpr:
    """
    Return an expression representing the start time of an interval.

    If the interval is absent (optional and not selected), returns absent_value.

    Args:
        interval: The interval variable.
        absent_value: Value to return if interval is absent (default: 0).

    Returns:
        An expression representing the start time.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> expr = start_of(task)
        >>> # Can be used in constraints: start_of(task) >= 5
    """
    return IntervalExpr(
        expr_type=ExprType.START_OF,
        interval=interval,
        absent_value=absent_value,
    )


def end_of(interval: IntervalVar, absent_value: int = 0) -> IntervalExpr:
    """
    Return an expression representing the end time of an interval.

    If the interval is absent (optional and not selected), returns absent_value.

    FIXME: end_of() still returns an internal IntervalExpr; for pycsp3 objectives use end_time() for now.

    Args:
        interval: The interval variable.
        absent_value: Value to return if interval is absent (default: 0).

    Returns:
        An expression representing the end time.

    Example:
        >>> task = IntervalVar(size=10, name="task")
        >>> expr = end_of(task)
        >>> # Can be used in constraints: end_of(task) <= 100
    """
    return IntervalExpr(
        expr_type=ExprType.END_OF,
        interval=interval,
        absent_value=absent_value,
    )


def size_of(interval: IntervalVar, absent_value: int = 0) -> IntervalExpr:
    """
    Return an expression representing the size (duration) of an interval.

    If the interval is absent (optional and not selected), returns absent_value.

    Args:
        interval: The interval variable.
        absent_value: Value to return if interval is absent (default: 0).

    Returns:
        An expression representing the size.

    Example:
        >>> task = IntervalVar(size=(5, 20), name="task")
        >>> expr = size_of(task)
        >>> # Can be used in constraints: size_of(task) >= 10
    """
    return IntervalExpr(
        expr_type=ExprType.SIZE_OF,
        interval=interval,
        absent_value=absent_value,
    )


def length_of(interval: IntervalVar, absent_value: int = 0) -> IntervalExpr:
    """
    Return an expression representing the length of an interval.

    Length can differ from size when intensity functions are used.
    If the interval is absent, returns absent_value.

    Args:
        interval: The interval variable.
        absent_value: Value to return if interval is absent (default: 0).

    Returns:
        An expression representing the length.

    Example:
        >>> task = IntervalVar(size=10, length=(8, 12), name="task")
        >>> expr = length_of(task)
    """
    return IntervalExpr(
        expr_type=ExprType.LENGTH_OF,
        interval=interval,
        absent_value=absent_value,
    )


def presence_of(interval: IntervalVar) -> IntervalExpr:
    """
    Return a boolean expression representing whether the interval is present.

    For mandatory intervals, this is always true.
    For optional intervals, this is a decision variable.

    Args:
        interval: The interval variable.

    Returns:
        A boolean expression (0 or 1) for presence.

    Example:
        >>> task = IntervalVar(size=10, optional=True, name="task")
        >>> expr = presence_of(task)
        >>> # Can be used: presence_of(task) == 1 means task is selected
    """
    return IntervalExpr(
        expr_type=ExprType.PRESENCE_OF,
        interval=interval,
        absent_value=0,  # Not applicable for presence
    )


def overlap_length(
    interval1: IntervalVar,
    interval2: IntervalVar,
    absent_value: int = 0,
) -> IntervalExpr:
    """
    Return an expression for the overlap length between two intervals.

    The overlap is max(0, min(end1, end2) - max(start1, start2)).
    If either interval is absent, returns absent_value.

    Args:
        interval1: First interval variable.
        interval2: Second interval variable.
        absent_value: Value to return if either interval is absent.

    Returns:
        An expression representing the overlap length.

    Example:
        >>> task1 = IntervalVar(size=10, name="task1")
        >>> task2 = IntervalVar(size=15, name="task2")
        >>> expr = overlap_length(task1, task2)
        >>> # expr == 0 means no overlap
    """
    # Create placeholder expressions for the two intervals
    expr1 = IntervalExpr(
        expr_type=ExprType.START_OF,
        interval=interval1,
    )
    expr2 = IntervalExpr(
        expr_type=ExprType.START_OF,
        interval=interval2,
    )
    return IntervalExpr(
        expr_type=ExprType.OVERLAP_LENGTH,
        operands=[expr1, expr2],
        absent_value=absent_value,
    )


# ============================================================================
# Utility Functions
# ============================================================================


def expr_min(*args: Union[IntervalExpr, int]) -> IntervalExpr:
    """
    Return the minimum of multiple expressions.

    Args:
        *args: Expressions or integers to take minimum of.

    Returns:
        An expression representing the minimum.
    """
    if len(args) < 2:
        raise ValueError("expr_min requires at least 2 arguments")
    exprs = [_to_expr(a) for a in args]
    return IntervalExpr(
        expr_type=ExprType.MIN,
        operands=exprs,
    )


def expr_max(*args: Union[IntervalExpr, int]) -> IntervalExpr:
    """
    Return the maximum of multiple expressions.

    Args:
        *args: Expressions or integers to take maximum of.

    Returns:
        An expression representing the maximum.
    """
    if len(args) < 2:
        raise ValueError("expr_max requires at least 2 arguments")
    exprs = [_to_expr(a) for a in args]
    return IntervalExpr(
        expr_type=ExprType.MAX,
        operands=exprs,
    )
