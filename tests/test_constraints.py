"""Tests for scheduling constraints."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import ECtr, clear as clear_pycsp3
from pycsp3.classes.main.constraints import ConstraintNoOverlap
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import SeqNoOverlap, end_before_start
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

    def test_transition_matrix_not_supported(self):
        """transition_matrix is rejected for now."""
        task = IntervalVar(size=3, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(NotImplementedError, match="transition_matrix"):
            SeqNoOverlap(seq, transition_matrix=[[0]])

    def test_is_direct_not_supported(self):
        """is_direct is rejected for now."""
        task = IntervalVar(size=3, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(NotImplementedError, match="is_direct"):
            SeqNoOverlap(seq, is_direct=True)

    def test_invalid_sequence_type(self):
        """SeqNoOverlap rejects non-sequences."""
        with pytest.raises(TypeError, match="SequenceVar"):
            SeqNoOverlap(123)

    def test_invalid_interval_element(self):
        """SeqNoOverlap rejects non-IntervalVar elements."""
        with pytest.raises(TypeError, match="IntervalVar"):
            SeqNoOverlap([1, 2])

    def test_optional_interval_not_supported(self):
        """Optional intervals are rejected for now."""
        task = IntervalVar(size=3, optional=True, name="t1")
        seq = SequenceVar(intervals=[task], name="machine")

        with pytest.raises(NotImplementedError, match="Optional intervals"):
            SeqNoOverlap(seq)


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
