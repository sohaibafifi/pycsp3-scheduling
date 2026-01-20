"""Tests for chain constraints."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import chain, strict_chain
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


class TestChain:
    """Tests for chain constraint."""

    def test_basic_chain(self):
        """chain returns precedence constraints."""
        intervals = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(3)]

        ctrs = chain(intervals)

        # Should have n-1 constraints
        assert len(ctrs) == 2
        for ctr in ctrs:
            assert isinstance(ctr, Node)
            assert ctr.type == TypeNode.LE

    def test_chain_with_uniform_delay(self):
        """chain with uniform delay."""
        intervals = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]

        ctrs = chain(intervals, delays=2)

        assert len(ctrs) == 2
        for ctr in ctrs:
            ctr_str = str(ctrs[0])
            assert "add(" in ctr_str

    def test_chain_with_variable_delays(self):
        """chain with variable delays."""
        intervals = [IntervalVar(size=5, name=f"t{i}") for i in range(4)]

        ctrs = chain(intervals, delays=[1, 2, 3])

        assert len(ctrs) == 3

    def test_chain_with_optional_intervals(self):
        """chain handles optional intervals."""
        intervals = [IntervalVar(size=5, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = chain(intervals)

        assert len(ctrs) == 2
        for ctr in ctrs:
            assert ctr.type == TypeNode.OR  # Has presence escape clause

    def test_chain_single_interval(self):
        """chain with single interval raises error."""
        intervals = [IntervalVar(size=5, name="t0")]

        with pytest.raises(ValueError, match="at least 2"):
            chain(intervals)

    def test_chain_wrong_delays_length(self):
        """chain with wrong delays length raises error."""
        intervals = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]

        with pytest.raises(ValueError, match="length"):
            chain(intervals, delays=[1])  # Should be 2

    def test_chain_invalid_interval_type(self):
        """chain rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            chain(["a", "b"])


class TestStrictChain:
    """Tests for strict_chain constraint."""

    def test_basic_strict_chain(self):
        """strict_chain returns equality constraints."""
        intervals = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(3)]

        ctrs = strict_chain(intervals)

        # Should have n-1 constraints
        assert len(ctrs) == 2
        for ctr in ctrs:
            assert isinstance(ctr, Node)
            assert ctr.type == TypeNode.EQ

    def test_strict_chain_with_delay(self):
        """strict_chain with uniform delay."""
        intervals = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]

        ctrs = strict_chain(intervals, delays=2)

        assert len(ctrs) == 2
        for ctr in ctrs:
            assert ctr.type == TypeNode.EQ

    def test_strict_chain_with_optional_intervals(self):
        """strict_chain handles optional intervals."""
        intervals = [IntervalVar(size=5, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = strict_chain(intervals)

        assert len(ctrs) == 2
        for ctr in ctrs:
            assert ctr.type == TypeNode.OR  # Has presence escape clause


class TestChainIntegration:
    """Integration tests for chain constraints with pycsp3."""

    def test_satisfy_with_chain(self):
        """Test chain constraint can be used with satisfy()."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(4)]

        satisfy(chain(tasks))

    def test_satisfy_with_strict_chain(self):
        """Test strict_chain constraint can be used with satisfy()."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(4)]

        satisfy(strict_chain(tasks))
