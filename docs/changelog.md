# Changelog

All notable changes to pycsp3-scheduling will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-01-23

### Added

- **Bounds Constraints**: `release_date`, `deadline`, `time_window`
  - Convenience constraints for setting time bounds on intervals
  - `release_date(interval, time)` - interval cannot start before given time
  - `deadline(interval, time)` - interval must complete by given time
  - `time_window(interval, earliest_start, latest_end)` - combined release + deadline
  - Properly handles optional intervals with presence escape clauses

- **State Helpers**: `requires_state`, `sets_state`
  - Convenience functions for working with state functions
  - `requires_state(interval, state_func, state)` - interval requires specific state (simpler API for always_equal)
  - `sets_state(interval, state_func, before_state, after_state)` - interval transitions state

- **IntervalVar Comparison Operators**
  - `interval >= time` - shorthand for `release_date(interval, time)`
  - `interval <= time` - shorthand for `deadline(interval, time)`
  - `interval > time` - strict release (start > time)
  - `interval < time` - strict deadline (end < time)
  - Works in list comprehensions: `satisfy(t >= 0 for t in tasks)`

### Changed

- Consolidated internal validation functions into `_pycsp3.py` to reduce code duplication
- Test files renamed to follow module-based naming convention

## [0.3.0] - 2026-01-21

  - Renamed `type_of_next`/`type_of_prev` to `next_arg`/`prev_arg` (old names still work as aliases)
  - **Forbidden Time Constraints**: `forbid_start`, `forbid_end`, `forbid_extent`
    - Prevent intervals from starting, ending, or spanning during specific time periods
  - **Presence Constraints**: `presence_implies`, `presence_or`, `presence_xor`
    - Express logical relationships between optional interval presence
  - **Group Presence Constraints**: `all_present_or_all_absent`, `presence_or_all`, `if_present_then`
    - Handle all-or-nothing groups and conditional constraints
  - **Cardinality Constraints**: `at_least_k_present`, `at_most_k_present`, `exactly_k_present`
    - Control how many optional intervals must be present
  - **Chain Constraints**: `chain`, `strict_chain`
    - Enforce sequential execution with optional delays
  - **Overlap Constraints**: `must_overlap`, `overlap_at_least`
    - Require intervals to share time or overlap by minimum duration
  - **Disjunctive Constraint**: `disjunctive`
    - Unary resource constraint (at most one interval active at a time)
  - **No-Overlap Pairwise**: `no_overlap_pairwise`
    - Simple pairwise no-overlap without sequence variable overhead
  - **Aggregate Expressions**: `count_present`, `earliest_start`, `latest_end`, `span_length`, `makespan`
    - Aggregate expressions over interval collections for constraints and objectives
  - Updated documentation

## [0.1.7] - 2026-01-05
  - Fixed VRPTW example notebook with distance minimization objective
  - Updated documentation for ElementMatrix and type_of_next/prev
  - Complete SeqNoOverlap support with transition matrix

## [0.1.6] - 2026-01-04

### Added

- **ElementMatrix** class for 2D array indexing with expressions
  - Supports indexing with pycsp3 variables (like CP Optimizer's `IloNumArray2`)
  - Built-in `last_value` and `absent_value` for boundary cases
  - Properties: `last_type`, `absent_type` for column indices
  - `get_value()` method for debugging/constant access

- **next_arg / prev_arg** (formerly `type_of_next`/`type_of_prev`) now return pycsp3 variables
  - Returns the ID of the next/previous interval in a sequence (similar to pycsp3's `maximum_arg`)
  - Can be used directly in `ElementMatrix` indexing
  - Enables CP Optimizer-style distance objectives:
    `M[id_i, next_arg(route, interval, last_value, absent_value)]`

- **element() and element2d()** helper functions
  - Array indexing with variable indices

### Fixed

- XCSP3 variable ID naming (must start with letter, not underscore)
  - Fixed prefixes: `tonext`, `toprev`, `tm`, `elem`, `elem2d`

### Changed

- VRPTW example updated to use `ElementMatrix` + `next_arg` for distance objective
- VRPTW notebooks updated with working distance minimization

## [0.1.5] - 2026-01-04
  - Added ElementMatrix expression for 2D array indexing
  - Add vrptw example 

## [0.1.4] - 2026-01-03
  - Added Visualization module and statistics functions

## [0.1.2] - 2026-01-03
  - `IntervalVar` intensity functions with granularity scaling

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
  - `IntervalValue` for attribute/dict-style interval results
  - `model_statistics()` and `solution_statistics()` for model/solve stats

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
