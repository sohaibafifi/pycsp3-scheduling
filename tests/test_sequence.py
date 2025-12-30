"""Tests for SequenceVar class."""

import pytest

from pycsp3_scheduling.variables import (
    IntervalVar,
    IntervalVarArray,
    SequenceVar,
    SequenceVarArray,
    clear_interval_registry,
    clear_sequence_registry,
)


@pytest.fixture(autouse=True)
def reset_registries():
    """Reset registries before each test."""
    clear_interval_registry()
    clear_sequence_registry()
    yield
    clear_interval_registry()
    clear_sequence_registry()


class TestSequenceVar:
    """Tests for SequenceVar class."""

    def test_basic_creation(self):
        """Test basic sequence variable creation."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")
        task3 = IntervalVar(size=8, name="t3")
        seq = SequenceVar(intervals=[task1, task2, task3], name="machine1")

        assert seq.name == "machine1"
        assert seq.size == 3
        assert len(seq) == 3
        assert not seq.has_types

    def test_with_types(self):
        """Test sequence with type identifiers."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")
        task3 = IntervalVar(size=8, name="t3")
        seq = SequenceVar(
            intervals=[task1, task2, task3],
            types=[0, 1, 0],
            name="machine1"
        )

        assert seq.has_types
        assert seq.get_type(0) == 0
        assert seq.get_type(1) == 1
        assert seq.get_type(2) == 0

    def test_get_intervals_by_type(self):
        """Test filtering intervals by type."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")
        task3 = IntervalVar(size=8, name="t3")
        seq = SequenceVar(
            intervals=[task1, task2, task3],
            types=[0, 1, 0],
            name="machine1"
        )

        type0_intervals = seq.get_intervals_by_type(0)
        assert len(type0_intervals) == 2
        assert task1 in type0_intervals
        assert task3 in type0_intervals

        type1_intervals = seq.get_intervals_by_type(1)
        assert len(type1_intervals) == 1
        assert task2 in type1_intervals

    def test_indexing(self):
        """Test interval access by index."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")
        seq = SequenceVar(intervals=[task1, task2], name="seq")

        assert seq[0] == task1
        assert seq[1] == task2
        assert seq.get_interval(0) == task1

    def test_iteration(self):
        """Test iteration over intervals."""
        tasks = [IntervalVar(size=10, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="seq")

        for i, interval in enumerate(seq):
            assert interval == tasks[i]

    def test_auto_name_generation(self):
        """Test automatic name generation."""
        task = IntervalVar(size=10, name="t")
        seq1 = SequenceVar(intervals=[task])
        seq2 = SequenceVar(intervals=[task])

        assert seq1.name != seq2.name
        assert seq1.name.startswith("_sequence_")

    def test_unique_ids(self):
        """Test that each sequence gets a unique ID."""
        task = IntervalVar(size=10, name="t")
        seq1 = SequenceVar(intervals=[task], name="s1")
        seq2 = SequenceVar(intervals=[task], name="s2")

        assert seq1._id != seq2._id

    def test_equality_by_id(self):
        """Test that equality is based on ID."""
        task = IntervalVar(size=10, name="t")
        seq1 = SequenceVar(intervals=[task], name="seq")
        seq2 = SequenceVar(intervals=[task], name="seq")  # Same name, different ID

        assert seq1 != seq2
        assert seq1 == seq1

    def test_hashable(self):
        """Test that sequences are hashable."""
        task = IntervalVar(size=10, name="t")
        seq1 = SequenceVar(intervals=[task], name="s1")
        seq2 = SequenceVar(intervals=[task], name="s2")

        s = {seq1, seq2}
        assert len(s) == 2

    def test_empty_sequence(self):
        """Test empty sequence creation."""
        seq = SequenceVar(intervals=[], name="empty")
        assert seq.size == 0
        assert len(seq) == 0

    def test_types_length_mismatch(self):
        """Test error when types length doesn't match intervals."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")

        with pytest.raises(ValueError, match="Length of types"):
            SequenceVar(
                intervals=[task1, task2],
                types=[0],  # Wrong length
                name="seq"
            )

    def test_negative_type(self):
        """Test error on negative type identifier."""
        task = IntervalVar(size=10, name="t")

        with pytest.raises(ValueError, match="non-negative integer"):
            SequenceVar(
                intervals=[task],
                types=[-1],
                name="seq"
            )

    def test_repr(self):
        """Test string representation."""
        task1 = IntervalVar(size=10, name="t1")
        task2 = IntervalVar(size=15, name="t2")
        seq = SequenceVar(intervals=[task1, task2], name="machine1")

        repr_str = repr(seq)
        assert "SequenceVar" in repr_str
        assert "machine1" in repr_str
        assert "t1" in repr_str
        assert "t2" in repr_str


class TestSequenceVarArray:
    """Tests for SequenceVarArray factory function."""

    def test_array_with_intervals(self):
        """Test array creation with intervals per sequence."""
        ops_m0 = IntervalVarArray(3, size_range=10, name="op_m0")
        ops_m1 = IntervalVarArray(3, size_range=15, name="op_m1")

        sequences = SequenceVarArray(
            2,
            intervals_per_sequence=[ops_m0, ops_m1],
            name="machine"
        )

        assert len(sequences) == 2
        assert sequences[0].name == "machine[0]"
        assert sequences[1].name == "machine[1]"
        assert sequences[0].size == 3
        assert sequences[1].size == 3

    def test_array_with_types(self):
        """Test array creation with types per sequence."""
        ops_m0 = IntervalVarArray(3, size_range=10, name="op_m0")
        ops_m1 = IntervalVarArray(3, size_range=15, name="op_m1")

        sequences = SequenceVarArray(
            2,
            intervals_per_sequence=[ops_m0, ops_m1],
            types_per_sequence=[[0, 1, 0], [1, 0, 1]],
            name="machine"
        )

        assert sequences[0].has_types
        assert sequences[1].has_types
        assert sequences[0].get_type(0) == 0
        assert sequences[1].get_type(0) == 1

    def test_empty_array(self):
        """Test array without intervals."""
        sequences = SequenceVarArray(3, name="machine")
        assert len(sequences) == 3
        for seq in sequences:
            assert seq.size == 0

    def test_size_mismatch_error(self):
        """Test error when intervals_per_sequence size doesn't match."""
        ops = IntervalVarArray(3, size_range=10, name="op")

        with pytest.raises(ValueError, match="must match size"):
            SequenceVarArray(
                2,
                intervals_per_sequence=[ops],  # Only 1, but size is 2
                name="machine"
            )
