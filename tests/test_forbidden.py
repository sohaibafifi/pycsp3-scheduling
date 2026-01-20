"""Tests for forbidden time constraints."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    forbid_end,
    forbid_extent,
    forbid_start,
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


class TestForbidStart:
    """Tests for forbid_start constraint."""

    def test_basic_constraint(self):
        """forbid_start returns constraint nodes."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_start(task, [(12, 13), (17, 24)])

        assert isinstance(ctrs, list)
        assert len(ctrs) == 2
        for ctr in ctrs:
            assert isinstance(ctr, Node)
            assert ctr.type == TypeNode.OR

    def test_single_period(self):
        """forbid_start with single forbidden period."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_start(task, [(5, 10)])

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "or(" in ctr_str
        assert "lt(" in ctr_str
        assert "ge(" in ctr_str

    def test_empty_periods(self):
        """forbid_start with empty periods list returns empty."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_start(task, [])

        assert ctrs == []

    def test_optional_interval(self):
        """forbid_start handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = forbid_start(task, [(5, 10)])

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        # Should include presence escape clause
        assert "iv_p_" in ctr_str

    def test_invalid_interval_type(self):
        """forbid_start rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            forbid_start("not_an_interval", [(5, 10)])

    def test_invalid_period_format(self):
        """forbid_start rejects malformed periods."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="tuple"):
            forbid_start(task, [(5,)])

    def test_invalid_period_order(self):
        """forbid_start rejects periods where start >= end."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="start < end"):
            forbid_start(task, [(10, 5)])


class TestForbidEnd:
    """Tests for forbid_end constraint."""

    def test_basic_constraint(self):
        """forbid_end returns constraint nodes."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_end(task, [(12, 13)])

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.OR

    def test_multiple_periods(self):
        """forbid_end with multiple forbidden periods."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_end(task, [(5, 10), (15, 20), (25, 30)])

        assert len(ctrs) == 3

    def test_optional_interval(self):
        """forbid_end handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = forbid_end(task, [(5, 10)])

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "iv_p_" in ctr_str

    def test_invalid_interval_type(self):
        """forbid_end rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            forbid_end(123, [(5, 10)])


class TestForbidExtent:
    """Tests for forbid_extent constraint."""

    def test_basic_constraint(self):
        """forbid_extent returns constraint nodes."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_extent(task, [(12, 13)])

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.OR

    def test_multiple_periods(self):
        """forbid_extent with multiple forbidden periods."""
        task = IntervalVar(size=10, name="task")

        ctrs = forbid_extent(task, [(5, 10), (20, 25)])

        assert len(ctrs) == 2

    def test_optional_interval(self):
        """forbid_extent handles optional intervals."""
        task = IntervalVar(size=10, optional=True, name="task")

        ctrs = forbid_extent(task, [(5, 10)])

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "iv_p_" in ctr_str

    def test_invalid_interval_type(self):
        """forbid_extent rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            forbid_extent(None, [(5, 10)])


class TestForbiddenIntegration:
    """Integration tests for forbidden constraints with pycsp3."""

    def test_satisfy_with_forbidden(self):
        """Test forbidden constraints can be used with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")

        # Should not raise
        satisfy(forbid_start(task, [(12, 13)]))
        satisfy(forbid_end(task, [(17, 18)]))
        satisfy(forbid_extent(task, [(20, 25)]))
