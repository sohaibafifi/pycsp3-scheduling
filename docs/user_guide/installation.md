# Installation

## Quick Install

Install pycsp3-scheduling from PyPI:

```bash
pip install pycsp3-scheduling
```

## Development Installation

For development or to get the latest features:

```bash
git clone https://github.com/sohaibafifi/pycsp3-scheduling.git
cd pycsp3-scheduling
pip install -e ".[dev]"
```

## Requirements

- **Python** >= 3.10
- **pycsp3** >= 2.5 (constraint programming framework)
- **lxml** >= 4.9 (for XCSP3 XML generation)

## Verifying Installation

After installation, verify everything works:

```python
from pycsp3_scheduling import __version__, IntervalVar

print(f"pycsp3-scheduling version: {__version__}")

# Quick test
task = IntervalVar(size=10, name="test_task")
print(f"Created: {task}")
```

## Optional: Installing a Solver

pycsp3-scheduling works with any solver supported by pycsp3. The default solver is ACE:

```bash
# ACE solver is included with pycsp3
# No additional installation needed
```

For other solvers, see the [pycsp3 documentation](https://pycsp.org).

## Building Documentation

To build the documentation locally:

```bash
cd docs
pip install -r requirements.txt
make html
```

The documentation will be available in `docs/_build/html/`.
