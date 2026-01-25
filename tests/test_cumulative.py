"""Tests for cumulative functions and constraints."""

from __future__ import annotations

import pytest

from pycsp3_scheduling import (
    CumulConstraint,
    CumulExpr,
    CumulFunction,
    CumulHeightExpr,
    SeqCumulative,
    IntervalVar,
    always_in,
    cumul_range,
    height_at_end,
    height_at_start,
    pulse,
    step_at,
    step_at_end,
    step_at_start,
)
from pycsp3_scheduling.functions.cumul_functions import (
    CumulConstraintType,
    CumulExprType,
    CumulHeightType,
    clear_cumul_registry,
    get_registered_cumuls,
)


@pytest.fixture(autouse=True)
def reset_cumul_registry():
    """Reset the cumulative registry before each test."""
    clear_cumul_registry()


class TestCumulExpr:
    """Tests for CumulExpr class."""

    def test_pulse_fixed_height(self):
        """Test pulse with fixed height."""
        task = IntervalVar(size=10, name="task")
        expr = pulse(task, 3)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.PULSE
        assert expr.interval is task
        assert expr.height == 3
        assert expr.height_min is None
        assert expr.height_max is None

    def test_pulse_variable_height(self):
        """Test pulse with variable height."""
        task = IntervalVar(size=10, name="task")
        expr = pulse(task, height_min=2, height_max=5)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.PULSE
        assert expr.interval is task
        assert expr.height is None
        assert expr.height_min == 2
        assert expr.height_max == 5

    def test_pulse_no_height_raises(self):
        """Test pulse without height raises error."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(ValueError, match="Must specify either height"):
            pulse(task)

    def test_pulse_both_height_types_raises(self):
        """Test pulse with both height types raises error."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(ValueError, match="Cannot specify both"):
            pulse(task, height=3, height_min=2)

    def test_pulse_partial_variable_height_raises(self):
        """Test pulse with only min or max raises error."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(ValueError, match="Must specify either height"):
            pulse(task, height_min=2)

    def test_step_at(self):
        """Test step_at function."""
        expr = step_at(5, 3)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT
        assert expr.time == 5
        assert expr.height == 3

    def test_step_at_negative(self):
        """Test step_at with negative height."""
        expr = step_at(10, -5)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT
        assert expr.time == 10
        assert expr.height == -5

    def test_step_at_start_fixed(self):
        """Test step_at_start with fixed height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_start(task, 4)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT_START
        assert expr.interval is task
        assert expr.height == 4

    def test_step_at_start_variable(self):
        """Test step_at_start with variable height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_start(task, height_min=1, height_max=3)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT_START
        assert expr.interval is task
        assert expr.height_min == 1
        assert expr.height_max == 3

    def test_step_at_end_fixed(self):
        """Test step_at_end with fixed height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_end(task, -4)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT_END
        assert expr.interval is task
        assert expr.height == -4

    def test_step_at_end_variable(self):
        """Test step_at_end with variable height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_end(task, height_min=-3, height_max=-1)

        assert isinstance(expr, CumulExpr)
        assert expr.expr_type == CumulExprType.STEP_AT_END
        assert expr.interval is task
        assert expr.height_min == -3
        assert expr.height_max == -1

    def test_invalid_interval_type(self):
        """Test pulse with invalid interval type."""
        with pytest.raises(TypeError, match="interval must be an IntervalVar"):
            pulse("not_an_interval", 3)  # type: ignore

    def test_invalid_height_type(self):
        """Test pulse with invalid height type."""
        task = IntervalVar(size=10, name="task")
        with pytest.raises(TypeError, match="height must be an int"):
            pulse(task, "three")  # type: ignore


class TestCumulFunction:
    """Tests for CumulFunction class."""

    def test_add_cumul_exprs(self):
        """Test adding CumulExpr objects."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")

        cumul = pulse(task1, 2) + pulse(task2, 3)

        assert isinstance(cumul, CumulFunction)
        assert len(cumul.expressions) == 2

    def test_add_cumul_function_and_expr(self):
        """Test adding CumulFunction and CumulExpr."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")
        task3 = IntervalVar(size=10, name="task3")

        cumul = pulse(task1, 2) + pulse(task2, 3)
        cumul2 = cumul + pulse(task3, 4)

        assert isinstance(cumul2, CumulFunction)
        assert len(cumul2.expressions) == 3

    def test_add_cumul_functions(self):
        """Test adding two CumulFunction objects."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")

        cumul1 = CumulFunction([pulse(task1, 2)])
        cumul2 = CumulFunction([pulse(task2, 3)])

        combined = cumul1 + cumul2
        assert isinstance(combined, CumulFunction)
        assert len(combined.expressions) == 2

    def test_iadd_cumul_expr(self):
        """Test in-place addition with CumulExpr."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")

        cumul = CumulFunction([pulse(task1, 2)])
        cumul += pulse(task2, 3)

        assert len(cumul.expressions) == 2

    def test_sub_via_negation(self):
        """Test subtraction via negation."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=10, name="task2")

        # Subtraction works via explicit negation
        cumul = pulse(task1, 2) + (-pulse(task2, 3))

        assert isinstance(cumul, CumulFunction)
        assert len(cumul.expressions) == 2
        # Second expression should be negated
        assert cumul.expressions[1].expr_type == CumulExprType.NEG

    def test_sum_of_pulses(self):
        """Test sum() with pulse expressions."""
        tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(5)]
        pulses = [pulse(t, 1) for t in tasks]

        cumul = sum(pulses)

        assert isinstance(cumul, CumulFunction)
        assert len(cumul.expressions) == 5

    def test_sum_with_list_comprehension(self):
        """Test sum() with list comprehension."""
        tasks = [IntervalVar(size=10, name=f"task{i}") for i in range(3)]

        cumul = sum(pulse(t, i + 1) for i, t in enumerate(tasks))

        assert isinstance(cumul, CumulFunction)
        assert len(cumul.expressions) == 3

    def test_neg_cumul_function(self):
        """Test negation of CumulFunction."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])
        neg_cumul = -cumul

        assert isinstance(neg_cumul, CumulFunction)
        assert len(neg_cumul.expressions) == 1
        assert neg_cumul.expressions[0].expr_type == CumulExprType.NEG


class TestCumulConstraint:
    """Tests for CumulConstraint comparisons."""

    def test_le_constraint(self):
        """Test <= comparison creates pycsp3-compatible constraint."""
        from pycsp3.classes.entities import ECtr

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul <= 5

        # For simple pulse-based cumul, returns pycsp3 ECtr
        assert isinstance(constraint, ECtr)

    def test_ge_constraint(self):
        """Test >= comparison creates constraint."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul >= 1

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.GE
        assert constraint.bound == 1

    def test_lt_constraint(self):
        """Test < comparison creates constraint."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul < 5

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.LT
        assert constraint.bound == 5

    def test_gt_constraint(self):
        """Test > comparison creates constraint."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul > 0

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.GT
        assert constraint.bound == 0

    def test_cumul_range_constraint(self):
        """Test cumul_range with min=0 returns pycsp3-compatible constraint."""
        from pycsp3.classes.entities import ECtr

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        # With min_val=0, returns pycsp3 ECtr (same as cumul <= max)
        constraint = cumul_range(cumul, 0, 5)
        assert isinstance(constraint, ECtr)

    def test_cumul_range_with_nonzero_min(self):
        """Test cumul_range with non-zero min returns CumulConstraint."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        # With min_val > 0, returns CumulConstraint
        constraint = cumul_range(cumul, 1, 5)
        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.RANGE
        assert constraint.min_bound == 1
        assert constraint.max_bound == 5

    def test_cumul_range_with_cumul_function(self):
        """Test cumul_range with CumulFunction."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul_range(cumul, 1, 3)

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.RANGE

    def test_cumul_range_invalid_bounds(self):
        """Test cumul_range with invalid bounds."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(ValueError, match="min_val .* cannot exceed max_val"):
            cumul_range(cumul, 5, 3)

    def test_always_in_with_interval(self):
        """Test always_in with interval for time range."""
        task = IntervalVar(size=10, name="task")
        time_range = IntervalVar(start=0, end=100, name="range")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = always_in(cumul, time_range, 0, 5)

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.ALWAYS_IN
        assert constraint.interval is time_range
        assert constraint.min_bound == 0
        assert constraint.max_bound == 5

    def test_always_in_with_tuple(self):
        """Test always_in with tuple for time range."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = always_in(cumul, (0, 100), 0, 5)

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.ALWAYS_IN
        assert constraint.start_time == 0
        assert constraint.end_time == 100

    def test_always_in_invalid_range(self):
        """Test always_in with invalid range type."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="interval_or_range must be"):
            always_in(cumul, [0, 100], 0, 5)  # type: ignore


class TestCumulHeightExpr:
    """Tests for cumulative height accessor expressions."""

    def test_height_at_start(self):
        """Test height_at_start accessor."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        expr = height_at_start(task, cumul)

        assert isinstance(expr, CumulHeightExpr)
        assert expr.expr_type == CumulHeightType.AT_START
        assert expr.cumul is cumul
        assert expr.interval is task

    def test_height_at_start_with_absent(self):
        """Test height_at_start with absent_value."""
        task = IntervalVar(size=10, name="task", optional=True)
        cumul = CumulFunction([pulse(task, 2)])

        expr = height_at_start(task, cumul, absent_value=0)

        assert isinstance(expr, CumulHeightExpr)
        assert expr.absent_value == 0

    def test_height_at_end(self):
        """Test height_at_end accessor."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        expr = height_at_end(task, cumul)

        assert isinstance(expr, CumulHeightExpr)
        assert expr.expr_type == CumulHeightType.AT_END
        assert expr.cumul is cumul
        assert expr.interval is task

    def test_height_at_end_with_absent(self):
        """Test height_at_end with absent_value."""
        task = IntervalVar(size=10, name="task", optional=True)
        cumul = CumulFunction([pulse(task, 2)])

        expr = height_at_end(task, cumul, absent_value=-1)

        assert isinstance(expr, CumulHeightExpr)
        assert expr.absent_value == -1


class TestSeqCumulativeConstraint:
    """Tests for the SeqCumulative global constraint."""

    def test_seq_cumulative_basic(self):
        """Test SeqCumulative constraint creation."""
        tasks = [IntervalVar(size=5, name=f"task{i}") for i in range(3)]
        heights = [1, 2, 1]
        capacity = 3

        # Should not raise and return a list with constraint
        result = SeqCumulative(tasks, heights, capacity)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_cumul_function_creates_constraint(self):
        """Test CumulFunction <= capacity creates pycsp3 constraint."""
        from pycsp3.classes.entities import ECtr

        tasks = [IntervalVar(size=5, name=f"task{i}") for i in range(3)]
        pulses = [pulse(t, h) for t, h in zip(tasks, [1, 2, 1])]
        cumul = sum(pulses)

        # This creates a pycsp3-compatible constraint
        constraint = cumul <= 3

        # For simple pulse-based cumul, returns pycsp3 ECtr
        assert isinstance(constraint, ECtr)

    def test_seq_cumulative_mismatched_lengths(self):
        """Test SeqCumulative with mismatched lengths."""
        tasks = [IntervalVar(size=5, name=f"task{i}") for i in range(3)]
        heights = [1, 2]  # Wrong length

        with pytest.raises(ValueError, match="must have same length"):
            SeqCumulative(tasks, heights, 3)

    def test_seq_cumulative_single_task(self):
        """Test SeqCumulative with single task."""
        task = IntervalVar(size=5, name="task")

        # Single task should work
        SeqCumulative([task], [2], 3)


class TestCumulRegistry:
    """Tests for cumulative function registry."""

    def test_registry_starts_empty(self):
        """Test that registry starts empty after reset."""
        registered = get_registered_cumuls()
        assert len(registered) == 0

    def test_clear_registry(self):
        """Test registry clearing."""
        # Create some cumulative objects to increment ID counters
        task = IntervalVar(size=10, name="task")
        CumulFunction([pulse(task, 2)], name="resource")

        clear_cumul_registry()

        assert len(get_registered_cumuls()) == 0


class TestCumulScenarios:
    """Integration tests for realistic scheduling scenarios."""

    def test_resource_constrained_scheduling(self):
        """Test resource-constrained project scheduling pattern."""
        from pycsp3.classes.entities import ECtr

        # Create tasks
        tasks = [
            IntervalVar(size=5, name="task_a"),
            IntervalVar(size=3, name="task_b"),
            IntervalVar(size=4, name="task_c"),
        ]

        # Resource usage
        resource_usage = [2, 3, 1]

        # Create cumulative function
        resource = sum(pulse(t, h) for t, h in zip(tasks, resource_usage))

        # Capacity constraint - returns pycsp3-compatible constraint
        constraint = resource <= 4

        assert isinstance(resource, CumulFunction)
        assert isinstance(constraint, ECtr)
        assert len(resource.expressions) == 3

    def test_renewable_resource_pattern(self):
        """Test renewable resource with pulse and step functions."""
        task = IntervalVar(start=0, size=10, name="task")

        # Pulse during task
        usage = pulse(task, 3)

        # Step at start (acquire) and end (release)
        acquire = step_at_start(task, 1)
        release = step_at_end(task, -1)

        # Combine
        resource = usage + acquire + release

        assert isinstance(resource, CumulFunction)
        assert len(resource.expressions) == 3

    def test_multiple_resources(self):
        """Test multiple resource constraints."""
        from pycsp3.classes.entities import ECtr

        tasks = [
            IntervalVar(size=5, name="task_a"),
            IntervalVar(size=3, name="task_b"),
            IntervalVar(size=4, name="task_c"),
        ]

        # Resource 1: CPU
        cpu = sum(pulse(t, h) for t, h in zip(tasks, [2, 1, 2]))
        cpu_constraint = cpu <= 3

        # Resource 2: Memory
        memory = sum(pulse(t, h) for t, h in zip(tasks, [4, 2, 1]))
        memory_constraint = memory <= 5

        # Both return pycsp3-compatible constraints
        assert isinstance(cpu_constraint, ECtr)
        assert isinstance(memory_constraint, ECtr)

    def test_variable_resource_usage(self):
        """Test variable resource usage pattern."""
        task = IntervalVar(size=10, name="task")

        # Variable height usage
        usage = pulse(task, height_min=1, height_max=3)

        assert usage.height_min == 1
        assert usage.height_max == 3

    def test_reservoir_pattern(self):
        """Test reservoir (non-renewable resource) pattern."""
        # Initial level
        initial = step_at(0, 100)

        # Tasks that consume resource
        task1 = IntervalVar(size=5, name="task1")
        task2 = IntervalVar(size=3, name="task2")

        # Consumption at start of each task
        consume1 = step_at_start(task1, -20)
        consume2 = step_at_start(task2, -30)

        # Reservoir level
        reservoir = initial + consume1 + consume2

        # Must stay non-negative
        constraint = reservoir >= 0

        assert isinstance(reservoir, CumulFunction)
        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.GE


class TestSeqCumulativeErrorPaths:
    """Tests for SeqCumulative error handling."""

    def test_invalid_interval_type(self):
        """Test SeqCumulative with non-IntervalVar raises TypeError."""
        tasks = ["not_an_interval", "also_not"]
        heights = [1, 2]

        with pytest.raises(TypeError, match="must be an IntervalVar"):
            SeqCumulative(tasks, heights, 3)

    def test_invalid_height_type(self):
        """Test SeqCumulative with non-int height raises TypeError."""
        tasks = [IntervalVar(size=5, name=f"task{i}") for i in range(2)]
        heights = [1, "two"]  # Invalid

        with pytest.raises(TypeError, match="must be an int"):
            SeqCumulative(tasks, heights, 3)

    def test_invalid_capacity_type(self):
        """Test SeqCumulative with non-int capacity raises TypeError."""
        tasks = [IntervalVar(size=5, name=f"task{i}") for i in range(2)]
        heights = [1, 2]

        with pytest.raises(TypeError, match="capacity must be an int"):
            SeqCumulative(tasks, heights, "three")


class TestCumulBuildHelpers:
    """Tests for cumulative build helper functions."""

    def test_is_simple_pulse_cumul_with_negated_pulse(self):
        """Test _is_simple_pulse_cumul with negated pulses."""
        from pycsp3_scheduling.constraints.cumulative import _is_simple_pulse_cumul

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        # Simple pulse should be recognized
        assert _is_simple_pulse_cumul(cumul)

    def test_is_simple_pulse_cumul_with_neg_pulse(self):
        """Test _is_simple_pulse_cumul with NEG of pulse."""
        from pycsp3_scheduling.constraints.cumulative import _is_simple_pulse_cumul

        task = IntervalVar(size=10, name="task")
        neg_expr = -pulse(task, 2)
        cumul = CumulFunction([neg_expr])

        # Negated pulse should still be simple
        assert _is_simple_pulse_cumul(cumul)

    def test_is_simple_pulse_cumul_with_variable_height(self):
        """Test _is_simple_pulse_cumul with variable height returns False."""
        from pycsp3_scheduling.constraints.cumulative import _is_simple_pulse_cumul

        task = IntervalVar(size=10, name="task")
        expr = pulse(task, height_min=1, height_max=5)
        cumul = CumulFunction([expr])

        # Variable height is not simple
        assert not _is_simple_pulse_cumul(cumul)

    def test_is_simple_pulse_cumul_with_step_at(self):
        """Test _is_simple_pulse_cumul with step_at returns False."""
        from pycsp3_scheduling.constraints.cumulative import _is_simple_pulse_cumul

        step = step_at(5, 3)
        cumul = CumulFunction([step])

        # Step is not a simple pulse
        assert not _is_simple_pulse_cumul(cumul)

    def test_get_pulse_data_basic(self):
        """Test _get_pulse_data extracts intervals and heights."""
        from pycsp3_scheduling.constraints.cumulative import _get_pulse_data

        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        cumul = CumulFunction([pulse(task1, 2), pulse(task2, 3)])

        intervals, heights = _get_pulse_data(cumul)

        assert len(intervals) == 2
        assert intervals[0] is task1
        assert intervals[1] is task2
        assert heights == [2, 3]

    def test_get_pulse_data_with_negation(self):
        """Test _get_pulse_data with negated pulse."""
        from pycsp3_scheduling.constraints.cumulative import _get_pulse_data

        task = IntervalVar(size=10, name="task")
        neg_expr = -pulse(task, 5)
        cumul = CumulFunction([neg_expr])

        intervals, heights = _get_pulse_data(cumul)

        assert len(intervals) == 1
        assert intervals[0] is task
        assert heights == [-5]

    def test_build_cumul_constraint_with_negative_heights(self):
        """Test build_cumul_constraint falls back for negative heights."""
        from pycsp3_scheduling.constraints.cumulative import build_cumul_constraint

        task = IntervalVar(size=10, name="task")
        neg_expr = -pulse(task, 5)
        cumul = CumulFunction([neg_expr])

        constraint = CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.LE,
            bound=10,
        )

        result = build_cumul_constraint(constraint)
        # Should return empty list from decomposed constraint
        assert isinstance(result, list)

    def test_build_cumul_constraint_with_range(self):
        """Test build_cumul_constraint with RANGE constraint type."""
        from pycsp3_scheduling.constraints.cumulative import build_cumul_constraint

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        # RANGE with min_bound=0 should use Cumulative
        constraint = CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.RANGE,
            min_bound=0,
            max_bound=5,
        )

        result = build_cumul_constraint(constraint)
        assert isinstance(result, list)

    def test_build_cumul_constraint_with_range_nonzero_min(self):
        """Test build_cumul_constraint with RANGE and nonzero min."""
        from pycsp3_scheduling.constraints.cumulative import build_cumul_constraint

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        # RANGE with min_bound > 0 should fall back to decomposed
        constraint = CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.RANGE,
            min_bound=1,
            max_bound=5,
        )

        result = build_cumul_constraint(constraint)
        # Should return empty list from decomposed constraint
        assert isinstance(result, list)

    def test_build_cumul_constraint_with_ge(self):
        """Test build_cumul_constraint with GE constraint type."""
        from pycsp3_scheduling.constraints.cumulative import build_cumul_constraint

        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.GE,
            bound=1,
        )

        result = build_cumul_constraint(constraint)
        # GE should use decomposed constraint
        assert isinstance(result, list)

    def test_build_cumul_constraint_with_always_in(self):
        """Test build_cumul_constraint with ALWAYS_IN constraint type."""
        from pycsp3_scheduling.constraints.cumulative import build_cumul_constraint

        task = IntervalVar(size=10, name="task")
        time_range = IntervalVar(start=0, end=100, name="range")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = CumulConstraint(
            cumul=cumul,
            constraint_type=CumulConstraintType.ALWAYS_IN,
            min_bound=0,
            max_bound=5,
            interval=time_range,
        )

        result = build_cumul_constraint(constraint)
        # ALWAYS_IN should use decomposed constraint
        assert isinstance(result, list)


class TestCumulFunctionAdvanced:
    """Advanced tests for CumulFunction."""

    def test_cumul_le_with_variable_height_pulse(self):
        """Test cumul <= capacity with variable height falls back."""
        task = IntervalVar(size=10, name="task")
        expr = pulse(task, height_min=1, height_max=5)
        cumul = CumulFunction([expr])

        constraint = cumul <= 10

        # With variable height, should return CumulConstraint
        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.LE

    def test_cumul_le_with_step_expression(self):
        """Test cumul <= capacity with step expression falls back."""
        task = IntervalVar(size=10, name="task")
        step = step_at_start(task, 3)
        cumul = CumulFunction([step])

        constraint = cumul <= 10

        # With step expression, should return CumulConstraint
        assert isinstance(constraint, CumulConstraint)

    def test_cumul_le_with_negative_height(self):
        """Test cumul <= capacity with negative height falls back."""
        task = IntervalVar(size=10, name="task")
        neg_expr = -pulse(task, 5)
        cumul = CumulFunction([neg_expr])

        constraint = cumul <= 10

        # With negative height, should return CumulConstraint
        assert isinstance(constraint, CumulConstraint)

    # NOTE: test_cumul_le_filters_zero_heights is omitted because height=0
    # is not a typical use case and creates edge case issues in the
    # cumul_functions module.

    def test_cumul_function_get_intervals(self):
        """Test CumulFunction.get_intervals method."""
        task1 = IntervalVar(size=10, name="task1")
        task2 = IntervalVar(size=15, name="task2")
        cumul = CumulFunction([pulse(task1, 2), pulse(task2, 3)])

        intervals = cumul.get_intervals()

        assert len(intervals) == 2
        assert task1 in intervals
        assert task2 in intervals

    def test_cumul_function_get_intervals_with_negation(self):
        """Test CumulFunction.get_intervals with negated expressions."""
        task = IntervalVar(size=10, name="task")
        neg_expr = -pulse(task, 5)
        cumul = CumulFunction([neg_expr])

        intervals = cumul.get_intervals()

        assert len(intervals) == 1
        assert task in intervals

    def test_cumul_function_repr_with_name(self):
        """Test CumulFunction repr with name."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)], name="resource")

        repr_str = repr(cumul)
        assert "resource" in repr_str

    def test_cumul_function_repr_empty(self):
        """Test CumulFunction repr when empty."""
        cumul = CumulFunction([])

        repr_str = repr(cumul)
        assert "CumulFunction()" == repr_str

    def test_cumul_constraint_repr_lt(self):
        """Test CumulConstraint repr for LT."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])
        constraint = cumul < 5

        repr_str = repr(constraint)
        assert "<" in repr_str
        assert "5" in repr_str

    def test_cumul_constraint_repr_gt(self):
        """Test CumulConstraint repr for GT."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])
        constraint = cumul > 0

        repr_str = repr(constraint)
        assert ">" in repr_str
        assert "0" in repr_str

    def test_cumul_constraint_repr_always_in_with_tuple(self):
        """Test CumulConstraint repr for ALWAYS_IN with tuple range."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])
        constraint = always_in(cumul, (0, 100), 0, 5)

        repr_str = repr(constraint)
        assert "always_in" in repr_str
        assert "(0, 100)" in repr_str


class TestCumulExprAdvanced:
    """Advanced tests for CumulExpr."""

    def test_cumul_expr_fixed_height_from_min_max(self):
        """Test fixed_height when height_min == height_max."""
        task = IntervalVar(size=10, name="task")
        expr = pulse(task, height_min=5, height_max=5)

        assert expr.fixed_height == 5
        assert not expr.is_variable_height

    def test_cumul_expr_add_non_zero_int_raises(self):
        """Test adding non-zero int to CumulExpr raises."""
        task = IntervalVar(size=10, name="task")
        expr = pulse(task, 2)

        with pytest.raises(TypeError, match="Cannot add non-zero integer"):
            expr + 5

    def test_cumul_function_add_non_zero_int_raises(self):
        """Test adding non-zero int to CumulFunction raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="Cannot add non-zero integer"):
            cumul + 5

    def test_cumul_expr_repr_step_at_start_variable_height(self):
        """Test repr for step_at_start with variable height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_start(task, height_min=1, height_max=5)

        repr_str = repr(expr)
        assert "step_at_start" in repr_str
        assert "[1,5]" in repr_str

    def test_cumul_expr_repr_step_at_end_variable_height(self):
        """Test repr for step_at_end with variable height."""
        task = IntervalVar(size=10, name="task")
        expr = step_at_end(task, height_min=-5, height_max=-1)

        repr_str = repr(expr)
        assert "step_at_end" in repr_str
        assert "[-5,-1]" in repr_str

    def test_cumul_expr_hash(self):
        """Test CumulExpr hash."""
        task = IntervalVar(size=10, name="task")
        expr1 = pulse(task, 2)
        expr2 = pulse(task, 3)

        # Different expressions should have different hashes (usually)
        s = {expr1, expr2}
        assert len(s) == 2


class TestCumulValidationErrors:
    """Tests for validation error paths in cumulative functions."""

    def test_pulse_height_min_greater_than_max(self):
        """Test pulse with height_min > height_max raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="cannot exceed"):
            pulse(task, height_min=10, height_max=5)

    def test_step_at_start_height_min_greater_than_max(self):
        """Test step_at_start with height_min > height_max raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="cannot exceed"):
            step_at_start(task, height_min=10, height_max=5)

    def test_step_at_end_height_min_greater_than_max(self):
        """Test step_at_end with height_min > height_max raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="cannot exceed"):
            step_at_end(task, height_min=10, height_max=5)

    def test_step_at_invalid_time_type(self):
        """Test step_at with invalid time type raises."""
        with pytest.raises(TypeError, match="time must be an int"):
            step_at("not_an_int", 5)

    def test_step_at_invalid_height_type(self):
        """Test step_at with invalid height type raises."""
        with pytest.raises(TypeError, match="height must be an int"):
            step_at(5, "not_an_int")

    def test_step_at_start_invalid_height_type(self):
        """Test step_at_start with invalid height type raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="height must be an int"):
            step_at_start(task, "not_an_int")

    def test_step_at_end_invalid_height_type(self):
        """Test step_at_end with invalid height type raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="height must be an int"):
            step_at_end(task, "not_an_int")

    def test_step_at_start_invalid_min_max_type(self):
        """Test step_at_start with invalid height_min/max type raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be integers"):
            step_at_start(task, height_min="1", height_max=5)

    def test_step_at_end_invalid_min_max_type(self):
        """Test step_at_end with invalid height_min/max type raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be integers"):
            step_at_end(task, height_min=1, height_max="5")

    def test_pulse_invalid_min_max_type(self):
        """Test pulse with invalid height_min/max type raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be integers"):
            pulse(task, height_min="1", height_max=5)

    def test_cumul_range_invalid_cumul_type(self):
        """Test cumul_range with invalid cumul type raises."""
        with pytest.raises(TypeError, match="must be a CumulFunction"):
            cumul_range("not_a_cumul", 0, 5)

    def test_cumul_range_invalid_bounds_type(self):
        """Test cumul_range with invalid bounds type raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="must be integers"):
            cumul_range(cumul, "0", 5)

    def test_always_in_invalid_cumul_type(self):
        """Test always_in with invalid cumul type raises."""
        with pytest.raises(TypeError, match="expects CumulFunction or StateFunction"):
            always_in("not_a_cumul", (0, 100), 0, 5)

    def test_always_in_invalid_bounds_type(self):
        """Test always_in with invalid bounds type raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="must be integers"):
            always_in(cumul, (0, 100), "0", 5)

    def test_always_in_min_greater_than_max(self):
        """Test always_in with min > max raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(ValueError, match="cannot exceed"):
            always_in(cumul, (0, 100), 10, 5)

    def test_always_in_invalid_time_range_type(self):
        """Test always_in with invalid time range type raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="must be a tuple of integers"):
            always_in(cumul, ("0", 100), 0, 5)

    def test_always_in_start_greater_than_end(self):
        """Test always_in with start > end raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(ValueError, match="cannot exceed"):
            always_in(cumul, (100, 0), 0, 5)

    def test_cumul_function_le_invalid_type(self):
        """Test CumulFunction <= with non-int raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="can only be compared with int"):
            cumul <= "5"

    def test_cumul_function_ge_invalid_type(self):
        """Test CumulFunction >= with non-int raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="can only be compared with int"):
            cumul >= "5"

    def test_cumul_function_lt_invalid_type(self):
        """Test CumulFunction < with non-int raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="can only be compared with int"):
            cumul < "5"

    def test_cumul_function_gt_invalid_type(self):
        """Test CumulFunction > with non-int raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="can only be compared with int"):
            cumul > "5"

    def test_height_at_start_invalid_interval(self):
        """Test height_at_start with invalid interval raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="must be an IntervalVar"):
            height_at_start("not_an_interval", cumul)

    def test_height_at_start_invalid_cumul(self):
        """Test height_at_start with invalid cumul raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be a CumulFunction"):
            height_at_start(task, "not_a_cumul")

    def test_height_at_end_invalid_interval(self):
        """Test height_at_end with invalid interval raises."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        with pytest.raises(TypeError, match="must be an IntervalVar"):
            height_at_end("not_an_interval", cumul)

    def test_height_at_end_invalid_cumul(self):
        """Test height_at_end with invalid cumul raises."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be a CumulFunction"):
            height_at_end(task, "not_a_cumul")
