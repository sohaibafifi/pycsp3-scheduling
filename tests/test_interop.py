"""Tests for interop module."""

from __future__ import annotations

import pytest

from pycsp3_scheduling import IntervalVar
from pycsp3_scheduling.variables.interval import clear_interval_registry
from pycsp3_scheduling.interop import (
    IntervalValue,
    ModelStatistics,
    SolutionStatistics,
    start_time,
    end_time,
    presence_time,
    model_statistics,
)


@pytest.fixture(autouse=True)
def reset_registries():
    """Reset registries before each test."""
    clear_interval_registry()
    from pycsp3_scheduling.functions.cumul_functions import clear_cumul_registry
    from pycsp3_scheduling.functions.state_functions import clear_state_function_registry
    from pycsp3_scheduling.variables.sequence import clear_sequence_registry

    clear_cumul_registry()
    clear_state_function_registry()
    clear_sequence_registry()
    yield
    clear_interval_registry()
    clear_cumul_registry()
    clear_state_function_registry()
    clear_sequence_registry()


class TestStartEndPresenceTime:
    """Tests for start_time, end_time, presence_time functions."""

    def test_start_time_basic(self):
        """Test start_time returns pycsp3 variable."""
        task = IntervalVar(size=10, name="task")
        result = start_time(task)
        # Should return a pycsp3 variable
        assert result is not None
        assert hasattr(result, "dom")

    def test_start_time_invalid_input(self):
        """Test start_time raises on invalid input."""
        with pytest.raises(TypeError, match="expects an IntervalVar"):
            start_time("not_an_interval")

    # NOTE: test_end_time_basic is omitted because pycsp3 has issues with
    # Variable + int arithmetic outside of a full model context.

    def test_end_time_invalid_input(self):
        """Test end_time raises on invalid input."""
        with pytest.raises(TypeError, match="expects an IntervalVar"):
            end_time(123)

    def test_presence_time_basic(self):
        """Test presence_time returns pycsp3 variable for optional interval."""
        task = IntervalVar(size=10, optional=True, name="task")
        result = presence_time(task)
        assert result is not None

    def test_presence_time_invalid_input(self):
        """Test presence_time raises on invalid input."""
        with pytest.raises(TypeError, match="expects an IntervalVar"):
            presence_time([1, 2, 3])


class TestIntervalValue:
    """Tests for IntervalValue dataclass."""

    def test_basic_creation(self):
        """Test basic IntervalValue creation."""
        val = IntervalValue(start=10, length=5, present=True, name="task")
        assert val.start == 10
        assert val.length == 5
        assert val.end == 15
        assert val.present is True
        assert val.name == "task"

    def test_end_property(self):
        """Test end is computed correctly."""
        val = IntervalValue(start=0, length=20)
        assert val.end == 20

        val2 = IntervalValue(start=50, length=10)
        assert val2.end == 60

    def test_getitem_start(self):
        """Test dict-like access for start."""
        val = IntervalValue(start=10, length=5)
        assert val["start"] == 10

    def test_getitem_end(self):
        """Test dict-like access for end."""
        val = IntervalValue(start=10, length=5)
        assert val["end"] == 15

    def test_getitem_length(self):
        """Test dict-like access for length."""
        val = IntervalValue(start=10, length=5)
        assert val["length"] == 5

    def test_getitem_present(self):
        """Test dict-like access for present."""
        val = IntervalValue(start=10, length=5, present=True)
        assert val["present"] is True

    def test_getitem_name(self):
        """Test dict-like access for name."""
        val = IntervalValue(start=10, length=5, name="test")
        assert val["name"] == "test"

    def test_getitem_invalid_key(self):
        """Test dict-like access with invalid key raises KeyError."""
        val = IntervalValue(start=10, length=5)
        with pytest.raises(KeyError):
            _ = val["invalid"]

    def test_iter(self):
        """Test iteration over keys."""
        val = IntervalValue(start=10, length=5)
        keys = list(val)
        assert keys == ["start", "end", "length", "present", "name"]

    def test_len(self):
        """Test length is 5."""
        val = IntervalValue(start=10, length=5)
        assert len(val) == 5

    def test_repr_with_name(self):
        """Test repr with name."""
        val = IntervalValue(start=10, length=5, name="task")
        repr_str = repr(val)
        assert "IntervalValue" in repr_str
        assert "name='task'" in repr_str
        assert "start=10" in repr_str
        assert "end=15" in repr_str

    def test_repr_without_name(self):
        """Test repr without name."""
        val = IntervalValue(start=10, length=5)
        repr_str = repr(val)
        assert "IntervalValue" in repr_str
        assert "start=10" in repr_str
        assert "name=" not in repr_str

    def test_to_dict(self):
        """Test to_dict method."""
        val = IntervalValue(start=10, length=5, present=True, name="task")
        d = val.to_dict()
        assert d == {
            "start": 10,
            "end": 15,
            "length": 5,
            "present": True,
            "name": "task",
        }

    def test_default_values(self):
        """Test default values."""
        val = IntervalValue(start=0, length=10)
        assert val.present is True
        assert val.name is None


class TestModelStatistics:
    """Tests for ModelStatistics dataclass."""

    def test_basic_creation(self):
        """Test basic creation."""
        stats = ModelStatistics(
            nb_interval_vars=10,
            nb_optional_interval_vars=3,
            nb_sequences=2,
            nb_sequences_with_types=1,
            nb_cumul_functions=4,
            nb_state_functions=1,
        )
        assert stats.nb_interval_vars == 10
        assert stats.nb_optional_interval_vars == 3
        assert stats.nb_sequences == 2
        assert stats.nb_sequences_with_types == 1
        assert stats.nb_cumul_functions == 4
        assert stats.nb_state_functions == 1

    def test_getitem_nb_interval_vars(self):
        """Test dict-like access."""
        stats = ModelStatistics(
            nb_interval_vars=5,
            nb_optional_interval_vars=2,
            nb_sequences=1,
            nb_sequences_with_types=0,
            nb_cumul_functions=3,
            nb_state_functions=0,
        )
        assert stats["nb_interval_vars"] == 5
        assert stats["nb_optional_interval_vars"] == 2
        assert stats["nb_sequences"] == 1
        assert stats["nb_sequences_with_types"] == 0
        assert stats["nb_cumul_functions"] == 3
        assert stats["nb_state_functions"] == 0

    def test_getitem_invalid_key(self):
        """Test invalid key raises KeyError."""
        stats = ModelStatistics(
            nb_interval_vars=0,
            nb_optional_interval_vars=0,
            nb_sequences=0,
            nb_sequences_with_types=0,
            nb_cumul_functions=0,
            nb_state_functions=0,
        )
        with pytest.raises(KeyError):
            _ = stats["invalid_key"]

    def test_iter(self):
        """Test iteration over keys."""
        stats = ModelStatistics(
            nb_interval_vars=0,
            nb_optional_interval_vars=0,
            nb_sequences=0,
            nb_sequences_with_types=0,
            nb_cumul_functions=0,
            nb_state_functions=0,
        )
        keys = list(stats)
        assert keys == [
            "nb_interval_vars",
            "nb_optional_interval_vars",
            "nb_sequences",
            "nb_sequences_with_types",
            "nb_cumul_functions",
            "nb_state_functions",
        ]

    def test_len(self):
        """Test length is 6."""
        stats = ModelStatistics(
            nb_interval_vars=0,
            nb_optional_interval_vars=0,
            nb_sequences=0,
            nb_sequences_with_types=0,
            nb_cumul_functions=0,
            nb_state_functions=0,
        )
        assert len(stats) == 6

    def test_repr(self):
        """Test repr."""
        stats = ModelStatistics(
            nb_interval_vars=5,
            nb_optional_interval_vars=2,
            nb_sequences=1,
            nb_sequences_with_types=0,
            nb_cumul_functions=3,
            nb_state_functions=1,
        )
        repr_str = repr(stats)
        assert "ModelStatistics" in repr_str
        assert "nb_interval_vars=5" in repr_str

    def test_to_dict(self):
        """Test to_dict method."""
        stats = ModelStatistics(
            nb_interval_vars=5,
            nb_optional_interval_vars=2,
            nb_sequences=1,
            nb_sequences_with_types=0,
            nb_cumul_functions=3,
            nb_state_functions=1,
        )
        d = stats.to_dict()
        assert d == {
            "nb_interval_vars": 5,
            "nb_optional_interval_vars": 2,
            "nb_sequences": 1,
            "nb_sequences_with_types": 0,
            "nb_cumul_functions": 3,
            "nb_state_functions": 1,
        }


class TestSolutionStatistics:
    """Tests for SolutionStatistics dataclass."""

    def test_basic_creation(self):
        """Test basic creation."""
        stats = SolutionStatistics(
            status="SAT",
            objective_value=100,
            solve_time=1.5,
            nb_interval_vars=10,
            nb_intervals_present=8,
            nb_intervals_absent=2,
            min_start=0,
            max_end=50,
            makespan=50,
            span=50,
        )
        assert stats.status == "SAT"
        assert stats.objective_value == 100
        assert stats.solve_time == 1.5
        assert stats.nb_interval_vars == 10
        assert stats.nb_intervals_present == 8
        assert stats.nb_intervals_absent == 2
        assert stats.min_start == 0
        assert stats.max_end == 50
        assert stats.makespan == 50
        assert stats.span == 50

    def test_getitem_all_keys(self):
        """Test dict-like access for all keys."""
        stats = SolutionStatistics(
            status="OPTIMUM",
            objective_value=42,
            solve_time=2.0,
            nb_interval_vars=5,
            nb_intervals_present=3,
            nb_intervals_absent=2,
            min_start=10,
            max_end=100,
            makespan=100,
            span=90,
        )
        assert stats["status"] == "OPTIMUM"
        assert stats["objective_value"] == 42
        assert stats["solve_time"] == 2.0
        assert stats["nb_interval_vars"] == 5
        assert stats["nb_intervals_present"] == 3
        assert stats["nb_intervals_absent"] == 2
        assert stats["min_start"] == 10
        assert stats["max_end"] == 100
        assert stats["makespan"] == 100
        assert stats["span"] == 90

    def test_getitem_invalid_key(self):
        """Test invalid key raises KeyError."""
        stats = SolutionStatistics(
            status=None,
            objective_value=None,
            solve_time=None,
            nb_interval_vars=0,
            nb_intervals_present=0,
            nb_intervals_absent=0,
            min_start=None,
            max_end=None,
            makespan=None,
            span=None,
        )
        with pytest.raises(KeyError):
            _ = stats["invalid"]

    def test_iter(self):
        """Test iteration over keys."""
        stats = SolutionStatistics(
            status=None,
            objective_value=None,
            solve_time=None,
            nb_interval_vars=0,
            nb_intervals_present=0,
            nb_intervals_absent=0,
            min_start=None,
            max_end=None,
            makespan=None,
            span=None,
        )
        keys = list(stats)
        assert keys == [
            "status",
            "objective_value",
            "solve_time",
            "nb_interval_vars",
            "nb_intervals_present",
            "nb_intervals_absent",
            "min_start",
            "max_end",
            "makespan",
            "span",
        ]

    def test_len(self):
        """Test length is 10."""
        stats = SolutionStatistics(
            status=None,
            objective_value=None,
            solve_time=None,
            nb_interval_vars=0,
            nb_intervals_present=0,
            nb_intervals_absent=0,
            min_start=None,
            max_end=None,
            makespan=None,
            span=None,
        )
        assert len(stats) == 10

    def test_repr(self):
        """Test repr."""
        stats = SolutionStatistics(
            status="SAT",
            objective_value=100,
            solve_time=1.5,
            nb_interval_vars=10,
            nb_intervals_present=8,
            nb_intervals_absent=2,
            min_start=0,
            max_end=50,
            makespan=50,
            span=50,
        )
        repr_str = repr(stats)
        assert "SolutionStatistics" in repr_str
        assert "status=SAT" in repr_str

    def test_to_dict(self):
        """Test to_dict method."""
        stats = SolutionStatistics(
            status="SAT",
            objective_value=100,
            solve_time=1.5,
            nb_interval_vars=10,
            nb_intervals_present=8,
            nb_intervals_absent=2,
            min_start=0,
            max_end=50,
            makespan=50,
            span=50,
        )
        d = stats.to_dict()
        assert d["status"] == "SAT"
        assert d["objective_value"] == 100
        assert d["span"] == 50


class TestModelStatisticsFunction:
    """Tests for model_statistics function."""

    def test_empty_model(self):
        """Test model_statistics on empty model."""
        stats = model_statistics()
        assert stats.nb_interval_vars == 0
        assert stats.nb_optional_interval_vars == 0
        assert stats.nb_sequences == 0
        assert stats.nb_cumul_functions == 0

    def test_with_intervals(self):
        """Test model_statistics with registered intervals."""
        _ = IntervalVar(size=10, name="t1")
        _ = IntervalVar(size=10, name="t2")
        _ = IntervalVar(size=10, optional=True, name="t3")

        stats = model_statistics()
        assert stats.nb_interval_vars == 3
        assert stats.nb_optional_interval_vars == 1

    def test_with_sequences(self):
        """Test model_statistics with sequences."""
        from pycsp3_scheduling.variables.sequence import SequenceVar

        t1 = IntervalVar(size=10, name="t1")
        t2 = IntervalVar(size=10, name="t2")
        _ = SequenceVar(intervals=[t1, t2], name="seq1")
        _ = SequenceVar(intervals=[t1, t2], types=[0, 1], name="seq2")

        stats = model_statistics()
        assert stats.nb_sequences == 2
        assert stats.nb_sequences_with_types == 1

    def test_with_cumul_functions(self):
        """Test model_statistics with cumulative functions."""
        from pycsp3_scheduling.functions.cumul_functions import (
            CumulFunction,
            pulse,
            register_cumul,
        )

        t1 = IntervalVar(size=10, name="t1")
        cumul = CumulFunction([pulse(t1, 2)], name="resource")
        register_cumul(cumul)

        stats = model_statistics()
        assert stats.nb_cumul_functions == 1

    def test_with_state_functions(self):
        """Test model_statistics with state functions."""
        from pycsp3_scheduling.functions.state_functions import (
            StateFunction,
            _register_state_function,
        )

        state = StateFunction(name="machine_state")
        _register_state_function(state)

        stats = model_statistics()
        assert stats.nb_state_functions == 1
