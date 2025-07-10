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
        """Test cumul_range creates range constraint."""
        task = IntervalVar(size=10, name="task")
        cumul = CumulFunction([pulse(task, 2)])

        constraint = cumul_range(cumul, 0, 5)

        assert isinstance(constraint, CumulConstraint)
        assert constraint.constraint_type == CumulConstraintType.RANGE
        assert constraint.min_bound == 0
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

        # Should not raise
        SeqCumulative(tasks, heights, capacity)

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
