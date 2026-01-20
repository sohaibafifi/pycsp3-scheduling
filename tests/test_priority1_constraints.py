"""Tests for Priority 1 constraints: forbidden time, presence, and chain."""

import pytest

pycsp3 = pytest.importorskip("pycsp3")

from pycsp3.classes.entities import clear as clear_pycsp3
from pycsp3.classes.nodes import Node, TypeNode

from pycsp3_scheduling.constraints import (
    all_present_or_all_absent,
    at_least_k_present,
    at_most_k_present,
    chain,
    exactly_k_present,
    forbid_end,
    forbid_extent,
    forbid_start,
    if_present_then,
    presence_implies,
    presence_or,
    presence_or_all,
    presence_xor,
    strict_chain,
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


# =============================================================================
# Forbidden Time Constraints
# =============================================================================


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


# =============================================================================
# Presence Constraints
# =============================================================================


class TestPresenceImplies:
    """Tests for presence_implies constraint."""

    def test_both_optional(self):
        """presence_implies with both optional intervals."""
        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_implies(a, b)

        assert isinstance(ctrs, list)
        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "or(" in ctr_str

    def test_a_mandatory(self):
        """presence_implies with mandatory antecedent forces b present."""
        a = IntervalVar(size=10, name="a")  # mandatory
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_implies(a, b)

        assert len(ctrs) == 1
        # Should force b to be present
        assert ctrs[0].type == TypeNode.EQ

    def test_b_mandatory(self):
        """presence_implies with mandatory consequent is always satisfied."""
        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, name="b")  # mandatory

        ctrs = presence_implies(a, b)

        assert ctrs == []

    def test_invalid_interval_type(self):
        """presence_implies rejects non-IntervalVar."""
        a = IntervalVar(size=10, name="a")

        with pytest.raises(TypeError, match="IntervalVar"):
            presence_implies(a, "not_interval")


class TestPresenceOr:
    """Tests for presence_or constraint."""

    def test_both_optional(self):
        """presence_or with both optional intervals."""
        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_or(a, b)

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "or(" in ctr_str

    def test_one_mandatory(self):
        """presence_or with one mandatory is always satisfied."""
        a = IntervalVar(size=10, name="a")  # mandatory
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_or(a, b)

        assert ctrs == []

    def test_invalid_interval_type(self):
        """presence_or rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            presence_or("a", "b")


class TestPresenceXor:
    """Tests for presence_xor constraint."""

    def test_both_optional(self):
        """presence_xor with both optional intervals."""
        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_xor(a, b)

        assert len(ctrs) == 1
        # Should be pres_a + pres_b == 1
        assert ctrs[0].type == TypeNode.EQ

    def test_a_mandatory(self):
        """presence_xor with a mandatory forces b absent."""
        a = IntervalVar(size=10, name="a")  # mandatory
        b = IntervalVar(size=10, optional=True, name="b")

        ctrs = presence_xor(a, b)

        assert len(ctrs) == 1
        # Should force b to be absent
        assert ctrs[0].type == TypeNode.EQ

    def test_both_mandatory(self):
        """presence_xor with both mandatory is infeasible."""
        a = IntervalVar(size=10, name="a")
        b = IntervalVar(size=10, name="b")

        ctrs = presence_xor(a, b)

        # Should return a false constraint (0 == 1)
        assert len(ctrs) == 1

    def test_invalid_interval_type(self):
        """presence_xor rejects non-IntervalVar."""
        a = IntervalVar(size=10, name="a")

        with pytest.raises(TypeError, match="IntervalVar"):
            presence_xor(a, 123)


class TestAllPresentOrAllAbsent:
    """Tests for all_present_or_all_absent constraint."""

    def test_all_optional(self):
        """all_present_or_all_absent with all optional."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = all_present_or_all_absent(intervals)

        # Should have n-1 equality constraints
        assert len(ctrs) == 2

    def test_one_mandatory(self):
        """all_present_or_all_absent with one mandatory forces all present."""
        intervals = [
            IntervalVar(size=10, name="t0"),  # mandatory
            IntervalVar(size=10, optional=True, name="t1"),
            IntervalVar(size=10, optional=True, name="t2"),
        ]

        ctrs = all_present_or_all_absent(intervals)

        # Should force optional ones to be present
        assert len(ctrs) == 2

    def test_single_interval(self):
        """all_present_or_all_absent with single interval returns empty."""
        intervals = [IntervalVar(size=10, optional=True, name="t0")]

        ctrs = all_present_or_all_absent(intervals)

        assert ctrs == []

    def test_invalid_interval_type(self):
        """all_present_or_all_absent rejects non-IntervalVar."""
        with pytest.raises(TypeError, match="IntervalVar"):
            all_present_or_all_absent(["a", "b"])


class TestPresenceOrAll:
    """Tests for presence_or_all constraint."""

    def test_multiple_optional(self):
        """presence_or_all with multiple optional intervals."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = presence_or_all(*intervals)

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "or(" in ctr_str

    def test_one_mandatory(self):
        """presence_or_all with one mandatory is always satisfied."""
        intervals = [
            IntervalVar(size=10, name="t0"),  # mandatory
            IntervalVar(size=10, optional=True, name="t1"),
        ]

        ctrs = presence_or_all(*intervals)

        assert ctrs == []


class TestIfPresentThen:
    """Tests for if_present_then constraint."""

    def test_optional_interval(self):
        """if_present_then with optional interval."""
        task = IntervalVar(size=10, optional=True, name="task")

        # Create a simple constraint
        from pycsp3_scheduling.constraints._pycsp3 import start_var
        start = start_var(task)
        from pycsp3.classes.nodes import Node, TypeNode
        constraint = Node.build(TypeNode.GE, start, 5)

        ctrs = if_present_then(task, constraint)

        assert len(ctrs) == 1
        ctr_str = str(ctrs[0])
        assert "or(" in ctr_str

    def test_mandatory_interval(self):
        """if_present_then with mandatory interval applies constraint directly."""
        task = IntervalVar(size=10, name="task")

        from pycsp3_scheduling.constraints._pycsp3 import start_var
        start = start_var(task)
        from pycsp3.classes.nodes import Node, TypeNode
        constraint = Node.build(TypeNode.GE, start, 5)

        ctrs = if_present_then(task, constraint)

        assert len(ctrs) == 1
        # Should be the original constraint
        assert ctrs[0].type == TypeNode.GE


class TestAtLeastKPresent:
    """Tests for at_least_k_present constraint."""

    def test_basic(self):
        """at_least_k_present returns sum >= k constraint."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(5)]

        ctrs = at_least_k_present(intervals, 3)

        assert len(ctrs) == 1
        assert ctrs[0].type == TypeNode.GE

    def test_k_zero(self):
        """at_least_k_present with k=0 is always satisfied."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = at_least_k_present(intervals, 0)

        assert ctrs == []

    def test_invalid_k_type(self):
        """at_least_k_present rejects non-int k."""
        intervals = [IntervalVar(size=10, optional=True, name="t0")]

        with pytest.raises(TypeError, match="integer"):
            at_least_k_present(intervals, "3")

    def test_negative_k(self):
        """at_least_k_present rejects negative k."""
        intervals = [IntervalVar(size=10, optional=True, name="t0")]

        with pytest.raises(ValueError, match="non-negative"):
            at_least_k_present(intervals, -1)


class TestAtMostKPresent:
    """Tests for at_most_k_present constraint."""

    def test_basic(self):
        """at_most_k_present returns sum <= k constraint."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(5)]

        ctrs = at_most_k_present(intervals, 3)

        assert len(ctrs) == 1
        assert ctrs[0].type == TypeNode.LE

    def test_k_greater_than_n(self):
        """at_most_k_present with k >= n is always satisfied."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = at_most_k_present(intervals, 5)

        assert ctrs == []


class TestExactlyKPresent:
    """Tests for exactly_k_present constraint."""

    def test_basic(self):
        """exactly_k_present returns sum == k constraint."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(5)]

        ctrs = exactly_k_present(intervals, 3)

        assert len(ctrs) == 1
        assert ctrs[0].type == TypeNode.EQ

    def test_k_greater_than_n(self):
        """exactly_k_present with k > n is infeasible."""
        intervals = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        ctrs = exactly_k_present(intervals, 5)

        # Should return infeasible constraint
        assert len(ctrs) == 1


# =============================================================================
# Chain Constraints
# =============================================================================


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


# =============================================================================
# Integration Tests
# =============================================================================


class TestPriority1Integration:
    """Integration tests for priority 1 constraints with pycsp3."""

    def test_satisfy_with_forbidden(self):
        """Test forbidden constraints can be used with satisfy()."""
        from pycsp3 import satisfy

        task = IntervalVar(size=10, name="task")

        # Should not raise
        satisfy(forbid_start(task, [(12, 13)]))
        satisfy(forbid_end(task, [(17, 18)]))
        satisfy(forbid_extent(task, [(20, 25)]))

    def test_satisfy_with_presence(self):
        """Test presence constraints can be used with satisfy()."""
        from pycsp3 import satisfy

        a = IntervalVar(size=10, optional=True, name="a")
        b = IntervalVar(size=10, optional=True, name="b")

        satisfy(presence_implies(a, b))
        satisfy(presence_or(a, b))

    def test_satisfy_with_chain(self):
        """Test chain constraint can be used with satisfy()."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=i + 1, name=f"t{i}") for i in range(4)]

        satisfy(chain(tasks))

    def test_combined_constraints(self):
        """Test combining multiple priority 1 constraints."""
        from pycsp3 import satisfy

        tasks = [IntervalVar(size=10, optional=True, name=f"t{i}") for i in range(3)]

        # Chain with at least 2 present, no task during lunch
        satisfy(
            chain(tasks),
            at_least_k_present(tasks, 2),
            *[forbid_extent(t, [(12, 13)]) for t in tasks],
        )
