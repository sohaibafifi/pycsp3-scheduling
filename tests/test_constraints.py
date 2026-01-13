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

    def test_transition_matrix_now_supported(self):
        """transition_matrix is now supported with typed SequenceVar."""
        tasks = [IntervalVar(size=3, name="t1"), IntervalVar(size=2, name="t2")]
        seq = SequenceVar(intervals=tasks, types=[0, 1], name="machine")

        # Should not raise - now supported
        result = SeqNoOverlap(seq, transition_matrix=[[0, 5], [3, 0]])
        assert isinstance(result, list)

    def test_transition_matrix_requires_types(self):
        """transition_matrix requires SequenceVar with types."""
        task = IntervalVar(size=3, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(ValueError, match="requires a SequenceVar with types"):
            SeqNoOverlap(seq, transition_matrix=[[0]])

    def test_is_direct_parameter(self):
        """is_direct parameter is accepted for direct (Next) transitions."""
        tasks = [IntervalVar(size=3, name="t1"), IntervalVar(size=2, name="t2")]
        seq = SequenceVar(intervals=tasks, types=[0, 1], name="machine")

        # is_direct can be used with transition matrix
        result = SeqNoOverlap(seq, transition_matrix=[[0, 5], [3, 0]], is_direct=True)
        assert isinstance(result, list)

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
        # Returns a list of pairwise constraints when there are optional intervals
        ctrs = SeqNoOverlap(seq)
        assert isinstance(ctrs, list)
        assert len(ctrs) >= 1


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


# =============================================================================
# Intensity Discretization Tests
# =============================================================================


class TestIntensityDiscretization:
    """
    Tests for intensity function discretization.

    Intensity functions model variable work rates over time. The key equation is:
        size * granularity = sum of intensity(t) for t in [start, start + length)

    These tests verify the discretization logic that converts this relationship
    into table constraints for XCSP3 export.
    """

    def test_intensity_at_basic(self):
        """Test intensity evaluation at various time points."""
        from pycsp3_scheduling.constraints._pycsp3 import _intensity_at

        # Steps: 0 until t=5, then 80, then 50 after t=10
        steps = [(5, 80), (10, 50)]

        # Before first step: default value is 0
        assert _intensity_at(steps, 0) == 0
        assert _intensity_at(steps, 4) == 0

        # At and after first step
        assert _intensity_at(steps, 5) == 80
        assert _intensity_at(steps, 9) == 80

        # At and after second step
        assert _intensity_at(steps, 10) == 50
        assert _intensity_at(steps, 100) == 50

    def test_intensity_at_single_step(self):
        """Test intensity with a single step starting at 0."""
        from pycsp3_scheduling.constraints._pycsp3 import _intensity_at

        # Constant 100% intensity from the start
        steps = [(0, 100)]

        assert _intensity_at(steps, 0) == 100
        assert _intensity_at(steps, 50) == 100

    def test_integrate_intensity_constant(self):
        """Test integration with constant intensity."""
        from pycsp3_scheduling.constraints._pycsp3 import _integrate_intensity

        # Constant 100% intensity
        steps = [(0, 100)]

        # Integral over [0, 10) = 100 * 10 = 1000
        assert _integrate_intensity(steps, 0, 10) == 1000

        # Integral over [5, 15) = 100 * 10 = 1000
        assert _integrate_intensity(steps, 5, 15) == 1000

    def test_integrate_intensity_step_change(self):
        """Test integration across a step boundary."""
        from pycsp3_scheduling.constraints._pycsp3 import _integrate_intensity

        # 100% until t=10, then 50%
        steps = [(0, 100), (10, 50)]

        # Integral over [0, 20):
        # [0, 10): 100 * 10 = 1000
        # [10, 20): 50 * 10 = 500
        # Total: 1500
        assert _integrate_intensity(steps, 0, 20) == 1500

        # Integral over [5, 15):
        # [5, 10): 100 * 5 = 500
        # [10, 15): 50 * 5 = 250
        # Total: 750
        assert _integrate_intensity(steps, 5, 15) == 750

    def test_integrate_intensity_empty_range(self):
        """Test integration with empty or invalid range."""
        from pycsp3_scheduling.constraints._pycsp3 import _integrate_intensity

        steps = [(0, 100)]

        # Empty range
        assert _integrate_intensity(steps, 5, 5) == 0

        # Negative range (end < start)
        assert _integrate_intensity(steps, 10, 5) == 0

    def test_find_length_for_work_constant_intensity(self):
        """Test finding length with constant intensity."""
        from pycsp3_scheduling.constraints._pycsp3 import _find_length_for_work

        # Constant 100% intensity
        steps = [(0, 100)]

        # Need 1000 work units at 100 intensity/time -> 10 time units
        assert _find_length_for_work(0, 1000, 100, steps=steps) == 10

        # Starting at t=5 doesn't change anything (constant intensity)
        assert _find_length_for_work(5, 1000, 100, steps=steps) == 10

    def test_find_length_for_work_variable_intensity(self):
        """Test finding length when intensity varies."""
        from pycsp3_scheduling.constraints._pycsp3 import _find_length_for_work

        # 100% until t=10, then 50%
        steps = [(0, 100), (10, 50)]

        # Starting at t=0, need 1000 work units:
        # At 100 intensity, 10 time units gives exactly 1000
        assert _find_length_for_work(0, 1000, 100, steps=steps) == 10

        # Starting at t=5, need 1000 work units:
        # [5, 10): 5 * 100 = 500
        # Need 500 more at 50 intensity -> 10 more time units
        # Total length: 5 + 10 = 15
        assert _find_length_for_work(5, 1000, 100, steps=steps) == 15

        # Starting at t=10 (in 50% zone), need 1000 work units:
        # At 50 intensity, need 20 time units
        assert _find_length_for_work(10, 1000, 100, steps=steps) == 20

    def test_find_length_for_work_zero_intensity(self):
        """Test that zero intensity returns None (can't complete work)."""
        from pycsp3_scheduling.constraints._pycsp3 import _find_length_for_work

        # No steps means 0 intensity everywhere
        steps = []

        # Can't complete any work with 0 intensity
        assert _find_length_for_work(0, 100, 1000, steps=steps) is None

    def test_find_length_for_work_exceeds_max(self):
        """Test when work can't be completed within max_length."""
        from pycsp3_scheduling.constraints._pycsp3 import _find_length_for_work

        # Low intensity
        steps = [(0, 10)]

        # Need 1000 work at intensity 10 -> would need 100 time units
        # But max_length is 50
        assert _find_length_for_work(0, 1000, 50, steps=steps) is None

    def test_compute_intensity_table_fixed_size(self):
        """Test table computation for fixed-size interval."""
        from pycsp3_scheduling.constraints._pycsp3 import _compute_intensity_table

        # Create interval with intensity
        # size=10, granularity=100 -> need 1000 work units
        # Intensity: 100% until t=10, then 50%
        #
        # IMPORTANT: length must be explicitly set to allow values larger than size
        # because at 50% intensity, length will be 20 (double the size)
        intensity = [(0, 100), (10, 50)]
        task = IntervalVar(
            size=10,
            length=(10, 30),  # Allow length up to 30 for lower intensity periods
            intensity=intensity,
            granularity=100,
            start=(0, 20),
            end=(0, 50),
            name="task",
        )

        table = _compute_intensity_table(task, horizon=50)

        assert table is not None
        assert len(table) > 0

        # All entries should be (start, length) tuples
        for entry in table:
            assert len(entry) == 2
            start, length = entry
            assert isinstance(start, int)
            assert isinstance(length, int)

        # Check specific values:
        # At start=0, intensity is 100, so length=10
        assert (0, 10) in table

        # At start=5, need to work across the boundary:
        # [5,10): 5*100=500, then need 500 more at 50 -> 10 units
        # Total length = 5 + 10 = 15
        assert (5, 15) in table

        # At start=10, intensity is 50, so length=20
        assert (10, 20) in table

    def test_compute_intensity_table_variable_size(self):
        """Test table computation for variable-size interval."""
        from pycsp3_scheduling.constraints._pycsp3 import _compute_intensity_table

        # Variable size interval with explicit length bounds
        intensity = [(0, 100)]
        task = IntervalVar(
            size=(5, 10),
            length=(5, 15),  # Explicit length bounds
            intensity=intensity,
            granularity=100,
            start=(0, 10),
            end=(0, 30),
            name="task",
        )

        table = _compute_intensity_table(task, horizon=30)

        assert table is not None

        # Entries should be (start, size, length) triples
        for entry in table:
            assert len(entry) == 3
            start, size, length = entry
            # At constant 100 intensity, length should equal size
            assert length == size

    def test_compute_intensity_table_no_intensity(self):
        """Test that None is returned when no intensity is defined."""
        from pycsp3_scheduling.constraints._pycsp3 import _compute_intensity_table

        task = IntervalVar(size=10, name="task")

        table = _compute_intensity_table(task, horizon=100)

        assert table is None

    def test_length_var_with_intensity(self):
        """Test that length_var posts intensity constraint."""
        from pycsp3_scheduling.constraints._pycsp3 import (
            _intensity_constraints_posted,
            length_var,
        )

        # Intensity: 100% until t=10, then 50%
        # With size=10 and granularity=100, at 50% we need length=20
        intensity = [(0, 100), (10, 50)]
        task = IntervalVar(
            size=10,
            length=(10, 30),  # Allow larger lengths for lower intensity
            intensity=intensity,
            granularity=100,
            start=(0, 20),
            end=(0, 60),
            name="task",
        )

        # Get the length variable - this should post the constraint
        length = length_var(task)

        # Verify constraint was posted
        assert task in _intensity_constraints_posted

        # Verify length is a variable (not a constant)
        assert hasattr(length, "id")

    def test_length_value_with_intensity_returns_variable(self):
        """Test that length_value returns a variable when intensity is set."""
        from pycsp3_scheduling.constraints._pycsp3 import length_value

        # Constant 100% intensity - length will equal size
        intensity = [(0, 100)]
        task = IntervalVar(
            size=10,
            length=(10, 20),  # Explicit length bounds
            intensity=intensity,
            granularity=100,
            start=(0, 50),
            end=(0, 70),
            name="task",
        )

        result = length_value(task)

        # Should be a variable, not a constant
        assert hasattr(result, "id")

    def test_length_value_without_intensity_fixed(self):
        """Test that length_value returns constant for fixed-size without intensity."""
        from pycsp3_scheduling.constraints._pycsp3 import length_value

        task = IntervalVar(size=10, name="task")

        result = length_value(task)

        # Should be a constant (integer)
        assert result == 10

    def test_intensity_constraint_posted_once(self):
        """Test that intensity constraint is only posted once per interval."""
        from pycsp3_scheduling.constraints._pycsp3 import (
            _intensity_constraints_posted,
            length_var,
        )

        # Constant 100% intensity
        intensity = [(0, 100)]
        task = IntervalVar(
            size=10,
            length=(10, 20),  # Explicit length bounds
            intensity=intensity,
            granularity=100,
            start=(0, 50),
            end=(0, 70),
            name="task",
        )

        # Call length_var twice
        length_var(task)
        length_var(task)

        # Should only be tracked once
        assert task in _intensity_constraints_posted
