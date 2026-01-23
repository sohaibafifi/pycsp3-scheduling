"""
State functions for modeling discrete states over time.

A state function represents a resource that can be in different states
over time, with optional transition constraints between states.

Use cases:
- Machine modes (setup, processing, idle, maintenance)
- Room configurations (lecture, exam, meeting)
- Worker skills/roles
- Any resource with discrete, mutually exclusive states

Example:
    >>> machine_state = StateFunction(name="machine")
    >>> # Task requires machine in state 1
    >>> satisfy(always_equal(machine_state, task, 1))
    >>> # Define valid transitions with durations
    >>> transitions = TransitionMatrix([
    ...     [0, 5, 10],  # From state 0: 0->0=0, 0->1=5, 0->2=10
    ...     [5, 0, 3],   # From state 1: 1->0=5, 1->1=0, 1->2=3
    ...     [10, 3, 0],  # From state 2: 2->0=10, 2->1=3, 2->2=0
    ... ])
    >>> machine_state = StateFunction(name="machine", transitions=transitions)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar


# =============================================================================
# Transition Matrix
# =============================================================================


@dataclass
class TransitionMatrix:
    """
    Transition matrix defining valid state transitions and durations.

    A transition matrix specifies the time required to transition from
    one state to another. A value of -1 (or FORBIDDEN) indicates that
    the transition is not allowed.

    Attributes:
        matrix: 2D list of transition times. matrix[i][j] is the time
            to transition from state i to state j.
        name: Optional name for the matrix.

    Example:
        >>> # 3 states with symmetric transition times
        >>> tm = TransitionMatrix([
        ...     [0, 5, 10],
        ...     [5, 0, 3],
        ...     [10, 3, 0],
        ... ])
        >>> tm[0, 1]  # Time from state 0 to state 1
        5
    """

    matrix: list[list[int]]
    name: str | None = None
    _id: int = field(default=-1, repr=False)

    # Special value indicating forbidden transition
    FORBIDDEN: int = -1

    def __post_init__(self) -> None:
        """Validate and assign unique ID."""
        self._validate()
        if self._id == -1:
            self._id = TransitionMatrix._get_next_id()

    def _validate(self) -> None:
        """Validate the transition matrix."""
        if not self.matrix:
            raise ValueError("Transition matrix cannot be empty")

        n = len(self.matrix)
        for i, row in enumerate(self.matrix):
            if len(row) != n:
                raise ValueError(
                    f"Transition matrix must be square. "
                    f"Row {i} has {len(row)} elements, expected {n}"
                )
            for j, val in enumerate(row):
                if not isinstance(val, int):
                    raise TypeError(
                        f"Transition matrix values must be integers, "
                        f"got {type(val).__name__} at [{i}][{j}]"
                    )

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID."""
        current = getattr(TransitionMatrix, "_id_counter", 0)
        TransitionMatrix._id_counter = current + 1
        return current

    @property
    def size(self) -> int:
        """Number of states (dimension of the matrix)."""
        return len(self.matrix)

    def __getitem__(self, key: tuple[int, int]) -> int:
        """Get transition time from state i to state j."""
        i, j = key
        return self.matrix[i][j]

    def __setitem__(self, key: tuple[int, int], value: int) -> None:
        """Set transition time from state i to state j."""
        i, j = key
        self.matrix[i][j] = value

    def is_forbidden(self, from_state: int, to_state: int) -> bool:
        """Check if transition from from_state to to_state is forbidden."""
        return self.matrix[from_state][to_state] == self.FORBIDDEN

    def get_row(self, state: int) -> list[int]:
        """Get all transition times from a given state."""
        return self.matrix[state]

    def get_column(self, state: int) -> list[int]:
        """Get all transition times to a given state."""
        return [row[state] for row in self.matrix]

    def __repr__(self) -> str:
        """String representation."""
        if self.name:
            return f"TransitionMatrix({self.name}, {self.size}x{self.size})"
        return f"TransitionMatrix({self.size}x{self.size})"


# =============================================================================
# State Function
# =============================================================================


@dataclass
class StateFunction:
    """
    State function representing a discrete state over time.

    A state function can be in different integer states at different times.
    Tasks can require specific states during their execution, and transitions
    between states can have associated times defined by a transition matrix.

    Attributes:
        name: Name of the state function.
        transitions: Optional transition matrix defining transition times.
        initial_state: Initial state at time 0 (default: no specific state).
        states: Set of valid state values (inferred from transitions if not given).

    Example:
        >>> machine = StateFunction(name="machine_mode")
        >>> # Machine must be in state 2 during task execution
        >>> satisfy(always_equal(machine, task, 2))
    """

    name: str
    transitions: TransitionMatrix | None = None
    initial_state: int | None = None
    states: set[int] | None = None
    _id: int = field(default=-1, repr=False)

    def __post_init__(self) -> None:
        """Initialize and validate."""
        if self._id == -1:
            self._id = StateFunction._get_next_id()
            _register_state_function(self)

        # Infer states from transition matrix if not provided
        if self.states is None and self.transitions is not None:
            self.states = set(range(self.transitions.size))

    @staticmethod
    def _get_next_id() -> int:
        """Get next unique ID."""
        current = getattr(StateFunction, "_id_counter", 0)
        StateFunction._id_counter = current + 1
        return current

    @property
    def num_states(self) -> int | None:
        """Number of valid states, if known."""
        if self.states is not None:
            return len(self.states)
        if self.transitions is not None:
            return self.transitions.size
        return None

    def __hash__(self) -> int:
        """Hash based on unique ID."""
        return hash(self._id)

    def __repr__(self) -> str:
        """String representation."""
        parts = [f"StateFunction({self.name!r}"]
        if self.transitions:
            parts.append(f", transitions={self.transitions.size}x{self.transitions.size}")
        if self.initial_state is not None:
            parts.append(f", initial={self.initial_state}")
        parts.append(")")
        return "".join(parts)


# =============================================================================
# State Constraint Types
# =============================================================================


class StateConstraintType(Enum):
    """Types of state constraints."""

    ALWAYS_IN = auto()  # State in range [min, max]
    ALWAYS_EQUAL = auto()  # State equals specific value
    ALWAYS_CONSTANT = auto()  # State doesn't change during interval
    ALWAYS_NO_STATE = auto()  # No state defined during interval


@dataclass
class StateConstraint:
    """
    Constraint on a state function during an interval.

    Attributes:
        state_func: The state function being constrained.
        interval: The interval during which the constraint applies.
        constraint_type: Type of constraint.
        value: State value for ALWAYS_EQUAL.
        min_value: Minimum state for ALWAYS_IN.
        max_value: Maximum state for ALWAYS_IN.
        is_start_aligned: Whether constraint starts exactly at interval start.
        is_end_aligned: Whether constraint ends exactly at interval end.
    """

    state_func: StateFunction
    interval: IntervalVar
    constraint_type: StateConstraintType
    value: int | None = None
    min_value: int | None = None
    max_value: int | None = None
    is_start_aligned: bool = True
    is_end_aligned: bool = True

    def __repr__(self) -> str:
        """String representation."""
        interval_name = self.interval.name if self.interval else "?"
        if self.constraint_type == StateConstraintType.ALWAYS_EQUAL:
            return f"always_equal({self.state_func.name}, {interval_name}, {self.value})"
        elif self.constraint_type == StateConstraintType.ALWAYS_IN:
            return f"always_in({self.state_func.name}, {interval_name}, {self.min_value}, {self.max_value})"
        elif self.constraint_type == StateConstraintType.ALWAYS_CONSTANT:
            return f"always_constant({self.state_func.name}, {interval_name})"
        elif self.constraint_type == StateConstraintType.ALWAYS_NO_STATE:
            return f"always_no_state({self.state_func.name}, {interval_name})"
        return f"StateConstraint({self.constraint_type})"


# =============================================================================
# State Constraint Functions
# =============================================================================


def always_equal(
    state_func: StateFunction,
    interval: IntervalVar,
    value: int,
    is_start_aligned: bool = True,
    is_end_aligned: bool = True,
) -> StateConstraint:
    """
    Constrain state function to equal a specific value during interval.

    The state function must be equal to the specified value throughout
    the execution of the interval.

    Args:
        state_func: The state function.
        interval: The interval during which the constraint applies.
        value: The required state value.
        is_start_aligned: If True, state must equal value exactly at start.
        is_end_aligned: If True, state must equal value exactly at end.

    Returns:
        A StateConstraint representing the always_equal constraint.

    Example:
        >>> machine = StateFunction(name="machine")
        >>> # Machine must be in state 2 during task
        >>> satisfy(always_equal(machine, task, 2))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(state_func, StateFunction):
        raise TypeError(
            f"state_func must be a StateFunction, got {type(state_func).__name__}"
        )
    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )
    if not isinstance(value, int):
        raise TypeError(f"value must be an int, got {type(value).__name__}")

    return StateConstraint(
        state_func=state_func,
        interval=interval,
        constraint_type=StateConstraintType.ALWAYS_EQUAL,
        value=value,
        is_start_aligned=is_start_aligned,
        is_end_aligned=is_end_aligned,
    )


def always_in(
    state_func: StateFunction,
    interval: IntervalVar,
    min_value: int,
    max_value: int,
    is_start_aligned: bool = True,
    is_end_aligned: bool = True,
) -> StateConstraint:
    """
    Constrain state function to be within a range during interval.

    The state function must be within [min_value, max_value] throughout
    the execution of the interval.

    Args:
        state_func: The state function.
        interval: The interval during which the constraint applies.
        min_value: Minimum allowed state value.
        max_value: Maximum allowed state value.
        is_start_aligned: If True, constraint applies exactly at start.
        is_end_aligned: If True, constraint applies exactly at end.

    Returns:
        A StateConstraint representing the always_in constraint.

    Example:
        >>> machine = StateFunction(name="machine")
        >>> # Machine must be in state 1, 2, or 3 during task
        >>> satisfy(always_in(machine, task, 1, 3))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(state_func, StateFunction):
        raise TypeError(
            f"state_func must be a StateFunction, got {type(state_func).__name__}"
        )
    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )
    if not isinstance(min_value, int) or not isinstance(max_value, int):
        raise TypeError("min_value and max_value must be integers")
    if min_value > max_value:
        raise ValueError(
            f"min_value ({min_value}) cannot exceed max_value ({max_value})"
        )

    return StateConstraint(
        state_func=state_func,
        interval=interval,
        constraint_type=StateConstraintType.ALWAYS_IN,
        min_value=min_value,
        max_value=max_value,
        is_start_aligned=is_start_aligned,
        is_end_aligned=is_end_aligned,
    )


def always_constant(
    state_func: StateFunction,
    interval: IntervalVar,
    is_start_aligned: bool = True,
    is_end_aligned: bool = True,
) -> StateConstraint:
    """
    Constrain state function to remain constant during interval.

    The state function must not change its value throughout the
    execution of the interval.

    Args:
        state_func: The state function.
        interval: The interval during which the constraint applies.
        is_start_aligned: If True, constant region starts exactly at start.
        is_end_aligned: If True, constant region ends exactly at end.

    Returns:
        A StateConstraint representing the always_constant constraint.

    Example:
        >>> machine = StateFunction(name="machine")
        >>> # Machine state cannot change during task
        >>> satisfy(always_constant(machine, task))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(state_func, StateFunction):
        raise TypeError(
            f"state_func must be a StateFunction, got {type(state_func).__name__}"
        )
    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )

    return StateConstraint(
        state_func=state_func,
        interval=interval,
        constraint_type=StateConstraintType.ALWAYS_CONSTANT,
        is_start_aligned=is_start_aligned,
        is_end_aligned=is_end_aligned,
    )


def always_no_state(
    state_func: StateFunction,
    interval: IntervalVar,
    is_start_aligned: bool = True,
    is_end_aligned: bool = True,
) -> StateConstraint:
    """
    Constrain state function to have no defined state during interval.

    The state function must not be in any state throughout the
    execution of the interval (the resource is "unused").

    Args:
        state_func: The state function.
        interval: The interval during which the constraint applies.
        is_start_aligned: If True, no-state region starts exactly at start.
        is_end_aligned: If True, no-state region ends exactly at end.

    Returns:
        A StateConstraint representing the always_no_state constraint.

    Example:
        >>> machine = StateFunction(name="machine")
        >>> # Machine must be unused during maintenance
        >>> satisfy(always_no_state(machine, maintenance_interval))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(state_func, StateFunction):
        raise TypeError(
            f"state_func must be a StateFunction, got {type(state_func).__name__}"
        )
    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )

    return StateConstraint(
        state_func=state_func,
        interval=interval,
        constraint_type=StateConstraintType.ALWAYS_NO_STATE,
        is_start_aligned=is_start_aligned,
        is_end_aligned=is_end_aligned,
    )


# =============================================================================
# Registry for State Functions
# =============================================================================


_state_function_registry: list[StateFunction] = []


def _register_state_function(sf: StateFunction) -> None:
    """Register a state function."""
    if sf not in _state_function_registry:
        _state_function_registry.append(sf)


def get_registered_state_functions() -> list[StateFunction]:
    """Get all registered state functions."""
    return list(_state_function_registry)


def clear_state_function_registry() -> None:
    """Clear the state function registry."""
    _state_function_registry.clear()
    StateFunction._id_counter = 0
    TransitionMatrix._id_counter = 0


# =============================================================================
# Convenience State Helpers
# =============================================================================


def requires_state(
    interval: IntervalVar,
    state_func: StateFunction,
    required_state: int,
) -> StateConstraint:
    """
    Simplified constraint that interval requires a specific state.

    This is a convenience wrapper around always_equal with a more intuitive
    parameter order (interval first, like other constraint functions).

    Args:
        interval: The interval requiring the state.
        state_func: The state function (resource).
        required_state: The required state value.

    Returns:
        A StateConstraint representing the requirement.

    Example:
        >>> oven = StateFunction(name="oven_temp")
        >>> bake_task = IntervalVar(size=30, name="bake")
        >>> # Baking requires oven at temperature state 2 (e.g., 350F)
        >>> satisfy(requires_state(bake_task, oven, 2))
    """
    return always_equal(state_func, interval, required_state)


def sets_state(
    interval: IntervalVar,
    state_func: StateFunction,
    before_state: int | None,
    after_state: int,
) -> list[StateConstraint]:
    """
    Interval transitions the state from one value to another.

    This constraint models a task that changes the state of a resource.
    The state must be `before_state` when the interval starts (if specified),
    and becomes `after_state` when the interval ends.

    Args:
        interval: The interval performing the state change.
        state_func: The state function.
        before_state: Required state before interval (None = any state).
        after_state: State after interval completes.

    Returns:
        List of StateConstraints representing the state transition.

    Example:
        >>> machine_mode = StateFunction(name="machine_mode")
        >>> changeover = IntervalVar(size=15, name="changeover_A_to_B")
        >>> # This changeover task transitions machine from mode A (0) to mode B (1)
        >>> satisfy(sets_state(changeover, machine_mode, before_state=0, after_state=1))
    """
    from pycsp3_scheduling.variables.interval import IntervalVar

    if not isinstance(state_func, StateFunction):
        raise TypeError(
            f"state_func must be a StateFunction, got {type(state_func).__name__}"
        )
    if not isinstance(interval, IntervalVar):
        raise TypeError(
            f"interval must be an IntervalVar, got {type(interval).__name__}"
        )
    if not isinstance(after_state, int):
        raise TypeError(f"after_state must be an int, got {type(after_state).__name__}")
    if before_state is not None and not isinstance(before_state, int):
        raise TypeError(f"before_state must be an int or None, got {type(before_state).__name__}")

    constraints = []

    # If before_state is specified, require that state at start
    if before_state is not None:
        constraints.append(
            StateConstraint(
                state_func=state_func,
                interval=interval,
                constraint_type=StateConstraintType.ALWAYS_EQUAL,
                value=before_state,
                is_start_aligned=True,
                is_end_aligned=False,  # Only at start
            )
        )

    # After interval, state becomes after_state
    constraints.append(
        StateConstraint(
            state_func=state_func,
            interval=interval,
            constraint_type=StateConstraintType.ALWAYS_EQUAL,
            value=after_state,
            is_start_aligned=False,  # Only at end
            is_end_aligned=True,
        )
    )

    return constraints
