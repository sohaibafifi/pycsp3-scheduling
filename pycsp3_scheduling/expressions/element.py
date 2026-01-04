"""
Element expressions for array indexing with variable indices.

This module provides the ability to index into arrays using expressions
(like type_of_next), similar to CP Optimizer's IloNumArray2 pattern.

The key use case is building objectives like:
    sum(M[type_i][type_of_next(route, visit[i], last, abs)] for i in intervals)

Where M is a transition cost matrix indexed by interval types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Sequence, Union

if TYPE_CHECKING:
    from pycsp3_scheduling.variables.interval import IntervalVar
    from pycsp3_scheduling.variables.sequence import SequenceVar


@dataclass
class ElementMatrix:
    """
    A 2D matrix that can be indexed with expressions.

    This class wraps a 2D list of values and provides element-style indexing
    where indices can be pycsp3 variables or expressions. It's designed to
    work with type_of_next() for computing transition costs in scheduling.

    The matrix supports two special values for boundary cases:
    - last_value: Used when an interval is the last in its sequence
    - absent_value: Used when an interval is absent (optional and not selected)

    Example (CP Optimizer pattern):
        # Travel distance matrix indexed by customer types
        M = ElementMatrix(
            matrix=travel_times,    # 2D list [from_type][to_type]
            last_value=depot_distances,  # 1D list or scalar for return to depot
            absent_value=0,         # 0 cost if interval is absent
        )
        
        # Objective: minimize total travel distance
        for k in vehicles:
            for i in intervals:
                cost = M[type_i, type_of_next(route[k], visit[k][i])]

    Attributes:
        matrix: 2D list of transition costs [from_type][to_type].
        last_value: Value(s) when next is "last" (end of sequence).
                   Can be a scalar or 1D list indexed by from_type.
        absent_value: Value when interval is absent (scalar or 1D list).
        n_rows: Number of rows (from_types).
        n_cols: Number of columns (to_types).
    """

    matrix: list[list[int | float]]
    last_value: int | float | list[int | float] = 0
    absent_value: int | float | list[int | float] = 0
    _flat_vars: Any = field(default=None, repr=False, compare=False)
    _n_rows: int = field(default=-1, repr=False, compare=False)
    _n_cols: int = field(default=-1, repr=False, compare=False)
    _last_type: int = field(default=-1, repr=False, compare=False)
    _absent_type: int = field(default=-1, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate and setup the matrix."""
        if not self.matrix:
            raise ValueError("Matrix cannot be empty")
        
        # Validate rectangular matrix
        self._n_rows = len(self.matrix)
        self._n_cols = len(self.matrix[0])
        for row in self.matrix:
            if len(row) != self._n_cols:
                raise ValueError("Matrix must be rectangular")
        
        # Special type indices: last = n_cols, absent = n_cols + 1
        self._last_type = self._n_cols
        self._absent_type = self._n_cols + 1

    @property
    def n_rows(self) -> int:
        """Number of rows (from_types)."""
        return self._n_rows

    @property
    def n_cols(self) -> int:
        """Number of columns (to_types), excluding special types."""
        return self._n_cols

    @property
    def last_type(self) -> int:
        """Type index representing 'last' (end of sequence)."""
        return self._last_type

    @property
    def absent_type(self) -> int:
        """Type index representing 'absent' (interval not scheduled)."""
        return self._absent_type

    @property
    def total_cols(self) -> int:
        """Total columns including special types (last, absent)."""
        return self._n_cols + 2

    def _get_last_value(self, row: int) -> int | float:
        """Get the last_value for a given row."""
        if isinstance(self.last_value, (int, float)):
            return self.last_value
        return self.last_value[row]

    def _get_absent_value(self, row: int) -> int | float:
        """Get the absent_value for a given row."""
        if isinstance(self.absent_value, (int, float)):
            return self.absent_value
        return self.absent_value[row]

    def build_extended_matrix(self) -> list[list[int | float]]:
        """
        Build the full matrix including last and absent columns.

        Returns:
            Matrix of shape [n_rows][n_cols + 2] where:
            - columns 0..n_cols-1 are regular transitions
            - column n_cols is the "last" value
            - column n_cols+1 is the "absent" value
        """
        extended = []
        for i, row in enumerate(self.matrix):
            new_row = list(row) + [self._get_last_value(i), self._get_absent_value(i)]
            extended.append(new_row)
        return extended

    def _ensure_flat_vars(self) -> None:
        """Create flattened pycsp3 VarArray for element constraints (lazy)."""
        if self._flat_vars is not None:
            return

        try:
            from pycsp3 import VarArray
        except ImportError:
            raise ImportError("pycsp3 is required for element constraints")

        # Build extended matrix with last/absent columns
        extended = self.build_extended_matrix()
        
        # Flatten to 1D for element constraint
        flat = [val for row in extended for val in row]
        
        # Create VarArray with singleton domains (constants)
        # Use a unique name based on id to avoid conflicts
        # Note: XCSP3 IDs must start with a letter, not underscore
        var_id = f"tm{id(self)}"
        self._flat_vars = VarArray(
            size=len(flat),
            dom=lambda k: {int(flat[k])},  # Singleton domain = constant
            id=var_id,
        )

    def __getitem__(self, indices: tuple) -> Any:
        """
        Index the matrix with expressions.

        Args:
            indices: Tuple of (row_index, col_index) where each can be:
                     - An integer constant
                     - A pycsp3 variable or expression
                     - The result of type_of_next() etc.

        Returns:
            A pycsp3 element expression that evaluates to matrix[row][col].

        Example:
            M = TransitionMatrix(travel_times)
            cost = M[type_i, type_of_next(route, interval)]
        """
        if not isinstance(indices, tuple) or len(indices) != 2:
            raise TypeError("TransitionMatrix requires 2D indexing: M[row, col]")

        row_idx, col_idx = indices

        # Ensure flat vars exist
        self._ensure_flat_vars()

        # Compute linear index: row * total_cols + col
        total_cols = self.total_cols
        
        # Build the linear index expression
        try:
            linear_idx = row_idx * total_cols + col_idx
        except TypeError:
            # If indices don't support arithmetic, wrap them
            from pycsp3.classes.nodes import Node, TypeNode
            row_node = row_idx if hasattr(row_idx, 'cnt') else row_idx
            col_node = col_idx if hasattr(col_idx, 'cnt') else col_idx
            linear_idx = Node.build(
                TypeNode.ADD,
                Node.build(TypeNode.MUL, row_node, total_cols),
                col_node
            )

        # Return element expression
        return self._flat_vars[linear_idx]

    def get_value(self, row: int, col: int) -> int | float:
        """
        Get a constant value from the matrix (no expression).

        Use this for debugging or when indices are known constants.
        For variable indices, use __getitem__ instead.
        """
        if col == self._last_type:
            return self._get_last_value(row)
        elif col == self._absent_type:
            return self._get_absent_value(row)
        else:
            return self.matrix[row][col]


def element(array: Sequence, index: Any) -> Any:
    """
    Create an element expression for array indexing with a variable index.

    This provides a clean way to access array[index] where index is a
    pycsp3 variable or expression.

    Args:
        array: A list of values or VarArray.
        index: A pycsp3 variable, expression, or integer.

    Returns:
        A pycsp3 element expression.

    Example:
        costs = [10, 20, 30, 40, 50]
        idx = type_of_next(route, interval)
        cost = element(costs, idx)  # Returns costs[type_of_next(...)]
    """
    try:
        from pycsp3 import VarArray
        from pycsp3.classes.main.variables import Variable
    except ImportError:
        raise ImportError("pycsp3 is required for element constraints")

    # If index is a constant integer, just return the value
    if isinstance(index, int):
        return array[index]

    # If array is already a VarArray, use it directly
    if hasattr(array, '__getitem__') and hasattr(array[0] if array else None, 'dom'):
        return array[index]

    # Convert constant list to VarArray with singleton domains
    # Note: XCSP3 IDs must start with a letter, not underscore
    var_id = f"elem{id(array)}"
    var_array = VarArray(
        size=len(array),
        dom=lambda k: {int(array[k])},
        id=var_id,
    )
    
    return var_array[index]


def element2d(matrix: Sequence[Sequence], row_idx: Any, col_idx: Any) -> Any:
    """
    Create an element expression for 2D array indexing with variable indices.

    This provides matrix[row][col] access where row and col can be expressions.

    Args:
        matrix: A 2D list of values.
        row_idx: Row index (variable or expression).
        col_idx: Column index (variable or expression).

    Returns:
        A pycsp3 element expression.

    Example:
        travel = [[0, 10, 20], [10, 0, 15], [20, 15, 0]]
        i = type_of(interval_from)
        j = type_of_next(route, interval_from)
        cost = element2d(travel, i, j)
    """
    try:
        from pycsp3 import VarArray
    except ImportError:
        raise ImportError("pycsp3 is required for element constraints")

    # If both indices are constants, return the value directly
    if isinstance(row_idx, int) and isinstance(col_idx, int):
        return matrix[row_idx][col_idx]

    # Flatten the matrix
    n_rows = len(matrix)
    n_cols = len(matrix[0])
    flat = [matrix[i][j] for i in range(n_rows) for j in range(n_cols)]

    # Create VarArray for flattened matrix
    # Note: XCSP3 IDs must start with a letter, not underscore
    var_id = f"elem2d{id(matrix)}"
    flat_vars = VarArray(
        size=len(flat),
        dom=lambda k: {int(flat[k])},
        id=var_id,
    )

    # Compute linear index
    linear_idx = row_idx * n_cols + col_idx

    return flat_vars[linear_idx]
