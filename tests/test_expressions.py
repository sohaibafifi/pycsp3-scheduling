"""Tests for interval expressions."""

import pytest

from pycsp3_scheduling.variables import IntervalVar, clear_interval_registry
from pycsp3_scheduling.variables.sequence import SequenceVar
from pycsp3_scheduling.expressions import (
    ExprType,
    IntervalExpr,
    start_of,
    end_of,
    size_of,
    length_of,
    presence_of,
    overlap_length,
    expr_min,
    expr_max,
)
from pycsp3_scheduling.expressions.sequence_expr import (
    next_arg,
    prev_arg,
    clear_sequence_expr_cache,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset registries before each test."""
    clear_interval_registry()
    clear_sequence_expr_cache()
    IntervalExpr._id_counter = 0
    yield
    clear_interval_registry()
    clear_sequence_expr_cache()


class TestBasicAccessors:
    """Tests for basic accessor expressions."""

    def test_start_of(self):
        """Test start_of expression."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task)

        assert expr.expr_type == ExprType.START_OF
        assert expr.interval == task
        assert expr.absent_value == 0

    def test_start_of_with_absent_value(self):
        """Test start_of with custom absent value."""
        task = IntervalVar(size=10, optional=True, name="task")
        expr = start_of(task, absent_value=-1)

        assert expr.expr_type == ExprType.START_OF
        assert expr.absent_value == -1

    def test_end_of(self):
        """Test end_of expression."""
        task = IntervalVar(size=10, name="task")
        expr = end_of(task)

        assert expr.expr_type == ExprType.END_OF
        assert expr.interval == task
        assert expr.absent_value == 0

    def test_size_of(self):
        """Test size_of expression."""
        task = IntervalVar(size=(5, 20), name="task")
        expr = size_of(task)

        assert expr.expr_type == ExprType.SIZE_OF
        assert expr.interval == task

    def test_length_of(self):
        """Test length_of expression."""
        task = IntervalVar(size=10, length=(8, 12), name="task")
        expr = length_of(task)

        assert expr.expr_type == ExprType.LENGTH_OF
        assert expr.interval == task

    def test_presence_of(self):
        """Test presence_of expression."""
        task = IntervalVar(size=10, optional=True, name="task")
        expr = presence_of(task)

        assert expr.expr_type == ExprType.PRESENCE_OF
        assert expr.interval == task


class TestOverlapLength:
    """Tests for overlap_length expression."""

    def test_overlap_length(self):
        """Test overlap_length expression."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = overlap_length(task1, task2)

        assert expr.expr_type == ExprType.OVERLAP_LENGTH
        assert len(expr.operands) == 2

    def test_overlap_length_with_absent_value(self):
        """Test overlap_length with custom absent value."""
        task1 = IntervalVar(size=10, optional=True, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = overlap_length(task1, task2, absent_value=-1)

        assert expr.absent_value == -1


class TestArithmeticOperators:
    """Tests for arithmetic operators on expressions."""

    def test_addition(self):
        """Test expression addition."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) + 5

        assert expr.expr_type == ExprType.ADD
        assert len(expr.operands) == 2

    def test_addition_two_expressions(self):
        """Test adding two expressions."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = start_of(task1) + end_of(task2)

        assert expr.expr_type == ExprType.ADD

    def test_right_addition(self):
        """Test right addition (int + expr)."""
        task = IntervalVar(size=10, name="task")
        expr = 5 + start_of(task)

        assert expr.expr_type == ExprType.ADD

    def test_subtraction(self):
        """Test expression subtraction."""
        task = IntervalVar(size=10, name="task")
        expr = end_of(task) - start_of(task)

        assert expr.expr_type == ExprType.SUB

    def test_right_subtraction(self):
        """Test right subtraction (int - expr)."""
        task = IntervalVar(size=10, name="task")
        expr = 100 - end_of(task)

        assert expr.expr_type == ExprType.SUB
        # First operand should be the constant
        assert expr.operands[0].value == 100

    def test_multiplication(self):
        """Test expression multiplication."""
        task = IntervalVar(size=10, name="task")
        expr = size_of(task) * 2

        assert expr.expr_type == ExprType.MUL

    def test_division(self):
        """Test expression division."""
        task = IntervalVar(size=10, name="task")
        expr = size_of(task) / 2

        assert expr.expr_type == ExprType.DIV

    def test_negation(self):
        """Test expression negation."""
        task = IntervalVar(size=10, name="task")
        expr = -start_of(task)

        assert expr.expr_type == ExprType.NEG
        assert len(expr.operands) == 1

    def test_absolute(self):
        """Test absolute value."""
        task = IntervalVar(size=10, name="task")
        expr = abs(start_of(task) - 50)

        assert expr.expr_type == ExprType.ABS

    def test_chained_arithmetic(self):
        """Test chained arithmetic operations."""
        task = IntervalVar(size=10, name="task")
        expr = (end_of(task) - start_of(task)) * 2 + 5

        assert expr.expr_type == ExprType.ADD


class TestComparisonOperators:
    """Tests for comparison operators."""

    def test_equality(self):
        """Test equality comparison."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")
        expr = start_of(task1) == start_of(task2)

        assert expr.expr_type == ExprType.EQ
        assert expr.is_comparison()

    def test_equality_with_constant(self):
        """Test equality with constant."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) == 0

        assert expr.expr_type == ExprType.EQ

    def test_inequality(self):
        """Test inequality comparison."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) != 0

        assert expr.expr_type == ExprType.NE

    def test_less_than(self):
        """Test less than comparison."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")
        expr = end_of(task1) < start_of(task2)

        assert expr.expr_type == ExprType.LT

    def test_less_equal(self):
        """Test less than or equal comparison."""
        task = IntervalVar(size=10, name="task")
        expr = end_of(task) <= 100

        assert expr.expr_type == ExprType.LE

    def test_greater_than(self):
        """Test greater than comparison."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) > 10

        assert expr.expr_type == ExprType.GT

    def test_greater_equal(self):
        """Test greater than or equal comparison."""
        task = IntervalVar(size=10, name="task")
        expr = size_of(task) >= 5

        assert expr.expr_type == ExprType.GE


class TestMinMaxExpressions:
    """Tests for min/max expressions."""

    def test_expr_min(self):
        """Test minimum of expressions."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = expr_min(end_of(task1), end_of(task2))

        assert expr.expr_type == ExprType.MIN
        assert len(expr.operands) == 2

    def test_expr_min_multiple(self):
        """Test minimum of multiple expressions."""
        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]
        expr = expr_min(end_of(tasks[0]), end_of(tasks[1]), end_of(tasks[2]))

        assert expr.expr_type == ExprType.MIN
        assert len(expr.operands) == 3

    def test_expr_max(self):
        """Test maximum of expressions."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = expr_max(end_of(task1), end_of(task2))

        assert expr.expr_type == ExprType.MAX
        assert len(expr.operands) == 2

    def test_expr_min_error_single_arg(self):
        """Test error when min has single argument."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(ValueError, match="at least 2 arguments"):
            expr_min(end_of(task))

    def test_expr_max_error_single_arg(self):
        """Test error when max has single argument."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(ValueError, match="at least 2 arguments"):
            expr_max(end_of(task))


class TestExpressionUtilities:
    """Tests for expression utilities."""

    def test_get_intervals(self):
        """Test getting all intervals from expression."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = end_of(task1) - start_of(task2)

        intervals = expr.get_intervals()
        assert len(intervals) == 2
        assert task1 in intervals
        assert task2 in intervals

    def test_get_intervals_nested(self):
        """Test getting intervals from deeply nested expression."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        expr = (end_of(task1) + start_of(task2)) * 2 - 5

        intervals = expr.get_intervals()
        assert len(intervals) == 2

    def test_is_comparison(self):
        """Test is_comparison method."""
        task = IntervalVar(size=10, name="task")

        assert not start_of(task).is_comparison()
        assert (start_of(task) == 0).is_comparison()
        assert (start_of(task) < 10).is_comparison()

    def test_hashable(self):
        """Test that expressions are hashable."""
        task = IntervalVar(size=10, name="task")
        expr1 = start_of(task)
        expr2 = end_of(task)

        s = {expr1, expr2}
        assert len(s) == 2

    def test_repr(self):
        """Test string representation."""
        task = IntervalVar(size=10, name="task")

        assert "start_of(task)" in repr(start_of(task))
        assert "end_of(task)" in repr(end_of(task))
        assert "size_of(task)" in repr(size_of(task))
        assert "presence_of(task)" in repr(presence_of(task))

    def test_repr_arithmetic(self):
        """Test repr for arithmetic expressions."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) + 5

        repr_str = repr(expr)
        assert "+" in repr_str

    def test_repr_comparison(self):
        """Test repr for comparison expressions."""
        task = IntervalVar(size=10, name="task")
        expr = start_of(task) <= 100

        repr_str = repr(expr)
        assert "<=" in repr_str


class TestNextArg:
    """Tests for next_arg expression validation (unit tests only).

    Full solution validation tests are in tests/validate_sequence_arg.py
    which runs each test in a subprocess to avoid pycsp3 state issues.
    """

    def test_next_arg_requires_sequence_var(self):
        """Test that next_arg requires a SequenceVar."""
        t1 = IntervalVar(size=5, name="t1")
        t2 = IntervalVar(size=5, name="t2")

        with pytest.raises(TypeError, match="requires a SequenceVar"):
            next_arg([t1, t2], t1)

    def test_next_arg_requires_types(self):
        """Test that next_arg requires sequence with types."""
        t1 = IntervalVar(size=5, name="t1")
        t2 = IntervalVar(size=5, name="t2")
        seq = SequenceVar(intervals=[t1, t2], name="seq")  # No types

        with pytest.raises(ValueError, match="requires sequence with types"):
            next_arg(seq, t1)

    def test_next_arg_interval_not_in_sequence(self):
        """Test error when interval is not in sequence."""
        t1 = IntervalVar(size=5, name="t1")
        t2 = IntervalVar(size=5, name="t2")
        t3 = IntervalVar(size=5, name="t3")
        seq = SequenceVar(intervals=[t1, t2], types=[0, 1], name="seq")

        with pytest.raises(ValueError, match="not in the sequence"):
            next_arg(seq, t3)


class TestPrevArg:
    """Tests for prev_arg expression validation (unit tests only)."""

    def test_prev_arg_requires_sequence_var(self):
        """Test that prev_arg requires a SequenceVar."""
        t1 = IntervalVar(size=5, name="t1")
        t2 = IntervalVar(size=5, name="t2")

        with pytest.raises(TypeError, match="requires a SequenceVar"):
            prev_arg([t1, t2], t1)


class TestElementArray:
    """Tests for ElementArray with transparent indexing."""

    def test_creation(self):
        """Test ElementArray creation."""
        from pycsp3_scheduling.expressions import ElementArray

        arr = ElementArray([10, 20, 30, 40, 50])
        assert len(arr) == 5
        assert arr.data == [10, 20, 30, 40, 50]

    def test_integer_indexing(self):
        """Test indexing with integer constants."""
        from pycsp3_scheduling.expressions import ElementArray

        arr = ElementArray([10, 20, 30, 40, 50])
        assert arr[0] == 10
        assert arr[2] == 30
        assert arr[-1] == 50

    def test_iteration(self):
        """Test iteration over ElementArray."""
        from pycsp3_scheduling.expressions import ElementArray

        arr = ElementArray([10, 20, 30])
        values = list(arr)
        assert values == [10, 20, 30]

    def test_repr(self):
        """Test string representation."""
        from pycsp3_scheduling.expressions import ElementArray

        arr = ElementArray([10, 20, 30])
        assert repr(arr) == "ElementArray([10, 20, 30])"

    def test_empty_array_raises(self):
        """Test that empty arrays are rejected."""
        from pycsp3_scheduling.expressions import ElementArray

        with pytest.raises(ValueError, match="cannot be empty"):
            ElementArray([])


class TestElementMatrixChainedIndexing:
    """Tests for ElementMatrix with M[i][j] chained indexing."""

    def test_creation(self):
        """Test ElementMatrix creation."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2, 3], [4, 5, 6]])
        assert m.n_rows == 2
        assert m.n_cols == 3

    def test_tuple_indexing(self):
        """Test tuple indexing m[row, col]."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2], [3, 4]])
        assert m[0, 1] == 2
        assert m[1, 0] == 3

    def test_chained_indexing(self):
        """Test chained indexing m[row][col]."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2], [3, 4]])
        assert m[0][1] == 2
        assert m[1][0] == 3

    def test_last_value_access(self):
        """Test access to last_value column via chained indexing."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2], [3, 4]], last_value=99, absent_value=0)
        # last_type is at column index n_cols = 2
        assert m.get_value(0, m.last_type) == 99
        assert m.get_value(1, m.last_type) == 99

    def test_absent_value_access(self):
        """Test access to absent_value column."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2], [3, 4]], last_value=0, absent_value=-1)
        # absent_type is at column index n_cols + 1 = 3
        assert m.get_value(0, m.absent_type) == -1
        assert m.get_value(1, m.absent_type) == -1

    def test_per_row_last_value(self):
        """Test per-row last values."""
        from pycsp3_scheduling.expressions import ElementMatrix

        m = ElementMatrix([[1, 2], [3, 4]], last_value=[10, 20])
        assert m.get_value(0, m.last_type) == 10
        assert m.get_value(1, m.last_type) == 20

    def test_empty_matrix_raises(self):
        """Test that empty matrices are rejected."""
        from pycsp3_scheduling.expressions import ElementMatrix

        with pytest.raises(ValueError, match="cannot be empty"):
            ElementMatrix([])

    def test_non_rectangular_raises(self):
        """Test that non-rectangular matrices are rejected."""
        from pycsp3_scheduling.expressions import ElementMatrix

        with pytest.raises(ValueError, match="must be rectangular"):
            ElementMatrix([[1, 2], [3]])
