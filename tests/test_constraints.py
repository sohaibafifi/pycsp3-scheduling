"""Tests for scheduling constraints."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import ECtr, clear as clear_pycsp3
from pycsp3.classes.main.constraints import ConstraintNoOverlap
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    SeqNoOverlap,
    end_at_end,
    end_at_start,
    end_before_end,
    end_before_start,
    start_at_end,
    start_at_start,
    start_before_end,
    start_before_start,
)
from pycsp3_scheduling.constraints._pycsp3 import clear_pycsp3_cache
from pycsp3_scheduling.variables import (
    IntervalVar,
    SequenceVar,
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


class TestSeqNoOverlap:
    """Tests for SeqNoOverlap constraint."""

    def test_sequence_var(self):
        """SeqNoOverlap accepts a SequenceVar."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")
        seq = SequenceVar(intervals=[task1, task2], name="machine")

        ctr = SeqNoOverlap(seq)

        assert isinstance(ctr, ECtr)
        assert isinstance(ctr.constraint, ConstraintNoOverlap)

    def test_interval_list(self):
        """SeqNoOverlap accepts a list of IntervalVar."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        ctr = SeqNoOverlap([task1, task2])

        assert isinstance(ctr, ECtr)
        assert isinstance(ctr.constraint, ConstraintNoOverlap)

    def test_transition_matrix_not_supported(self):
        """transition_matrix is rejected for now."""
        task = IntervalVar(size=3, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(NotImplementedError, match="transition_matrix"):
            SeqNoOverlap(seq, transition_matrix=[[0]])

    def test_is_direct_not_supported(self):
        """is_direct is rejected for now."""
        task = IntervalVar(size=3, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(NotImplementedError, match="is_direct"):
            SeqNoOverlap(seq, is_direct=True)

    def test_invalid_sequence_type(self):
        """SeqNoOverlap rejects non-sequences."""
        with pytest.raises(TypeError, match="SequenceVar"):
            SeqNoOverlap(123)

    def test_invalid_interval_element(self):
        """SeqNoOverlap rejects non-IntervalVar elements."""
        with pytest.raises(TypeError, match="IntervalVar"):
            SeqNoOverlap([1, 2])

    def test_optional_interval_supported(self):
        """Optional intervals are now supported."""
        task = IntervalVar(size=3, optional=True, name="t1")
        task2 = IntervalVar(size=2, optional=True, name="t2")
        seq = SequenceVar(intervals=[task, task2], name="machine")

        # Should not raise - optional intervals now supported
        ctr = SeqNoOverlap(seq)
        assert isinstance(ctr, ECtr)


# =============================================================================
# Exact Timing Constraints (Equality)
# =============================================================================


class TestStartAtStart:
    """Tests for start_at_start constraint."""

    def test_basic_constraint(self):
        """start_at_start returns an equality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_at_start(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "eq(" in expr_str

    def test_with_delay(self):
        """start_at_start with delay adds to rhs."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_at_start(task1, task2, delay=5)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        assert "5" in expr_str
        assert "add(" in expr_str

    def test_invalid_interval_type(self):
        """start_at_start rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            start_at_start("t0", task)

    def test_invalid_delay_type(self):
        """start_at_start rejects non-int delay."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        with pytest.raises(TypeError, match="delay must be an int"):
            start_at_start(task1, task2, delay="5")


class TestStartAtEnd:
    """Tests for start_at_end constraint."""

    def test_basic_constraint(self):
        """start_at_end returns an equality node with length."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_at_end(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        # Should have start vars and duration
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "3" in expr_str  # Fixed length of task1

    def test_with_delay(self):
        """start_at_end with delay adds to rhs."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_at_end(task1, task2, delay=2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        # delay (2) + length (3) = 5 in the expression
        assert "5" in expr_str

    def test_variable_length(self):
        """start_at_end works with variable-length intervals."""
        task1 = IntervalVar(size=(3, 10), name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_at_end(task1, task2)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "iv_l_0" in expr_str  # Variable length for task1

    def test_invalid_interval_type(self):
        """start_at_end rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            start_at_end(task, "t2")


class TestEndAtStart:
    """Tests for end_at_start constraint."""

    def test_basic_constraint(self):
        """end_at_start returns an equality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_at_start(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str

    def test_with_delay(self):
        """end_at_start with delay adds to rhs."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_at_start(task1, task2, delay=4)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "4" in expr_str

    def test_invalid_interval_type(self):
        """end_at_start rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            end_at_start(task, 123)


class TestEndAtEnd:
    """Tests for end_at_end constraint."""

    def test_basic_constraint(self):
        """end_at_end returns an equality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_at_end(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        # Should have both start vars and both lengths
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "3" in expr_str  # task1 length
        assert "2" in expr_str  # task2 length

    def test_with_delay(self):
        """end_at_end with delay adds to rhs."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_at_end(task1, task2, delay=7)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.EQ
        expr_str = str(expr)
        # length(a)=3 + delay=7 = 10 in the expression
        assert "10" in expr_str

    def test_variable_lengths(self):
        """end_at_end works with variable-length intervals."""
        task1 = IntervalVar(size=(3, 10), name="t1")
        task2 = IntervalVar(size=(2, 8), name="t2")

        expr = end_at_end(task1, task2)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "iv_l_0" in expr_str  # Variable length for task1
        assert "iv_l_1" in expr_str  # Variable length for task2

    def test_invalid_interval_type(self):
        """end_at_end rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            end_at_end(None, task)


# =============================================================================
# Before Constraints (Inequality)
# =============================================================================


class TestStartBeforeStart:
    """Tests for start_before_start constraint."""

    def test_basic_constraint(self):
        """start_before_start returns an inequality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_before_start(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "le(" in expr_str

    def test_with_delay(self):
        """start_before_start with delay."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_before_start(task1, task2, delay=3)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "3" in expr_str
        assert "add(" in expr_str

    def test_invalid_interval_type(self):
        """start_before_start rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            start_before_start("invalid", task)


class TestStartBeforeEnd:
    """Tests for start_before_end constraint."""

    def test_basic_constraint(self):
        """start_before_end returns an inequality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_before_end(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "2" in expr_str  # task2 length

    def test_with_delay(self):
        """start_before_end with delay."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = start_before_end(task1, task2, delay=5)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "5" in expr_str

    def test_invalid_interval_type(self):
        """start_before_end rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            start_before_end(task, [])


class TestEndBeforeStart:
    """Tests for end_before_start constraint."""

    def test_basic_constraint(self):
        """end_before_start returns a comparison node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_before_start(task1, task2, delay=1)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "le(" in expr_str

    def test_no_delay(self):
        """end_before_start without delay (classic precedence)."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_before_start(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        assert "3" in expr_str  # task1 length

    def test_invalid_delay_type(self):
        """end_before_start rejects non-int delay."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        with pytest.raises(TypeError, match="delay must be an int"):
            end_before_start(task1, task2, delay="1")

    def test_invalid_interval_type(self):
        """end_before_start rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            end_before_start("t0", task)


class TestEndBeforeEnd:
    """Tests for end_before_end constraint."""

    def test_basic_constraint(self):
        """end_before_end returns an inequality node."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_before_end(task1, task2)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        assert "iv_s_0" in expr_str
        assert "iv_s_1" in expr_str
        assert "3" in expr_str  # task1 length
        assert "2" in expr_str  # task2 length

    def test_with_delay(self):
        """end_before_end with delay."""
        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        expr = end_before_end(task1, task2, delay=4)

        assert isinstance(expr, Node)
        assert expr.type == TypeNode.LE
        expr_str = str(expr)
        # length(a)=3 + delay=4 = 7 in the expression
        assert "7" in expr_str

    def test_variable_lengths(self):
        """end_before_end works with variable-length intervals."""
        task1 = IntervalVar(size=(3, 10), name="t1")
        task2 = IntervalVar(size=(2, 8), name="t2")

        expr = end_before_end(task1, task2)

        assert isinstance(expr, Node)
        expr_str = str(expr)
        assert "iv_l_0" in expr_str
        assert "iv_l_1" in expr_str

    def test_invalid_interval_type(self):
        """end_before_end rejects non-IntervalVar inputs."""
        task = IntervalVar(size=3, name="t1")

        with pytest.raises(TypeError, match="IntervalVar"):
            end_before_end(task, {"not": "interval"})


# =============================================================================
# Integration Tests
# =============================================================================


class TestPrecedenceIntegration:
    """Integration tests for precedence constraints with pycsp3."""

    def test_satisfy_with_precedence(self):
        """Test that constraints can be used with satisfy()."""
        from pycsp3 import satisfy

        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        # Should not raise
        satisfy(end_before_start(task1, task2))

    def test_satisfy_with_multiple_constraints(self):
        """Test multiple precedence constraints together."""
        from pycsp3 import satisfy

        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")
        task3 = IntervalVar(size=4, name="t3")

        # Should not raise
        satisfy(
            end_before_start(task1, task2),
            start_at_start(task2, task3),
        )

    def test_satisfy_with_generator(self):
        """Test precedence constraints with generator expression."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(3)]

        # Chain of precedence constraints
        satisfy(
            end_before_start(tasks[i], tasks[i + 1]) for i in range(len(tasks) - 1)
        )

    def test_constraint_with_regular_pycsp3_var(self):
        """Test that interval vars coexist with regular pycsp3 variables."""
        from pycsp3 import Var, satisfy

        # Regular pycsp3 variable
        x = Var(dom=range(10), id="x")

        # Interval variable
        task = IntervalVar(size=3, name="task")

        # Get pycsp3 var from interval
        from pycsp3_scheduling.interop import start_time

        start = start_time(task)

        # Constraint mixing both
        satisfy(start <= x)

    def test_exact_and_before_constraints_together(self):
        """Test mixing exact timing and before constraints."""
        from pycsp3 import satisfy

        task1 = IntervalVar(size=3, name="t1")
        task2 = IntervalVar(size=2, name="t2")
        task3 = IntervalVar(size=4, name="t3")

        # task1 and task2 start together, task3 starts after task2 ends
        satisfy(
            start_at_start(task1, task2),
            end_before_start(task2, task3),
        )
