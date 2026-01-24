"""
Element expressions for array indexing with variable indices.

This module provides the ability to index into arrays using expressions
(like next_arg).

The key use case is building objectives like:
    sum(M[type_i][next_arg(route, visit[i], last, abs)] for i in intervals)

Where M is a transition cost matrix indexed by interval types.

Also provides ElementArray for transparent array[variable_index] syntax:
    costs = ElementArray([10, 20, 30, 40, 50])
    idx = next_arg(route, interval)
    cost = costs[idx]  # Automatically creates element expression
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, overload


@dataclass
class ElementMatrix:
    """
    A 2D matrix that can be indexed with expressions.

    This class wraps a 2D list of values and provides element-style indexing
    where indices can be pycsp3 variables or expressions. It's designed to
    work with next_arg() for computing transition costs in scheduling.

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
                cost = M[type_i, next_arg(route[k], visit[k][i])]

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

        from pycsp3 import VarArray

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

    def __getitem__(self, index: int | tuple | Any) -> Any:
        """
        Index the matrix with expressions.

        Supports two syntaxes:
        - M[row, col] - tuple indexing
        - M[row][col] - chained indexing (row returns a proxy)

        Args:
            index: Can be:
                - tuple (row, col): Returns element at (row, col)
                - int: Returns an _ElementMatrixRowProxy for chained indexing
                - variable/expression: Returns a proxy for deferred column access

        Returns:
            - If tuple: A pycsp3 element expression for matrix[row][col]
            - If int/variable: A proxy for M[row][col] chained access

        Example:
            M = ElementMatrix(travel_times, last_value=depot, absent_value=0)
            cost = M[type_i, next_arg(route, interval)]  # tuple syntax
            cost = M[type_i][next_arg(route, interval)]  # chained syntax
        """
        # Tuple indexing: M[row, col]
        if isinstance(index, tuple):
            if len(index) != 2:
                raise TypeError("ElementMatrix requires 2D indexing: M[row, col]")
            row_idx, col_idx = index
            return self._get_element(row_idx, col_idx)

        # Single index - return proxy for chained access M[row][col]
        return _ElementMatrixRowProxy(self, index)

    def _get_element(self, row_idx: Any, col_idx: Any) -> Any:
        """
        Get element at (row, col) with variable or constant indices.

        Args:
            row_idx: Row index (int or pycsp3 variable/expression)
            col_idx: Column index (int or pycsp3 variable/expression)

        Returns:
            Value if both indices are int, otherwise pycsp3 element expression.
        """
        # If both are constants, return value directly
        if isinstance(row_idx, int) and isinstance(col_idx, int):
            return self.get_value(row_idx, col_idx)

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
        idx = next_arg(route, interval)
        cost = element(costs, idx)  # Returns costs[next_arg(...)]
    """
    from pycsp3 import VarArray

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
        j = next_arg(route, interval_from)
        cost = element2d(travel, i, j)
    """
    from pycsp3 import VarArray

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


class ElementArray(Sequence):
    """
    A wrapper that allows transparent array[variable_index] syntax.

    This class wraps a list of values and overrides __getitem__ to create
    pycsp3 element expressions when indexed with a variable or expression.

    Unlike regular Python lists, ElementArray supports:
    - Integer indexing (returns the value directly)
    - Variable indexing (returns a pycsp3 element expression)

    Example:
        from pycsp3_scheduling.expressions import ElementArray

        # Create an ElementArray from costs
        costs = ElementArray([10, 20, 30, 40, 50])

        # Index with a constant - returns 30
        costs[2]

        # Index with a variable/expression - returns element expression
        idx = next_arg(route, interval)
        cost = costs[idx]  # Creates element(costs, idx) automatically

        # Use in objective
        minimize(Sum(costs[next_arg(route, v)] for v in visits))

    Attributes:
        data: The underlying list of values.
        _var_array: Cached pycsp3 VarArray for element constraints.
    """

    def __init__(self, data: list[int | float]) -> None:
        """
        Initialize an ElementArray.

        Args:
            data: A list of numeric values.
        """
        if not data:
            raise ValueError("ElementArray cannot be empty")
        self._data = list(data)
        self._var_array: Any = None

    @property
    def data(self) -> list[int | float]:
        """The underlying data list."""
        return self._data

    def __len__(self) -> int:
        """Return the number of elements."""
        return len(self._data)

    @overload
    def __getitem__(self, index: int) -> int | float: ...

    @overload
    def __getitem__(self, index: Any) -> Any: ...

    def __getitem__(self, index: int | Any) -> int | float | Any:
        """
        Index the array, supporting both constants and variables.

        Args:
            index: An integer constant or a pycsp3 variable/expression.

        Returns:
            - If index is an int: Returns the value at that index.
            - If index is a variable/expression: Returns a pycsp3 element expression.

        Example:
            arr = ElementArray([10, 20, 30])
            arr[1]        # Returns 20
            arr[var_idx]  # Returns element expression
        """
        # Constant integer index - return value directly
        if isinstance(index, int):
            return self._data[index]

        # Variable index - create element expression
        return element(self._data, index)

    def __repr__(self) -> str:
        return f"ElementArray({self._data!r})"

    def __iter__(self):
        """Iterate over the values."""
        return iter(self._data)


class _ElementMatrixRowProxy:
    """
    Internal proxy for deferred column indexing when row is a variable.

    This allows matrix[var_row][col] syntax to work correctly with ElementMatrix.
    """

    def __init__(self, matrix: ElementMatrix, row_idx: Any) -> None:
        self._matrix = matrix
        self._row_idx = row_idx

    def __getitem__(self, col_idx: Any) -> Any:
        """
        Index with column, creating element expression.

        Args:
            col_idx: Column index (int or variable/expression).

        Returns:
            A pycsp3 element expression for matrix[row][col].
        """
        return self._matrix._get_element(self._row_idx, col_idx)

