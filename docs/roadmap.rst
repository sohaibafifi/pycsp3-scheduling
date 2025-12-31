Roadmap
=======

This page summarizes what's been completed and what remains for pycsp3-scheduling.

Completed ✅
------------

**Core Scheduling Features** 

- **Interval Variables**: ``IntervalVar``, ``IntervalVarArray``, ``IntervalVarDict`` with full bounds support
- **Sequence Variables**: ``SequenceVar`` with type support
- **Expressions**: ``start_of``, ``end_of``, ``size_of``, ``length_of``, ``presence_of``, ``overlap_length``
- **Precedence Constraints**: All 8 variants (``start_at_*``, ``end_at_*``, ``start_before_*``, ``end_before_*``)
- **Grouping Constraints**: ``span``, ``alternative``, ``synchronize``
- **Sequence Constraints**: ``SeqNoOverlap``, ``first``, ``last``, ``before``, ``previous``, sequence accessors
- **Cumulative Functions**: ``pulse``, ``step_at``, ``step_at_start``, ``step_at_end``, ``Cumulative``, ``cumul_range``, ``always_in``
- **State Functions**: ``StateFunction``, ``TransitionMatrix``, ``always_equal``, ``always_constant``, ``always_no_state``

**Documentation & Examples**

- API documentation, user guides, Jupyter tutorials
- Examples: Job Shop, Flexible Job Shop, RCPSP, Flow Shop, Open Shop, Employee Scheduling

Remaining Work ⏳
-----------------



**Testing**

- Achieve 90%+ code coverage
- Integration tests and benchmarks
- Python 3.9-3.12 compatibility validation

**Examples**

- Vehicle Routing with Time Windows example

**Other**

- Intensity function support for ``IntervalVar``
- ``isomorphism`` constraint
- Evaluation functions (``start_eval``, ``end_eval``, etc.)

Contributing
------------

We welcome contributions! See :doc:`contributing` for details.
