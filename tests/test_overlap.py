"""Tests for overlap and disjunctive constraints."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    disjunctive,
    must_overlap,
    no_overlap_pairwise,
    overlap_at_least,
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


class TestMustOverlap:
    """Tests for must_overlap constraint."""

    def test_basic_constraint(self):
        """must_overlap returns AND constraint."""
        a = IntervalVar(size=10, name="a")
        b = IntervalVar(size=10, name="b")

        ctrs = must_overlap(a, b)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.AND

    def test_optional_intervals(self):
        """must_overlap handles optional intervals."""
        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = must_overlap(a, b)

        assert len(ctrs) == 1
        # Should be OR with presence escape clauses
        assert ctrs[0].type == TypeNode.OR

    def test_invalid_interval_type(self):
        """must_overlap rejects non-IntervalVar."""
        a = IntervalVar(size=10, name="a")

        with pytest.raises(TypeError, match="IntervalVar"):
            must_overlap(a, "not_interval")


class TestOverlapAtLeast:
    """Tests for overlap_at_least constraint."""

    def test_basic_constraint(self):
        """overlap_at_least returns GE constraint."""
        a = IntervalVar(size=60, name="a")
        b = IntervalVar(size=60, name="b")

        ctrs = overlap_at_least(a, b, 30)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        assert isinstance(ctrs[0], Node)
        assert ctrs[0].type == TypeNode.GE

    def test_zero_overlap(self):
        """overlap_at_least with 0 returns empty."""
        a = IntervalVar(size=10, name="a")
        b = IntervalVar(size=10, name="b")

        ctrs = overlap_at_least(a, b, 0)

        assert ctrs == []

    def test_optional_intervals(self):
        """overlap_at_least handles optional intervals."""
        a = IntervalVar(size=60, optional=True, name="a")
        b = IntervalVar(size=60, optional=True, name="b")

        ctrs = overlap_at_least(a, b, 30)

        assert len(ctrs) == 1
        assert ctrs[0].type == TypeNode.OR

    def test_invalid_min_overlap(self):
        """overlap_at_least rejects negative min_overlap."""
        a = IntervalVar(size=10, name="a")
        b = IntervalVar(size=10, name="b")

        with pytest.raises(ValueError, match="non-negative"):
            overlap_at_least(a, b, -1)

    def test_invalid_min_overlap_type(self):
        """overlap_at_least rejects non-int min_overlap."""
        a = IntervalVar(size=10, name="a")
        b = IntervalVar(size=10, name="b")

        with pytest.raises(TypeError, match="integer"):
            overlap_at_least(a, b, "30")


class TestNoOverlapPairwise:
    """Tests for no_overlap_pairwise constraint."""

    def test_basic_constraint(self):
        """no_overlap_pairwise returns OR constraints."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        ctrs = no_overlap_pairwise(intervals)

        # n*(n-1)/2 = 3 constraints for 3 intervals
        assert len(ctrs) == 3
        for ctr in ctrs:
            assert isinstance(ctr, Node)
            assert ctr.type == TypeNode.OR

    def test_single_interval(self):
        """no_overlap_pairwise with single interval returns empty."""
        intervals = [IntervalVar(size=10, name="t0")]

        ctrs = no_overlap_pairwise(intervals)

        assert ctrs == []

    def test_optional_intervals(self):
        """no_overlap_pairwise handles optional intervals."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = no_overlap_pairwise(intervals)

        assert len(ctrs) == 3
        for ctr in ctrs:
            assert ctr.type == TypeNode.OR

    def test_invalid_interval_type(self):
        """no_overlap_pairwise rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            no_overlap_pairwise(["a", "b"])


class TestDisjunctive:
    """Tests for disjunctive constraint."""

    def test_basic_constraint(self):
        """disjunctive returns OR constraints (pairwise)."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]

        ctrs = disjunctive(intervals)

        # Same as no_overlap_pairwise when no transition times
        assert len(ctrs) == 3
        for ctr in ctrs:
            assert isinstance(ctr, Node)
            assert ctr.type == TypeNode.OR

    def test_with_transition_times(self):
        """disjunctive with transition times."""
        intervals = [IntervalVar(size=10, name=f"t{i}") for i in range(2)]
        transition = [[0, 5], [3, 0]]

        ctrs = disjunctive(intervals, transition_times=transition)

        assert len(ctrs) == 1

    def test_single_interval(self):
        """disjunctive with single interval returns empty."""
        intervals = [IntervalVar(size=10, name="t0")]

        ctrs = disjunctive(intervals)

        assert ctrs == []

    def test_optional_intervals(self):
        """disjunctive handles optional intervals."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = disjunctive(intervals)

        assert len(ctrs) == 3


class TestOverlapIntegration:
    """Integration tests for overlap constraints with pycsp3."""

    def test_satisfy_with_overlap(self):
        """Test overlap constraints can be used with satisfy()."""
        from pycsp3 import satisfy

        a = IntervalVar(size=60, name="a")
        b = IntervalVar(size=60, name="b")

        satisfy(must_overlap(a, b))
        satisfy(overlap_at_least(a, b, 30))

    def test_satisfy_with_disjunctive(self):
        """Test disjunctive constraint can be used with satisfy()."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(4)]

        satisfy(disjunctive(tasks))

    def test_satisfy_with_no_overlap_pairwise(self):
        """Test no_overlap_pairwise can be used with satisfy()."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(4)]

        satisfy(no_overlap_pairwise(tasks))
