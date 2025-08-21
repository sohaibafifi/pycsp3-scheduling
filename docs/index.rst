pycsp3-scheduling Documentation
=================================

**pycsp3-scheduling** is a scheduling extension for `pycsp3 <https://pycsp.org>`_
that provides interval variables, sequence variables, and comprehensive scheduling
constraints for modeling complex scheduling problems.

.. note::
   This library is designed for research-grade constraint programming with emphasis
   on mathematical correctness and seamless pycsp3 integration.

Key Features
------------

* **Interval Variables**: Represent tasks with start, end, size, and optional presence
* **Sequence Variables**: Model ordered sequences on disjunctive resources
* **Precedence Constraints**: Full set of temporal constraints (before, at)
* **Grouping Constraints**: ``span``, ``alternative``, ``synchronize``
* **Cumulative Functions**: Resource capacity modeling with ``pulse``, ``step_at_*``
* **State Functions**: Discrete resource states with transition matrices
* **XCSP3 Compatible**: Output scheduling models in XCSP3 format

Quick Example
-------------

.. code-block:: python

   from pycsp3 import *
   from pycsp3_scheduling import *

   # Create tasks
   task1 = IntervalVar(size=10, name="task1")
   task2 = IntervalVar(size=15, name="task2")

   # task1 must finish before task2 starts
   satisfy(end_before_start(task1, task2))

   # Minimize makespan
   minimize(Maximum(end_time(task1), end_time(task2)))

   if solve() in (SAT, OPTIMUM):
       print(f"task1: {interval_value(task1)}")
       print(f"task2: {interval_value(task2)}")

Getting Started
---------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/getting_started
   user_guide/scheduling_concepts
   user_guide/modeling_guide

Tutorials
---------

.. toctree::
   :maxdepth: 2
   :caption: Interactive Tutorials

   tutorials/index

API Reference
-------------

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   api/variables
   api/expressions
   api/constraints
   api/functions
   api/interop

Examples
--------

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/job_shop
   examples/rcpsp
   examples/flexible_job_shop

Additional Resources
--------------------

.. toctree::
   :maxdepth: 1
   :caption: Resources

   changelog
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Links
-----

* `PyCSP3 Documentation <https://pycsp.org>`_
* `XCSP3 Specification <https://xcsp.org/specifications/>`_
* `GitHub Repository <https://github.com/sohaibafifi/pycsp3-scheduling>`_
