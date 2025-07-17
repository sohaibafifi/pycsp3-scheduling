"""Tests for state functions and constraints."""

from __future__ import annotations

import pytest

from pycsp3_scheduling import (
    IntervalVar,
    StateConstraint,
    StateFunction,
    TransitionMatrix,
    always_constant,
    always_equal,
    always_in,
    always_no_state,
)
from pycsp3_scheduling.functions.state_functions import (
    StateConstraintType,
    clear_state_function_registry,
    get_registered_state_functions,
)


@pytest.fixture(autouse=True)
def reset_state_registry():
    """Reset the state function registry before each test."""
    clear_state_function_registry()


class TestTransitionMatrix:
    """Tests for TransitionMatrix class."""

    def test_create_basic_matrix(self):
        """Test creating a basic transition matrix."""
        tm = TransitionMatrix([
            [0, 5, 10],
            [5, 0, 3],
            [10, 3, 0],
        ])

        assert tm.size == 3
        assert tm[0, 1] == 5
        assert tm[1, 2] == 3
        assert tm[2, 0] == 10

    def test_create_named_matrix(self):
        """Test creating a named transition matrix."""
        tm = TransitionMatrix(
            [[0, 1], [1, 0]],
            name="setup_times"
        )

        assert tm.name == "setup_times"
        assert tm.size == 2

    def test_matrix_must_be_square(self):
        """Test that non-square matrix raises error."""
        with pytest.raises(ValueError, match="must be square"):
            TransitionMatrix([
                [0, 1, 2],
                [1, 0],  # Wrong length
            ])

    def test_empty_matrix_raises(self):
        """Test that empty matrix raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            TransitionMatrix([])

    def test_matrix_values_must_be_int(self):
        """Test that non-integer values raise error."""
        with pytest.raises(TypeError, match="must be integers"):
            TransitionMatrix([[0, 1.5], [1, 0]])  # type: ignore

    def test_setitem(self):
        """Test setting matrix values."""
        tm = TransitionMatrix([[0, 1], [1, 0]])
        tm[0, 1] = 5
        assert tm[0, 1] == 5

    def test_is_forbidden(self):
        """Test checking forbidden transitions."""
        tm = TransitionMatrix([
            [0, 5, -1],
            [5, 0, 3],
            [-1, 3, 0],
        ])

        assert tm.is_forbidden(0, 2)
        assert tm.is_forbidden(2, 0)
        assert not tm.is_forbidden(0, 1)

    def test_get_row(self):
        """Test getting transition times from a state."""
        tm = TransitionMatrix([
            [0, 5, 10],
            [5, 0, 3],
            [10, 3, 0],
        ])

        assert tm.get_row(1) == [5, 0, 3]

    def test_get_column(self):
        """Test getting transition times to a state."""
        tm = TransitionMatrix([
            [0, 5, 10],
            [5, 0, 3],
            [10, 3, 0],
        ])

        assert tm.get_column(1) == [5, 0, 3]

    def test_repr(self):
        """Test string representation."""
        tm = TransitionMatrix([[0, 1], [1, 0]], name="test")
        assert "test" in repr(tm)
        assert "2x2" in repr(tm)


class TestStateFunction:
    """Tests for StateFunction class."""

    def test_create_basic_state_function(self):
        """Test creating a basic state function."""
        sf = StateFunction(name="machine")

        assert sf.name == "machine"
        assert sf.transitions is None
        assert sf.initial_state is None

    def test_create_with_transitions(self):
        """Test creating a state function with transitions."""
        tm = TransitionMatrix([[0, 5], [5, 0]])
        sf = StateFunction(name="machine", transitions=tm)

        assert sf.transitions is tm
        assert sf.num_states == 2
        assert sf.states == {0, 1}

    def test_create_with_initial_state(self):
        """Test creating a state function with initial state."""
        sf = StateFunction(name="machine", initial_state=0)

        assert sf.initial_state == 0

    def test_create_with_explicit_states(self):
        """Test creating a state function with explicit states."""
        sf = StateFunction(name="machine", states={0, 1, 2, 3})

        assert sf.num_states == 4
        assert sf.states == {0, 1, 2, 3}

    def test_state_function_registration(self):
        """Test that state functions are registered."""
        sf = StateFunction(name="machine")

        registered = get_registered_state_functions()
        assert sf in registered

    def test_clear_registry(self):
        """Test clearing the registry."""
        StateFunction(name="machine")
        clear_state_function_registry()

        assert len(get_registered_state_functions()) == 0

    def test_repr(self):
        """Test string representation."""
        sf = StateFunction(name="machine")
        assert "machine" in repr(sf)


class TestAlwaysEqual:
    """Tests for always_equal constraint."""

    def test_always_equal_basic(self):
        """Test basic always_equal constraint."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        constraint = always_equal(sf, task, 2)

        assert isinstance(constraint, StateConstraint)
        assert constraint.constraint_type == StateConstraintType.ALWAYS_EQUAL
        assert constraint.state_func is sf
        assert constraint.interval is task
        assert constraint.value == 2

    def test_always_equal_alignment_options(self):
        """Test always_equal with alignment options."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        constraint = always_equal(
            sf, task, 1,
            is_start_aligned=False,
            is_end_aligned=False
        )

        assert constraint.is_start_aligned is False
        assert constraint.is_end_aligned is False

    def test_always_equal_invalid_state_func(self):
        """Test always_equal with invalid state function."""
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be a StateFunction"):
            always_equal("not_a_state_func", task, 1)  # type: ignore

    def test_always_equal_invalid_interval(self):
        """Test always_equal with invalid interval."""
        sf = StateFunction(name="machine")

        with pytest.raises(TypeError, match="must be an IntervalVar"):
            always_equal(sf, "not_an_interval", 1)  # type: ignore

    def test_always_equal_invalid_value(self):
        """Test always_equal with invalid value type."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError, match="must be an int"):
            always_equal(sf, task, "not_an_int")  # type: ignore


class TestAlwaysIn:
    """Tests for always_in constraint with StateFunction."""

    def test_always_in_basic(self):
        """Test basic always_in constraint."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        constraint = always_in(sf, task, 1, 3)

        assert isinstance(constraint, StateConstraint)
        assert constraint.constraint_type == StateConstraintType.ALWAYS_IN
        assert constraint.min_value == 1
        assert constraint.max_value == 3

    def test_always_in_invalid_bounds(self):
        """Test always_in with invalid bounds."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        with pytest.raises(ValueError, match="cannot exceed"):
            always_in(sf, task, 5, 3)


class TestAlwaysConstant:
    """Tests for always_constant constraint."""

    def test_always_constant_basic(self):
        """Test basic always_constant constraint."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        constraint = always_constant(sf, task)

        assert isinstance(constraint, StateConstraint)
        assert constraint.constraint_type == StateConstraintType.ALWAYS_CONSTANT
        assert constraint.state_func is sf
        assert constraint.interval is task

    def test_always_constant_alignment_options(self):
        """Test always_constant with alignment options."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        constraint = always_constant(
            sf, task,
            is_start_aligned=False,
            is_end_aligned=True
        )

        assert constraint.is_start_aligned is False
        assert constraint.is_end_aligned is True

    def test_always_constant_invalid_inputs(self):
        """Test always_constant with invalid inputs."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        with pytest.raises(TypeError):
            always_constant("not_sf", task)  # type: ignore

        with pytest.raises(TypeError):
            always_constant(sf, "not_interval")  # type: ignore


class TestAlwaysNoState:
    """Tests for always_no_state constraint."""

    def test_always_no_state_basic(self):
        """Test basic always_no_state constraint."""
        sf = StateFunction(name="machine")
        maintenance = IntervalVar(size=10, name="maintenance")

        constraint = always_no_state(sf, maintenance)

        assert isinstance(constraint, StateConstraint)
        assert constraint.constraint_type == StateConstraintType.ALWAYS_NO_STATE
        assert constraint.state_func is sf
        assert constraint.interval is maintenance

    def test_always_no_state_alignment_options(self):
        """Test always_no_state with alignment options."""
        sf = StateFunction(name="machine")
        maintenance = IntervalVar(size=10, name="maintenance")

        constraint = always_no_state(
            sf, maintenance,
            is_start_aligned=True,
            is_end_aligned=False
        )

        assert constraint.is_start_aligned is True
        assert constraint.is_end_aligned is False


class TestStateScenarios:
    """Integration tests for realistic state function scenarios."""

    def test_machine_modes_scenario(self):
        """Test machine with different operating modes."""
        # Define transition times between modes
        # Mode 0: Idle, Mode 1: Processing, Mode 2: Setup
        transitions = TransitionMatrix([
            [0, 2, 5],   # From Idle: to Processing=2, to Setup=5
            [1, 0, 3],   # From Processing: to Idle=1, to Setup=3
            [3, 4, 0],   # From Setup: to Idle=3, to Processing=4
        ])

        machine = StateFunction(
            name="machine",
            transitions=transitions,
            initial_state=0
        )

        # Tasks that require specific modes
        task_a = IntervalVar(size=10, name="task_a")
        task_b = IntervalVar(size=5, name="task_b")

        # Both tasks need machine in Processing mode (1)
        c1 = always_equal(machine, task_a, 1)
        c2 = always_equal(machine, task_b, 1)

        assert c1.value == 1
        assert c2.value == 1
        assert machine.num_states == 3

    def test_room_configuration_scenario(self):
        """Test room with different configurations."""
        room = StateFunction(
            name="room",
            states={0, 1, 2}  # 0=empty, 1=lecture, 2=exam
        )

        lecture = IntervalVar(size=60, name="lecture")
        exam = IntervalVar(size=120, name="exam")
        cleanup = IntervalVar(size=15, name="cleanup")

        # Lecture needs room in lecture mode
        c1 = always_equal(room, lecture, 1)

        # Exam needs room in exam mode
        c2 = always_equal(room, exam, 2)

        # Cleanup - room has no specific mode
        c3 = always_no_state(room, cleanup)

        assert c1.value == 1
        assert c2.value == 2
        assert c3.constraint_type == StateConstraintType.ALWAYS_NO_STATE

    def test_worker_skills_scenario(self):
        """Test worker with different skill requirements."""
        worker_mode = StateFunction(name="worker")

        # Tasks requiring different skill levels (0-4)
        basic_task = IntervalVar(size=30, name="basic")
        advanced_task = IntervalVar(size=60, name="advanced")

        # Basic task needs skill level 1-2
        c1 = always_in(worker_mode, basic_task, 1, 2)

        # Advanced task needs skill level 3-4
        c2 = always_in(worker_mode, advanced_task, 3, 4)

        assert c1.min_value == 1
        assert c1.max_value == 2
        assert c2.min_value == 3
        assert c2.max_value == 4

    def test_constraint_repr(self):
        """Test string representations of constraints."""
        sf = StateFunction(name="machine")
        task = IntervalVar(size=10, name="task")

        c1 = always_equal(sf, task, 2)
        c2 = always_in(sf, task, 1, 3)
        c3 = always_constant(sf, task)
        c4 = always_no_state(sf, task)

        assert "always_equal" in repr(c1)
        assert "always_in" in repr(c2)
        assert "always_constant" in repr(c3)
        assert "always_no_state" in repr(c4)
