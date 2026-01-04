"""Tests for sequence constraints and expressions (Phase 5)."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import ECtr, clear as clear_pycsp3
from pycsp3.classes.main.constraints import ConstraintNoOverlap
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    SeqNoOverlap,
    before,
    first,
    last,
    previous,
    same_common_subsequence,
    same_sequence,
)
from pycsp3_scheduling.constraints._pycsp3 import clear_pycsp3_cache
from pycsp3_scheduling.expressions import (
    end_of_next,
    end_of_prev,
    length_of_next,
    length_of_prev,
    size_of_next,
    size_of_prev,
    start_of_next,
    start_of_prev,
    type_of_next,
    type_of_prev,
)
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


# =============================================================================
# SeqNoOverlap Tests
# =============================================================================


class TestSeqNoOverlap:
    """Tests for SeqNoOverlap constraint with transition matrix."""

    def test_basic_no_overlap(self):
        """Basic SeqNoOverlap without transitions."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        ctr = SeqNoOverlap(tasks)
        assert isinstance(ctr, ECtr)
        assert isinstance(ctr.constraint, ConstraintNoOverlap)

    def test_empty_sequence(self):
        """Empty sequence returns empty constraint list."""
        result = SeqNoOverlap([])
        assert result == []

    def test_with_sequence_var(self):
        """SeqNoOverlap accepts SequenceVar."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        ctr = SeqNoOverlap(seq)
        assert isinstance(ctr, ECtr)

    def test_transition_matrix_basic(self):
        """SeqNoOverlap with transition matrix returns list of constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, types=[0, 1, 0], name="machine")
        matrix = [[0, 5], [3, 0]]  # Setup times between types
        
        result = SeqNoOverlap(seq, transition_matrix=matrix)
        
        assert isinstance(result, list)
        assert len(result) > 1  # NoOverlap + transition constraints

    def test_transition_matrix_requires_sequence_var(self):
        """transition_matrix requires SequenceVar with types."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        matrix = [[0, 5], [3, 0]]
        
        with pytest.raises(ValueError, match="requires a SequenceVar with types"):
            SeqNoOverlap(tasks, transition_matrix=matrix)

    def test_transition_matrix_requires_types(self):
        """transition_matrix requires SequenceVar with types defined."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")  # No types
        matrix = [[0, 5], [3, 0]]
        
        with pytest.raises(ValueError, match="requires a SequenceVar with types"):
            SeqNoOverlap(seq, transition_matrix=matrix)

    def test_transition_matrix_dimension_validation(self):
        """transition_matrix dimensions must match types."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, types=[0, 1, 2], name="machine")
        matrix = [[0, 5], [3, 0]]  # Only 2 types, but we have type 2
        
        with pytest.raises(ValueError, match="at least 3 rows"):
            SeqNoOverlap(seq, transition_matrix=matrix)

    def test_transition_matrix_row_validation(self):
        """transition_matrix rows must be lists."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        seq = SequenceVar(intervals=tasks, types=[0, 1], name="machine")
        matrix = [[0, 5], "invalid"]
        
        with pytest.raises(TypeError, match="must be a list"):
            SeqNoOverlap(seq, transition_matrix=matrix)

    def test_transition_matrix_column_validation(self):
        """transition_matrix columns must have correct length."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        seq = SequenceVar(intervals=tasks, types=[0, 1], name="machine")
        matrix = [[0], [3, 0]]  # First row too short
        
        with pytest.raises(ValueError, match="at least 2 columns"):
            SeqNoOverlap(seq, transition_matrix=matrix)

    def test_transition_matrix_type_validation(self):
        """transition_matrix must be a list."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        seq = SequenceVar(intervals=tasks, types=[0, 1], name="machine")
        
        with pytest.raises(TypeError, match="must be a 2D list"):
            SeqNoOverlap(seq, transition_matrix="not a list")


# =============================================================================
# Sequence Ordering Constraints Tests
# =============================================================================


class TestFirst:
    """Tests for first() constraint."""

    def test_basic_first(self):
        """first() returns list of constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        constraints = first(seq, tasks[0])
        
        assert isinstance(constraints, list)
        assert len(constraints) == 2  # Against t1 and t2
        for c in constraints:
            assert isinstance(c, Node)
            assert c.type == TypeNode.LE

    def test_first_with_list(self):
        """first() works with list of intervals."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        constraints = first(tasks, tasks[0])
        
        assert isinstance(constraints, list)
        assert len(constraints) == 2

    def test_first_single_interval(self):
        """first() with single interval returns empty list."""
        task = IntervalVar(size=5, name="t0")
        
        constraints = first([task], task)
        
        assert constraints == []

    def test_first_optional_interval(self):
        """first() with optional intervals includes presence conditions."""
        tasks = [
            IntervalVar(size=5, optional=True, name="t0"),
            IntervalVar(size=5, name="t1"),
        ]
        
        constraints = first(tasks, tasks[0])
        
        assert isinstance(constraints, list)
        for c in constraints:
            assert isinstance(c, Node)
            # Should be OR constraint (absence or ordering)
            assert c.type == TypeNode.OR

    def test_first_interval_not_in_sequence(self):
        """first() raises error for interval not in sequence."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        other = IntervalVar(size=5, name="other")
        
        with pytest.raises(ValueError, match="not in the sequence"):
            first(tasks, other)

    def test_first_invalid_interval_type(self):
        """first() raises error for non-IntervalVar."""
        tasks = [IntervalVar(size=5, name="t0")]
        
        with pytest.raises(TypeError, match="must be an IntervalVar"):
            first(tasks, "not_interval")


class TestLast:
    """Tests for last() constraint."""

    def test_basic_last(self):
        """last() returns list of constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        constraints = last(seq, tasks[2])
        
        assert isinstance(constraints, list)
        assert len(constraints) == 2  # Against t0 and t1
        for c in constraints:
            assert isinstance(c, Node)
            assert c.type == TypeNode.LE

    def test_last_single_interval(self):
        """last() with single interval returns empty list."""
        task = IntervalVar(size=5, name="t0")
        
        constraints = last([task], task)
        
        assert constraints == []

    def test_last_optional_intervals(self):
        """last() with optional intervals includes presence conditions."""
        tasks = [
            IntervalVar(size=5, name="t0"),
            IntervalVar(size=5, optional=True, name="t1"),
        ]
        
        constraints = last(tasks, tasks[1])
        
        assert isinstance(constraints, list)
        for c in constraints:
            assert c.type == TypeNode.OR

    def test_last_interval_not_in_sequence(self):
        """last() raises error for interval not in sequence."""
        tasks = [IntervalVar(size=5, name="t0")]
        other = IntervalVar(size=5, name="other")
        
        with pytest.raises(ValueError, match="not in the sequence"):
            last(tasks, other)


class TestBefore:
    """Tests for before() constraint."""

    def test_basic_before(self):
        """before() returns precedence constraint."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        constraints = before(seq, tasks[0], tasks[2])
        
        assert isinstance(constraints, list)
        assert len(constraints) == 1
        assert isinstance(constraints[0], Node)
        assert constraints[0].type == TypeNode.LE

    def test_before_same_interval(self):
        """before() raises error for same interval."""
        task = IntervalVar(size=5, name="t0")
        
        with pytest.raises(ValueError, match="must be different"):
            before([task, task], task, task)

    def test_before_optional_intervals(self):
        """before() with optional intervals includes presence conditions."""
        tasks = [
            IntervalVar(size=5, optional=True, name="t0"),
            IntervalVar(size=5, optional=True, name="t1"),
        ]
        
        constraints = before(tasks, tasks[0], tasks[1])
        
        assert len(constraints) == 1
        assert constraints[0].type == TypeNode.OR

    def test_before_interval_not_in_sequence(self):
        """before() raises error for interval not in sequence."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        other = IntervalVar(size=5, name="other")
        
        with pytest.raises(ValueError, match="not in the sequence"):
            before(tasks, tasks[0], other)


class TestPrevious:
    """Tests for previous() constraint."""

    def test_basic_previous(self):
        """previous() returns precedence + no-between constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        constraints = previous(seq, tasks[0], tasks[1])
        
        assert isinstance(constraints, list)
        # 1 precedence + 1 no-between (for t2)
        assert len(constraints) == 2

    def test_previous_two_intervals(self):
        """previous() with only two intervals."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        
        constraints = previous(tasks, tasks[0], tasks[1])
        
        # Just precedence, no third interval to be "between"
        assert len(constraints) == 1

    def test_previous_same_interval(self):
        """previous() raises error for same interval."""
        task = IntervalVar(size=5, name="t0")
        
        with pytest.raises(ValueError, match="must be different"):
            previous([task, task], task, task)

    def test_previous_optional_intervals(self):
        """previous() with optional intervals."""
        tasks = [
            IntervalVar(size=5, optional=True, name="t0"),
            IntervalVar(size=5, optional=True, name="t1"),
            IntervalVar(size=5, optional=True, name="t2"),
        ]
        
        constraints = previous(tasks, tasks[0], tasks[1])
        
        assert isinstance(constraints, list)
        for c in constraints:
            assert c.type == TypeNode.OR


# =============================================================================
# Sequence Consistency Constraints Tests
# =============================================================================


class TestSameSequence:
    """Tests for same_sequence() constraint."""

    def test_basic_same_sequence(self):
        """same_sequence() returns ordering constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq1 = SequenceVar(intervals=tasks, name="machine1")
        seq2 = SequenceVar(intervals=tasks, name="machine2")
        
        constraints = same_sequence(seq1, seq2)
        
        assert isinstance(constraints, list)
        # 3 common intervals = 3 choose 2 = 3 pairs
        assert len(constraints) == 3

    def test_same_sequence_no_common(self):
        """same_sequence() with no common intervals returns empty."""
        tasks1 = [IntervalVar(size=5, name=f"t1_{i}") for i in range(2)]
        tasks2 = [IntervalVar(size=5, name=f"t2_{i}") for i in range(2)]
        
        constraints = same_sequence(tasks1, tasks2)
        
        assert constraints == []

    def test_same_sequence_one_common(self):
        """same_sequence() with one common interval returns empty."""
        common = IntervalVar(size=5, name="common")
        tasks1 = [common, IntervalVar(size=5, name="t1")]
        tasks2 = [common, IntervalVar(size=5, name="t2")]
        
        constraints = same_sequence(tasks1, tasks2)
        
        assert constraints == []

    def test_same_sequence_partial_overlap(self):
        """same_sequence() with partial overlap."""
        t0 = IntervalVar(size=5, name="t0")
        t1 = IntervalVar(size=5, name="t1")
        t2 = IntervalVar(size=5, name="t2")
        t3 = IntervalVar(size=5, name="t3")
        
        # t0, t1 are common
        tasks1 = [t0, t1, t2]
        tasks2 = [t0, t1, t3]
        
        constraints = same_sequence(tasks1, tasks2)
        
        # 2 common intervals = 1 pair
        assert len(constraints) == 1


class TestSameCommonSubsequence:
    """Tests for same_common_subsequence() constraint."""

    def test_basic_same_common_subsequence(self):
        """same_common_subsequence() returns ordering constraints."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq1 = SequenceVar(intervals=tasks, name="machine1")
        seq2 = SequenceVar(intervals=tasks, name="machine2")
        
        constraints = same_common_subsequence(seq1, seq2)
        
        assert isinstance(constraints, list)
        assert len(constraints) == 3  # 3 pairs

    def test_same_common_subsequence_no_common(self):
        """same_common_subsequence() with no common intervals returns empty."""
        tasks1 = [IntervalVar(size=5, name=f"t1_{i}") for i in range(2)]
        tasks2 = [IntervalVar(size=5, name=f"t2_{i}") for i in range(2)]
        
        constraints = same_common_subsequence(tasks1, tasks2)
        
        assert constraints == []

    def test_same_common_subsequence_optional(self):
        """same_common_subsequence() with optional intervals."""
        tasks = [IntervalVar(size=5, optional=True, name=f"t{i}") for i in range(3)]
        
        constraints = same_common_subsequence(tasks, tasks)
        
        assert isinstance(constraints, list)
        for c in constraints:
            assert c.type == TypeNode.OR


# =============================================================================
# Sequence Accessor Expressions Tests
# =============================================================================


class TestSequenceAccessorNext:
    """Tests for sequence accessor expressions (next)."""

    def test_start_of_next_basic(self):
        """start_of_next returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        expr = start_of_next(seq, tasks[0])
        
        assert isinstance(expr, IntervalExpr)

    def test_end_of_next_basic(self):
        """end_of_next returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = end_of_next(tasks, tasks[0])
        
        assert isinstance(expr, IntervalExpr)

    def test_size_of_next_basic(self):
        """size_of_next returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = size_of_next(tasks, tasks[0])
        
        assert isinstance(expr, IntervalExpr)

    def test_length_of_next_basic(self):
        """length_of_next returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = length_of_next(tasks, tasks[0])
        
        assert isinstance(expr, IntervalExpr)

    def test_type_of_next_basic(self):
        """type_of_next returns a pycsp3 variable that can be used for indexing."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, types=[0, 1, 2], name="machine")
        
        result = type_of_next(seq, tasks[0])
        
        # type_of_next now returns a pycsp3 variable for use in element constraints
        # It should have a string representation (variable ID)
        assert result is not None
        assert str(result).startswith("tonext")

    def test_type_of_next_requires_sequence_var(self):
        """type_of_next requires SequenceVar."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        with pytest.raises(TypeError, match="requires a SequenceVar"):
            type_of_next(tasks, tasks[0])

    def test_type_of_next_requires_types(self):
        """type_of_next requires types defined."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        with pytest.raises(ValueError, match="requires sequence with types"):
            type_of_next(seq, tasks[0])

    def test_accessor_interval_not_in_sequence(self):
        """Accessors raise error for interval not in sequence."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(2)]
        other = IntervalVar(size=5, name="other")
        
        with pytest.raises(ValueError, match="not in the sequence"):
            start_of_next(tasks, other)


class TestSequenceAccessorPrev:
    """Tests for sequence accessor expressions (prev)."""

    def test_start_of_prev_basic(self):
        """start_of_prev returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = start_of_prev(tasks, tasks[1])
        
        assert isinstance(expr, IntervalExpr)

    def test_end_of_prev_basic(self):
        """end_of_prev returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = end_of_prev(tasks, tasks[1])
        
        assert isinstance(expr, IntervalExpr)

    def test_size_of_prev_basic(self):
        """size_of_prev returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = size_of_prev(tasks, tasks[1])
        
        assert isinstance(expr, IntervalExpr)

    def test_length_of_prev_basic(self):
        """length_of_prev returns IntervalExpr."""
        from pycsp3_scheduling.expressions import IntervalExpr
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        expr = length_of_prev(tasks, tasks[1])
        
        assert isinstance(expr, IntervalExpr)

    def test_type_of_prev_basic(self):
        """type_of_prev returns a pycsp3 variable that can be used for indexing."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, types=[0, 1, 2], name="machine")
        
        result = type_of_prev(seq, tasks[1])
        
        # type_of_prev now returns a pycsp3 variable for use in element constraints
        # It should have a string representation (variable ID)
        assert result is not None
        assert str(result).startswith("toprev")

    def test_type_of_prev_requires_sequence_var(self):
        """type_of_prev requires SequenceVar."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        with pytest.raises(TypeError, match="requires a SequenceVar"):
            type_of_prev(tasks, tasks[1])

    def test_type_of_prev_requires_types(self):
        """type_of_prev requires types defined."""
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        with pytest.raises(ValueError, match="requires sequence with types"):
            type_of_prev(seq, tasks[1])


# =============================================================================
# Integration Tests
# =============================================================================


class TestSequenceIntegration:
    """Integration tests for sequence constraints with pycsp3."""

    def test_satisfy_with_first_last(self):
        """Test first and last work with satisfy()."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        satisfy(first(seq, tasks[0]))
        satisfy(last(seq, tasks[2]))

    def test_satisfy_with_before(self):
        """Test before works with satisfy()."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        satisfy(before(tasks, tasks[0], tasks[2]))

    def test_satisfy_with_previous(self):
        """Test previous works with satisfy()."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        
        satisfy(previous(tasks, tasks[0], tasks[1]))

    def test_satisfy_with_transition_matrix(self):
        """Test SeqNoOverlap with transition matrix works with satisfy()."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq = SequenceVar(intervals=tasks, types=[0, 1, 0], name="machine")
        matrix = [[0, 5], [3, 0]]
        
        satisfy(SeqNoOverlap(seq, transition_matrix=matrix))

    def test_satisfy_with_same_sequence(self):
        """Test same_sequence works with satisfy()."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(3)]
        seq1 = SequenceVar(intervals=tasks, name="m1")
        seq2 = SequenceVar(intervals=tasks, name="m2")
        
        satisfy(same_sequence(seq1, seq2))

    def test_job_shop_pattern(self):
        """Test job shop scheduling pattern."""
        from pycsp3 import satisfy
        
        # 2 jobs, 3 operations each
        ops = [[IntervalVar(size=5, name=f"j{j}o{o}") for o in range(3)] for j in range(2)]
        
        # Operations of same job must be in order
        for j in range(2):
            for o in range(2):
                satisfy(before(ops[j], ops[j][o], ops[j][o + 1]))

    def test_combined_sequence_constraints(self):
        """Test combining multiple sequence constraints."""
        from pycsp3 import satisfy
        
        tasks = [IntervalVar(size=5, name=f"t{i}") for i in range(4)]
        seq = SequenceVar(intervals=tasks, name="machine")
        
        # t0 is first, t3 is last, t1 before t2
        satisfy(first(seq, tasks[0]))
        satisfy(last(seq, tasks[3]))
        satisfy(before(seq, tasks[1], tasks[2]))
