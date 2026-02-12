"""
Discrete Lot-Sizing and Scheduling (CSPLib prob058) with IntervalVar + SequenceVar.

This scheduling reformulation represents each order as a unit-duration interval
scheduled on a single production resource.
Setup costs are computed from the predecessor relation in the production sequence,
and inventory cost is driven by due date minus production period.
"""

from collections import defaultdict

from pycsp3 import *
from pycsp3_scheduling import (
    IntervalVar,
    SequenceVar,
    SeqNoOverlap,
    ElementMatrix,
    start_time,
    end_before_start,
)
from pycsp3_scheduling.expressions.sequence_expr import next_arg

if data is None:
    raise ValueError("Missing input data. Run with -data=<json file>.")

nPeriods = data.nPeriods
inventoryCost = data.inventoryCost
changeCosts = [list(row) for row in data.changeCosts]
nbOfOrders = list(data.nbOfOrders)
orders_raw = list(data.orders)

duePeriods = [o.duePeriods for o in orders_raw]
itemTypes = [o.itemTypes for o in orders_raw]
nOrders = len(orders_raw)
nItemTypes = len(nbOfOrders)
inventoryCosts = [inventoryCost] * nItemTypes if isinstance(inventoryCost, int) else list(inventoryCost)
assert len(inventoryCosts) == nItemTypes
O = range(nOrders)

assert nOrders <= nPeriods

# Intervals for produced orders (one period per order).
orders = [
    IntervalVar(start=(0, nPeriods - 1), size=1, name=f"order_{i}")
    for i in O
]

# One disjunctive machine handling all productions.
prod_seq = SequenceVar(intervals=orders, types=itemTypes, name="prod_seq")

# Build setup-cost matrix at item-type granularity.
# Some datasets provide a type matrix directly, others provide an order matrix
# with an extra dummy row/column. In the latter case, we extract one
# representative row/column per item type using order_number convention.
is_type_matrix = (
    len(changeCosts) >= nItemTypes
    and all(len(row) >= nItemTypes for row in changeCosts[:nItemTypes])
    and len(changeCosts) <= nItemTypes + 1
)
if is_type_matrix:
    setup_matrix = [row[:nItemTypes] for row in changeCosts[:nItemTypes]]
else:
    first_order_of_type = []
    offset = 0
    for count in nbOfOrders:
        first_order_of_type.append(offset if count > 0 else None)
        offset += count

    setup_matrix = [[0 for _ in range(nItemTypes)] for _ in range(nItemTypes)]
    present_types = [t for t, count in enumerate(nbOfOrders) if count > 0]
    for t1 in present_types:
        i = first_order_of_type[t1]
        assert i is not None
        for t2 in present_types:
            j = first_order_of_type[t2]
            assert j is not None
            setup_matrix[t1][t2] = changeCosts[i][j]

M = ElementMatrix(
    matrix=setup_matrix,
    last_value=[0] * nItemTypes,
    absent_value=0,
)

by_type: dict[int, list[int]] = defaultdict(list)
for i, t in enumerate(itemTypes):
    by_type[t].append(i)

satisfy(
    # Single production resource.
    SeqNoOverlap(prod_seq),

    # Every order must be produced no later than its due period.
    [start_time(orders[i]) <= duePeriods[i] for i in O],

    # Symmetry breaking: same-type orders are produced in index order.
    [
        end_before_start(orders[idx[k]], orders[idx[k + 1]])
        for idx in by_type.values()
        for k in range(len(idx) - 1)
    ],
)

setup_cost = Sum(
    M[itemTypes[i]][next_arg(prod_seq, orders[i], last_value=M.last_type, absent_value=M.absent_type)]
    for i in O
)
inventory_cost = Sum(inventoryCosts[itemTypes[i]] * (duePeriods[i] - start_time(orders[i])) for i in O)

minimize(setup_cost + inventory_cost)
