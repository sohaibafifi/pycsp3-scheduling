"""Tests for bounds constraints (release_date, deadline, time_window)."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    deadline,
    release_date,
    time_window,
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


class TestReleaseDate:
    """Tests for release_date constraint."""

    def test_basic_constraint(self):
        """release_date returns GE constraint."""
        task = IntervalVar(size=10, name="task")

        ctrs = release_date(task, 8)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.GE

    def test_optional_interval(self):
        """release_date handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = release_date(task, 8)

        assert len(ctrs) == 1
        # Should be OR with presence escape clause
        assert ctrs[0].type == TypeNode.OR

    def test_zero_release(self):
        """release_date with time=0."""
        task = IntervalVar(size=10, name="task")

        ctrs = release_date(task, 0)

        assert len(ctrs) == 1
        assert ctrs[0].type == TypeNode.GE

    def test_invalid_interval_type(self):
        """release_date rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            release_date("not_an_interval", 8)

    def test_invalid_time_type(self):
        """release_date rejects non-integer time."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="integer"):
            release_date(task, "8")


class TestDeadline:
    """Tests for deadline constraint."""

    def test_basic_constraint(self):
        """deadline returns LE constraint."""
        task = IntervalVar(size=10, name="task")

        ctrs = deadline(task, 50)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.LE

    def test_optional_interval(self):
        """deadline handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = deadline(task, 50)

        assert len(ctrs) == 1
        # Should be OR with presence escape clause
        assert ctrs[0].type == TypeNode.OR

    def test_invalid_interval_type(self):
        """deadline rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            deadline(123, 50)

    def test_invalid_time_type(self):
        """deadline rejects non-integer time."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="integer"):
            deadline(task, 50.5)


class TestTimeWindow:
    """Tests for time_window constraint."""

    def test_basic_constraint(self):
        """time_window returns release + deadline constraints."""
        task = IntervalVar(size=10, name="task")

        ctrs = time_window(task, earliest_start=8, latest_end=50)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 2
        # First should be GE (release), second should be LE (deadline)
        assert ctrs[0].type == TypeNode.GE
        assert ctrs[1].type == TypeNode.LE

    def test_optional_interval(self):
        """time_window handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = time_window(task, earliest_start=8, latest_end=50)

        assert len(ctrs) == 2
        # Both should be OR with presence escape clauses
        assert ctrs[0].type == TypeNode.OR
        assert ctrs[1].type == TypeNode.OR

    def test_same_start_end(self):
        """time_window with same earliest_start and latest_end."""
        task = IntervalVar(size=0, name="task")

        ctrs = time_window(task, earliest_start=10, latest_end=10)

        assert len(ctrs) == 2

    def test_invalid_interval_type(self):
        """time_window rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            time_window(None, earliest_start=8, latest_end=50)

    def test_invalid_earliest_start_type(self):
        """time_window rejects non-integer earliest_start."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="earliest_start"):
            time_window(task, earliest_start="8", latest_end=50)

    def test_invalid_latest_end_type(self):
        """time_window rejects non-integer latest_end."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="latest_end"):
            time_window(task, earliest_start=8, latest_end="50")

    def test_invalid_bounds_order(self):
        """time_window rejects earliest_start > latest_end."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="earliest_start.*<=.*latest_end"):
            time_window(task, earliest_start=50, latest_end=8)


class TestBoundsIntegration:
    """Integration tests for bounds constraints with pycsp3."""

    def test_satisfy_with_release_date(self):
        """Test release_date can be used with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")

        satisfy(release_date(task, 8))

    def test_satisfy_with_deadline(self):
        """Test deadline can be used with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")

        satisfy(deadline(task, 50))

    def test_satisfy_with_time_window(self):
        """Test time_window can be used with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")

        satisfy(time_window(task, earliest_start=8, latest_end=50))

    def test_combined_bounds(self):
        """Test combining bounds with other constraints."""
        from pycsp3 import satisfy
        from pycsp3_scheduling.constraints import chain

        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        # Tasks in chain, each with time window
        satisfy(
            chain(tasks),
            *[time_window(t, earliest_start=0, latest_end=100) for t in tasks],
        )
