# Contributing

We welcome contributions to pycsp3-scheduling! This guide will help you get started.

## Getting Started

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pycsp3-scheduling.git
   cd pycsp3-scheduling
   ```

3. **Set up development environment**:
   ```bash
   pip install -e ".[dev]"
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pycsp3_scheduling

# Run specific test file
pytest tests/test_interval.py

# Run with verbose output
pytest -v
```

### Code Quality

We use several tools to maintain code quality:

```bash
# Linting
ruff check .

# Auto-format code
ruff format .

# Type checking
mypy pycsp3_scheduling
```

### Pre-commit Checks

Before committing, ensure:
1. All tests pass
2. Code is formatted with `ruff format`
3. No linting errors from `ruff check`
4. Type hints are correct (`mypy`)

## Coding Standards

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all public functions
- Maximum line length: 100 characters
- Use `from __future__ import annotations` for forward references

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: int, param2: str) -> bool:
    """Short description of the function.

    Longer description if needed, explaining the function's
    behavior in more detail.

    Args:
        param1: Description of first parameter.
        param2: Description of second parameter.

    Returns:
        Description of return value.

    Raises:
        TypeError: When input types are invalid.
        ValueError: When values are out of range.

    Example:
        >>> result = function_name(1, "test")
        >>> print(result)
        True
    """
    ...
```

### Naming Conventions

- Classes: `PascalCase` (e.g., `IntervalVar`, `SequenceVar`)
- Functions: `snake_case` (e.g., `end_before_start`, `interval_value`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `INTERVAL_MIN`, `INTERVAL_MAX`)
- Private functions: `_leading_underscore`

## Project Structure

```
pycsp3_scheduling/
├── __init__.py          # Public API exports
├── interop.py           # pycsp3 bridge functions
├── variables/           # Variable types
│   ├── interval.py      # IntervalVar
│   └── sequence.py      # SequenceVar
├── expressions/         # Expression functions
│   └── interval_expr.py # start_of, end_of, etc.
├── constraints/         # Constraint functions
│   ├── precedence.py    # Precedence constraints
│   ├── grouping.py      # span, alternative, synchronize
│   └── sequence.py      # SeqNoOverlap, first, last, etc.
└── functions/           # Cumulative and state functions
    ├── cumul_functions.py
    └── state_functions.py
```

## Adding New Features

### Adding a New Constraint

1. **Choose the appropriate module** (or create a new one)
2. **Implement the constraint function**:
   - Validate input types
   - Build pycsp3 Node expression
   - Return the constraint
3. **Add to exports** in `__init__.py`
4. **Write tests** in `tests/test_constraints.py`
5. **Document** in the API reference

Example pattern:
```python
def new_constraint(a: IntervalVar, b: IntervalVar, param: int = 0):
    """
    Description of the constraint.

    Args:
        a: First interval.
        b: Second interval.
        param: Optional parameter.

    Returns:
        A pycsp3 Node representing the constraint.
    """
    if not isinstance(a, IntervalVar) or not isinstance(b, IntervalVar):
        raise TypeError("new_constraint expects IntervalVar inputs")
    
    Node, TypeNode = _get_node_builders()
    # Build constraint...
    return Node.build(TypeNode.XXX, ...)
```

### Adding a New Variable Type

1. **Create module** in `variables/`
2. **Implement class** with `@dataclass` decorator
3. **Include validation** in `__post_init__`
4. **Add registry** for model compilation
5. **Export** from `variables/__init__.py` and main `__init__.py`
6. **Write comprehensive tests**

## Testing Guidelines

### Test Organization

- Use class-based test organization
- One test class per major feature
- Use fixtures for setup/teardown

```python
import pytest
from pycsp3_scheduling import IntervalVar

class TestIntervalVar:
    @pytest.fixture(autouse=True)
    def reset_registry(self):
        """Reset registry before each test."""
        from pycsp3_scheduling.variables.interval import clear_interval_registry
        clear_interval_registry()
    
    def test_creation_with_fixed_size(self):
        task = IntervalVar(size=10, name="task")
        assert task.size_min == 10
        assert task.size_max == 10
    
    def test_creation_with_variable_size(self):
        task = IntervalVar(size=(5, 15), name="task")
        assert task.size_min == 5
        assert task.size_max == 15
```

### Test Coverage

- Aim for >90% code coverage
- Test edge cases (empty inputs, boundary values)
- Test error handling (invalid inputs)

## Submitting Changes

1. **Ensure all checks pass**:
   ```bash
   pytest
   ruff check .
   mypy pycsp3_scheduling
   ```

2. **Write clear commit messages**:
   ```
   Add end_before_start constraint with delay parameter
   
   - Implement end_before_start(a, b, delay=0)
   - Add validation for IntervalVar inputs
   - Include docstring with examples
   - Add unit tests for all cases
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request** with:
   - Clear description of changes
   - Reference to any related issues
   - Test results

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions in pull requests

Thank you for contributing!
