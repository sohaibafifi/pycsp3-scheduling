"""Tests for aggregate expressions."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.expressions import (
    count_present,
    earliest_start,
    latest_end,
    makespan,
    span_length,
)
from pycsp3_scheduling.constraints._pycsp3 import clear_pycsp3_cache
from pycsp3_scheduling.variables import (
    IntervalVar,
    clear_interval_registry,
    clear_sequence_registry,
)


@pytest.fixture(autouse=True)
def reset_state():
    """Reset registries and caches before each test."""
    clear_pycsp3()
    clear_interval_registry()
    clear_sequence_registry()
    clear_pycsp3_cache()
    yield
    clear_pycsp3()
    clear_interval_registry()
    clear_sequence_registry()
    clear_pycsp3_cache()


class TestCountPresent:
    """Tests for count_present expression."""

    def test_basic_expression(self):
        """count_present returns ADD node."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        expr = count_present(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.ADD

    def test_single_interval(self):
        """count_present with single interval returns presence var."""
        intervals = [IntervalVar(size=10, optional=True, name="t0")]

        expr = count_present(intervals)

        # Single presence variable
        assert expr is not None

    def test_mandatory_intervals(self):
        """count_present with mandatory intervals."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        expr = count_present(intervals)

        # Should return sum of 1s = ADD(1, 1, 1)
        assert isinstance(expr, Node)

    def test_empty_intervals(self):
        """count_present with empty list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            count_present([])

    def test_invalid_interval_type(self):
        """count_present rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            count_present(["a", "b"])


class TestEarliestStart:
    """Tests for earliest_start expression."""

    def test_basic_expression(self):
        """earliest_start returns MIN node."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        expr = earliest_start(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.MIN

    def test_single_interval(self):
        """earliest_start with single interval returns start var."""
        intervals = [IntervalVar(size=10, name="t0")]

        expr = earliest_start(intervals)

        # Should be the start variable
        assert expr is not None

    def test_optional_intervals(self):
        """earliest_start handles optional intervals."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        expr = earliest_start(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.MIN

    def test_empty_intervals(self):
        """earliest_start with empty list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            earliest_start([])


class TestLatestEnd:
    """Tests for latest_end expression."""

    def test_basic_expression(self):
        """latest_end returns MAX node."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        expr = latest_end(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.MAX

    def test_single_interval(self):
        """latest_end with single interval returns end expr."""
        intervals = [IntervalVar(size=10, name="t0")]

        expr = latest_end(intervals)

        # Should be the end expression (start + length)
        assert expr is not None

    def test_optional_intervals(self):
        """latest_end handles optional intervals."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        expr = latest_end(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.MAX

    def test_empty_intervals(self):
        """latest_end with empty list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            latest_end([])


class TestSpanLength:
    """Tests for span_length expression."""

    def test_basic_expression(self):
        """span_length returns SUB node."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        expr = span_length(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.SUB

    def test_empty_intervals(self):
        """span_length with empty list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            span_length([])


class TestMakespan:
    """Tests for makespan expression."""

    def test_basic_expression(self):
        """makespan is alias for latest_end."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        expr = makespan(intervals)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.MAX


class TestAggregateIntegration:
    """Integration tests for aggregate expressions with pycsp3."""

    def test_aggregate_in_constraint(self):
        """Test aggregate expressions in constraints."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(5)]

        # Count present >= 3
        count_expr = count_present(tasks)
        satisfy(Node.build(TypeNode.GE, count_expr, 3))

        # Earliest start >= 0
        start_expr = earliest_start(tasks)
        satisfy(Node.build(TypeNode.GE, start_expr, 0))

    def test_aggregate_with_objective(self):
        """Test aggregate expressions work conceptually for objectives."""
        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(5)]

        # These should return valid expressions
        ms = makespan(tasks)
        span = span_length(tasks)

        assert ms is not None
        assert span is not None
