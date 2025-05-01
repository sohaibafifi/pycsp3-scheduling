# Contributing to pycsp3-scheduling

Thank you for your interest in contributing to pycsp3-scheduling!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/sohaibafifi/pycsp3-scheduling.git
   cd pycsp3-scheduling
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Code Style

This project uses:
- **ruff** for linting and formatting
- **mypy** for type checking

Run checks before committing:

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy pycsp3_scheduling
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pycsp3_scheduling --cov-report=html
```

## Project Structure

```
pycsp3_scheduling/
├── variables/       # IntervalVar, SequenceVar
├── expressions/     # start_of, end_of, etc.
├── constraints/     # Precedence, grouping, sequence constraints
├── functions/       # CumulFunction, StateFunction
├── output/          # XCSP3 output generator
└── solvers/         # Solver adapters
```

## Adding New Features

### Adding a New Constraint

1. Create or update the appropriate module in `constraints/`
2. Follow the existing constraint class pattern
3. Add exports to `constraints/__init__.py`
4. Add exports to main `__init__.py`
5. Write unit tests in `tests/`
6. Update documentation

### Adding a New Variable Type

1. Create the variable class in `variables/`
2. Implement required methods for pycsp3 integration
3. Add XCSP3 output support in `output/`
4. Write comprehensive tests

## Pull Request Process

1. Create a feature branch from `master`
2. Make your changes with clear commit messages
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request with a description of changes

## Reporting Issues

When reporting issues, please include:
- Python version
- pycsp3-scheduling version
- Minimal reproducible example
- Expected vs actual behavior

## Questions

For questions about the project, open a GitHub issue or discussion.
