"""Tests for IntervalVar class."""

import pytest

from pycsp3_scheduling.variables import (
    INTERVAL_MIN,
    IntervalVar,
    IntervalVarArray,
    IntervalVarDict,
    clear_interval_registry,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the interval registry before each test."""
    clear_interval_registry()
    yield
    clear_interval_registry()


class TestIntervalVar:
    """Tests for IntervalVar class."""

    def test_basic_creation(self):
        """Test basic interval variable creation."""
        task = IntervalVar(size=10, name="task1")
        assert task.name == "task1"
        assert task.size_min == 10
        assert task.size_max == 10
        assert task.is_fixed_size
        assert not task.optional
        assert task.is_present

    def test_size_as_range(self):
        """Test interval with size range."""
        task = IntervalVar(size=(5, 20), name="task")
        assert task.size_min == 5
        assert task.size_max == 20
        assert not task.is_fixed_size

    def test_start_end_bounds(self):
        """Test start and end bounds."""
        task = IntervalVar(
            start=(0, 100),
            end=(10, 200),
            size=10,
            name="task"
        )
        assert task.start_min == 0
        assert task.start_max == 100
        assert task.end_min == 10
        assert task.end_max == 200

    def test_optional_interval(self):
        """Test optional interval creation."""
        task = IntervalVar(size=10, optional=True, name="opt")
        assert task.optional
        assert not task.is_present

    def test_is_present_property(self):
        """Test is_present property."""
        task = IntervalVar(size=10, name="task")
        assert task.is_present
        assert not task.is_optional

        opt_task = IntervalVar(size=10, optional=True, name="opt")
        assert not opt_task.is_present
        assert opt_task.is_optional

    def test_auto_name_generation(self):
        """Test automatic name generation."""
        task1 = IntervalVar(size=10)
        task2 = IntervalVar(size=10)
        assert task1.name != task2.name
        assert task1.name.startswith("_interval_")
        assert task2.name.startswith("_interval_")

    def test_unique_ids(self):
        """Test that each interval gets a unique ID."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=10, name="t2")
        assert task1._id != task2._id

    def test_equality_by_id(self):
        """Test that equality is based on ID."""
        task1 = IntervalVar(size=10, name="task")
        task2 = IntervalVar(size=10, name="task")  # Same name, different ID
        assert task1 != task2
        assert task1 == task1

    def test_hashable(self):
        """Test that intervals are hashable."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=10, name="t2")
        s = {task1, task2}
        assert len(s) == 2
        assert task1 in s
        assert task2 in s

    def test_length_defaults_to_size(self):
        """Test that length defaults to size."""
        task = IntervalVar(size=(5, 10), name="task")
        assert task.length_min == 5
        assert task.length_max == 10

    def test_explicit_length(self):
        """Test explicit length different from size."""
        task = IntervalVar(size=10, length=(8, 12), name="task")
        assert task.size_min == 10
        assert task.size_max == 10
        assert task.length_min == 8
        assert task.length_max == 12

    def test_intensity_normalization(self):
        """Test intensity step normalization and merging."""
        intensity = [(0, 0), (5, 0), (7, 3), (10, 3), (12, 1)]
        # Set explicit length to avoid warning
        task = IntervalVar(size=10, length=(10, 50), intensity=intensity, name="task")
        assert task.intensity == [(7, 3), (12, 1)]

        intensity = [(INTERVAL_MIN, 5), (10, 5), (20, 1)]
        task = IntervalVar(size=10, length=(10, 50), intensity=intensity, name="task2")
        assert task.intensity == [(0, 5), (20, 1)]

    def test_empty_intensity_becomes_none(self):
        """Test that all-zero intensity normalizes to None."""
        intensity = [(0, 0), (5, 0), (10, 0)]
        task = IntervalVar(size=10, intensity=intensity, name="task")
        assert task.intensity is None

    def test_negative_intensity_raises(self):
        """Test that negative intensity values raise an error."""
        with pytest.raises(ValueError, match="Intensity values must be non-negative"):
            IntervalVar(size=10, intensity=[(0, -5)], name="task")

    def test_invalid_intensity_steps(self):
        """Test intensity validation for step ordering."""
        with pytest.raises(ValueError, match="Intensity steps must be strictly increasing"):
            IntervalVar(size=10, intensity=[(5, 1), (3, 2)], name="task")

    def test_granularity_validation(self):
        """Test granularity validation."""
        with pytest.raises(ValueError, match="granularity must be positive"):
            IntervalVar(size=10, granularity=0, name="task")
        with pytest.raises(TypeError, match="granularity must be an int"):
            IntervalVar(size=10, granularity=1.5, name="task")

    def test_invalid_bounds_min_greater_than_max(self):
        """Test error on invalid bounds."""
        with pytest.raises(ValueError, match="Invalid start bounds"):
            IntervalVar(start=(100, 0), size=10, name="task")

    def test_invalid_negative_size(self):
        """Test error on negative size."""
        with pytest.raises(ValueError, match="Size cannot be negative"):
            IntervalVar(size=(-5, 10), name="task")

    def test_infeasible_bounds(self):
        """Test error on infeasible bounds."""
        with pytest.raises(ValueError, match="Infeasible bounds"):
            IntervalVar(start=(100, 100), end=(50, 50), size=10, name="task")

    def test_repr(self):
        """Test string representation."""
        task = IntervalVar(size=10, name="task1")
        repr_str = repr(task)
        assert "IntervalVar" in repr_str
        assert "task1" in repr_str
        assert "size=10" in repr_str


class TestIntervalVarArray:
    """Tests for IntervalVarArray factory function."""

    def test_1d_array(self):
        """Test 1D array creation."""
        tasks = IntervalVarArray(5, size_range=10, name="task")
        assert len(tasks) == 5
        for i, task in enumerate(tasks):
            assert isinstance(task, IntervalVar)
            assert task.name == f"task[{i}]"
            assert task.size_min == 10

    def test_2d_array(self):
        """Test 2D array creation."""
        tasks = IntervalVarArray((3, 4), size_range=(5, 20), name="op")
        assert len(tasks) == 3
        assert len(tasks[0]) == 4
        for i in range(3):
            for j in range(4):
                assert isinstance(tasks[i][j], IntervalVar)
                assert tasks[i][j].name == f"op[{i}][{j}]"
                assert tasks[i][j].size_min == 5
                assert tasks[i][j].size_max == 20

    def test_optional_array(self):
        """Test array with optional intervals."""
        tasks = IntervalVarArray(3, size_range=10, optional=True, name="task")
        for task in tasks:
            assert task.optional

    def test_with_start_end_bounds(self):
        """Test array with start/end bounds."""
        tasks = IntervalVarArray(
            3,
            start=(0, 100),
            end=(10, 200),
            size_range=10,
            name="task"
        )
        for task in tasks:
            assert task.start_min == 0
            assert task.start_max == 100
            assert task.end_min == 10
            assert task.end_max == 200


class TestIntervalVarDict:
    """Tests for IntervalVarDict factory function."""

    def test_string_keys(self):
        """Test dictionary with string keys."""
        tasks = IntervalVarDict(["A", "B", "C"], size_range=10, name="task")
        assert len(tasks) == 3
        assert "A" in tasks
        assert "B" in tasks
        assert "C" in tasks
        assert tasks["A"].name == "task[A]"
        assert tasks["A"].size_min == 10

    def test_int_keys(self):
        """Test dictionary with integer keys."""
        tasks = IntervalVarDict([1, 2, 3], size_range=15, name="job")
        assert len(tasks) == 3
        assert 1 in tasks
        assert tasks[1].name == "job[1]"

    def test_tuple_keys(self):
        """Test dictionary with tuple keys."""
        keys = [(0, 0), (0, 1), (1, 0)]
        tasks = IntervalVarDict(keys, size_range=10, name="cell")
        assert len(tasks) == 3
        assert (0, 0) in tasks
        assert tasks[(0, 1)].name == "cell[(0, 1)]"
