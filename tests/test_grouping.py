"""Tests for grouping constraints (span, alternative, synchronize)."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import alternative, span, synchronize
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


# =============================================================================
# Span Constraint Tests
# =============================================================================


class TestSpan:
    """Tests for span constraint."""

    def test_basic_span_mandatory(self):
        """span with mandatory intervals returns constraints."""
        main = IntervalVar(name="main")
        subtasks = [
            IntervalVar(size=3, name="t1"),
            IntervalVar(size=2, name="t2"),
            IntervalVar(size=4, name="t3"),
        ]

        constraints = span(main, subtasks)

        assert isinstance(constraints, list)
        assert len(constraints) == 2  # start = min, end = max
        for c in constraints:
            assert isinstance(c, Node)
            assert c.type == TypeNode.EQ

    def test_span_with_optional_subtasks(self):
        """span with optional subtasks returns containment constraints."""
        main = IntervalVar(name="main")
        subtasks = [
            IntervalVar(size=3, optional=True, name="t1"),
            IntervalVar(size=2, optional=True, name="t2"),
        ]

        constraints = span(main, subtasks)

        assert isinstance(constraints, list)
        assert len(constraints) > 0
        # Should have containment constraints for each optional subtask
        for c in constraints:
            assert isinstance(c, Node)

    def test_span_with_optional_main(self):
        """span with optional main returns presence-linked constraints."""
        main = IntervalVar(optional=True, name="main")
        subtasks = [
            IntervalVar(size=3, name="t1"),
            IntervalVar(size=2, name="t2"),
        ]

        constraints = span(main, subtasks)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_span_with_all_optional(self):
        """span with all optional intervals."""
        main = IntervalVar(optional=True, name="main")
        subtasks = [
            IntervalVar(size=3, optional=True, name="t1"),
            IntervalVar(size=2, optional=True, name="t2"),
        ]

        constraints = span(main, subtasks)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_span_invalid_main_type(self):
        """span rejects non-IntervalVar main."""
        subtasks = [IntervalVar(size=3, name="t1")]

        with pytest.raises(TypeError, match="main must be an IntervalVar"):
            span("not_an_interval", subtasks)

    def test_span_invalid_subtasks_type(self):
        """span rejects non-list subtasks."""
        main = IntervalVar(name="main")

        with pytest.raises(TypeError, match="subtasks must be a list"):
            span(main, "not_a_list")

    def test_span_invalid_subtask_element(self):
        """span rejects non-IntervalVar in subtasks."""
        main = IntervalVar(name="main")

        with pytest.raises(TypeError, match="subtasks\\[1\\] must be an IntervalVar"):
            span(main, [IntervalVar(size=3, name="t1"), "invalid"])

    def test_span_empty_subtasks(self):
        """span rejects empty subtasks list."""
        main = IntervalVar(name="main")

        with pytest.raises(ValueError, match="subtasks cannot be empty"):
            span(main, [])

    def test_span_single_subtask(self):
        """span works with single subtask."""
        main = IntervalVar(name="main")
        subtasks = [IntervalVar(size=5, name="t1")]

        constraints = span(main, subtasks)

        assert isinstance(constraints, list)
        assert len(constraints) == 2


# =============================================================================
# Alternative Constraint Tests
# =============================================================================


class TestAlternative:
    """Tests for alternative constraint."""

    def test_basic_alternative(self):
        """alternative with default cardinality returns constraints."""
        main = IntervalVar(size=10, name="main")
        alts = [
            IntervalVar(size=10, optional=True, name="a1"),
            IntervalVar(size=10, optional=True, name="a2"),
            IntervalVar(size=10, optional=True, name="a3"),
        ]

        constraints = alternative(main, alts)

        assert isinstance(constraints, list)
        assert len(constraints) > 0
        for c in constraints:
            assert isinstance(c, Node)

    def test_alternative_cardinality_2(self):
        """alternative with cardinality=2."""
        main = IntervalVar(size=10, name="main")
        alts = [
            IntervalVar(size=10, optional=True, name="a1"),
            IntervalVar(size=10, optional=True, name="a2"),
            IntervalVar(size=10, optional=True, name="a3"),
        ]

        constraints = alternative(main, alts, cardinality=2)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_alternative_with_optional_main(self):
        """alternative with optional main."""
        main = IntervalVar(size=10, optional=True, name="main")
        alts = [
            IntervalVar(size=10, optional=True, name="a1"),
            IntervalVar(size=10, optional=True, name="a2"),
        ]

        constraints = alternative(main, alts)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_alternative_invalid_main_type(self):
        """alternative rejects non-IntervalVar main."""
        alts = [IntervalVar(size=10, optional=True, name="a1")]

        with pytest.raises(TypeError, match="main must be an IntervalVar"):
            alternative(123, alts)

    def test_alternative_invalid_alternatives_type(self):
        """alternative rejects non-list alternatives."""
        main = IntervalVar(size=10, name="main")

        with pytest.raises(TypeError, match="alternatives must be a list"):
            alternative(main, "not_a_list")

    def test_alternative_empty_alternatives(self):
        """alternative rejects empty alternatives list."""
        main = IntervalVar(size=10, name="main")

        with pytest.raises(ValueError, match="alternatives cannot be empty"):
            alternative(main, [])

    def test_alternative_non_optional_alternative(self):
        """alternative rejects non-optional alternatives."""
        main = IntervalVar(size=10, name="main")
        alts = [
            IntervalVar(size=10, optional=True, name="a1"),
            IntervalVar(size=10, name="a2"),  # Not optional!
        ]

        with pytest.raises(ValueError, match="must be optional"):
            alternative(main, alts)

    def test_alternative_invalid_cardinality_zero(self):
        """alternative rejects cardinality=0."""
        main = IntervalVar(size=10, name="main")
        alts = [IntervalVar(size=10, optional=True, name="a1")]

        with pytest.raises(ValueError, match="cardinality must be a positive integer"):
            alternative(main, alts, cardinality=0)

    def test_alternative_invalid_cardinality_negative(self):
        """alternative rejects negative cardinality."""
        main = IntervalVar(size=10, name="main")
        alts = [IntervalVar(size=10, optional=True, name="a1")]

        with pytest.raises(ValueError, match="cardinality must be a positive integer"):
            alternative(main, alts, cardinality=-1)

    def test_alternative_cardinality_exceeds_alternatives(self):
        """alternative rejects cardinality > len(alternatives)."""
        main = IntervalVar(size=10, name="main")
        alts = [
            IntervalVar(size=10, optional=True, name="a1"),
            IntervalVar(size=10, optional=True, name="a2"),
        ]

        with pytest.raises(ValueError, match="cardinality.*cannot exceed"):
            alternative(main, alts, cardinality=3)


# =============================================================================
# Synchronize Constraint Tests
# =============================================================================


class TestSynchronize:
    """Tests for synchronize constraint."""

    def test_basic_synchronize_mandatory(self):
        """synchronize with mandatory intervals."""
        main = IntervalVar(size=10, name="main")
        intervals = [
            IntervalVar(size=10, name="i1"),
            IntervalVar(size=10, name="i2"),
        ]

        constraints = synchronize(main, intervals)

        assert isinstance(constraints, list)
        # 2 intervals * 2 constraints each (start eq, end eq)
        assert len(constraints) == 4
        for c in constraints:
            assert isinstance(c, Node)
            assert c.type == TypeNode.EQ

    def test_synchronize_with_optional_intervals(self):
        """synchronize with optional intervals."""
        main = IntervalVar(size=10, name="main")
        intervals = [
            IntervalVar(size=10, optional=True, name="i1"),
            IntervalVar(size=10, optional=True, name="i2"),
        ]

        constraints = synchronize(main, intervals)

        assert isinstance(constraints, list)
        assert len(constraints) > 0
        # Should have OR constraints for optional presence

    def test_synchronize_with_optional_main(self):
        """synchronize with optional main."""
        main = IntervalVar(size=10, optional=True, name="main")
        intervals = [
            IntervalVar(size=10, optional=True, name="i1"),
            IntervalVar(size=10, optional=True, name="i2"),
        ]

        constraints = synchronize(main, intervals)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_synchronize_mixed_optional(self):
        """synchronize with mixed optional/mandatory intervals."""
        main = IntervalVar(size=10, name="main")
        intervals = [
            IntervalVar(size=10, name="mandatory"),
            IntervalVar(size=10, optional=True, name="optional"),
        ]

        constraints = synchronize(main, intervals)

        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_synchronize_invalid_main_type(self):
        """synchronize rejects non-IntervalVar main."""
        intervals = [IntervalVar(size=10, name="i1")]

        with pytest.raises(TypeError, match="main must be an IntervalVar"):
            synchronize(None, intervals)

    def test_synchronize_invalid_intervals_type(self):
        """synchronize rejects non-list intervals."""
        main = IntervalVar(size=10, name="main")

        with pytest.raises(TypeError, match="intervals must be a list"):
            synchronize(main, 123)

    def test_synchronize_empty_intervals(self):
        """synchronize rejects empty intervals list."""
        main = IntervalVar(size=10, name="main")

        with pytest.raises(ValueError, match="intervals cannot be empty"):
            synchronize(main, [])

    def test_synchronize_invalid_interval_element(self):
        """synchronize rejects non-IntervalVar in intervals."""
        main = IntervalVar(size=10, name="main")

        with pytest.raises(TypeError, match="intervals\\[0\\] must be an IntervalVar"):
            synchronize(main, ["not_interval"])


# =============================================================================
# Integration Tests
# =============================================================================


class TestGroupingIntegration:
    """Integration tests for grouping constraints with pycsp3."""

    def test_satisfy_with_span(self):
        """Test span works with satisfy()."""
        from pycsp3 import satisfy

        main = IntervalVar(name="project")
        phases = [IntervalVar(size=5, name=f"phase_{i}") for i in range(3)]

        # Should not raise
        satisfy(span(main, phases))

    def test_satisfy_with_alternative(self):
        """Test alternative works with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")
        machines = [
            IntervalVar(size=10, optional=True, name=f"m{i}") for i in range(3)
        ]

        # Should not raise
        satisfy(alternative(task, machines))

    def test_satisfy_with_synchronize(self):
        """Test synchronize works with satisfy()."""
        from pycsp3 import satisfy

        meeting = IntervalVar(size=60, name="meeting")
        attendees = [IntervalVar(size=60, name=f"person_{i}") for i in range(3)]

        # Should not raise
        satisfy(synchronize(meeting, attendees))

    def test_combined_grouping_constraints(self):
        """Test multiple grouping constraints together."""
        from pycsp3 import satisfy

        # Main task spans subtasks
        main = IntervalVar(name="main")
        subs = [IntervalVar(size=5, name=f"sub_{i}") for i in range(2)]

        # Each subtask has alternative implementations
        alts = [
            [IntervalVar(size=5, optional=True, name=f"alt_{i}_{j}") for j in range(2)]
            for i in range(2)
        ]

        satisfy(span(main, subs))
        for i, sub in enumerate(subs):
            satisfy(alternative(sub, alts[i]))

    def test_flexible_job_shop_pattern(self):
        """Test flexible job shop scheduling pattern."""
        from pycsp3 import satisfy

        # Operation that can run on different machines
        operation = IntervalVar(size=10, name="op")
        machine_assignments = [
            IntervalVar(size=10, optional=True, name=f"op_m{i}") for i in range(3)
        ]

        # Exactly one machine assignment
        satisfy(alternative(operation, machine_assignments))


# =============================================================================
# Optional Interval Tests
# =============================================================================


class TestOptionalIntervalSupport:
    """Tests for optional interval support in precedence constraints."""

    def test_optional_interval_precedence(self):
        """Test precedence constraints with optional intervals."""
        from pycsp3_scheduling.constraints import end_before_start

        task1 = IntervalVar(size=3, optional=True, name="t1")
        task2 = IntervalVar(size=2, optional=True, name="t2")

        # Should not raise - optional intervals now supported
        expr = end_before_start(task1, task2)
        assert isinstance(expr, Node)

    def test_optional_interval_exact_timing(self):
        """Test exact timing constraints with optional intervals."""
        from pycsp3_scheduling.constraints import start_at_start

        task1 = IntervalVar(size=3, optional=True, name="t1")
        task2 = IntervalVar(size=2, name="t2")

        # Should not raise
        expr = start_at_start(task1, task2)
        assert isinstance(expr, Node)

    def test_presence_var_optional(self):
        """Test presence variable creation for optional interval."""
        from pycsp3_scheduling.constraints._pycsp3 import presence_var

        task = IntervalVar(size=3, optional=True, name="t1")
        pres = presence_var(task)

        # Should be a pycsp3 variable with domain {0, 1}
        assert pres is not None

    def test_presence_var_mandatory(self):
        """Test presence variable for mandatory interval returns 1."""
        from pycsp3_scheduling.constraints._pycsp3 import presence_var

        task = IntervalVar(size=3, name="t1")
        pres = presence_var(task)

        # Should return constant 1 for mandatory intervals
        assert pres == 1

    def test_presence_var_cached(self):
        """Test presence variable is cached."""
        from pycsp3_scheduling.constraints._pycsp3 import presence_var

        task = IntervalVar(size=3, optional=True, name="t1")
        pres1 = presence_var(task)
        pres2 = presence_var(task)

        # Should return same variable
        assert pres1 is pres2
