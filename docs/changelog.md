# Changelog

All notable changes to pycsp3-scheduling will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-01

### Added

- **Core Variable Types**
  - `IntervalVar` class for representing tasks/activities
  - `SequenceVar` class for ordered sequences on disjunctive resources
  - `IntervalVarArray` and `IntervalVarDict` factory functions
  - `SequenceVarArray` factory function

- **Expression Functions**
  - `start_of()`, `end_of()`, `size_of()`, `length_of()`, `presence_of()`
  - `overlap_length()` for computing interval overlap
  - `expr_min()`, `expr_max()` utility functions
  - Sequence accessors: `start_of_next()`, `end_of_prev()`, etc.

- **Precedence Constraints**
  - Before constraints: `end_before_start()`, `start_before_start()`, etc.
  - At constraints: `start_at_start()`, `end_at_end()`, etc.
  - Support for delay parameter

- **Grouping Constraints**
  - `span()` - main interval spans sub-intervals
  - `alternative()` - select from alternative intervals
  - `synchronize()` - synchronize intervals with a main interval

- **Sequence Constraints**
  - `SeqNoOverlap()` with optional transition matrix
  - Ordering: `first()`, `last()`, `before()`, `previous()`
  - Consistency: `same_sequence()`, `same_common_subsequence()`

- **Cumulative Functions**
  - `CumulFunction` class for resource consumption modeling
  - Elementary functions: `pulse()`, `step_at()`, `step_at_start()`, `step_at_end()`
  - Constraints: `cumul_range()`, `always_in()` for cumulative
  - Accessors: `height_at_start()`, `height_at_end()`

- **State Functions**
  - `StateFunction` class for discrete resource states
  - `TransitionMatrix` for state transition times
  - Constraints: `always_equal()`, `always_constant()`, `always_no_state()`

- **Interop Helpers**
  - `start_time()`, `end_time()` for pycsp3 integration
  - `presence_time()` for optional interval handling
  - `interval_value()` for extracting solution values

- **Examples**
  - Job Shop Scheduling
  - Flow Shop Scheduling
  - Open Shop Scheduling
  - Flexible Job Shop
  - RCPSP and variants (MRCPSP, CyclicRCPSP, MSPSP)
  - Aircraft Landing
  - Employee Scheduling

### Notes

- First public release
- Requires Python >= 3.10
- Requires pycsp3 >= 2.5
