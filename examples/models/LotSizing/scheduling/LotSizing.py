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
prod_seq = SequenceVar(intervals=orders, types=list(O), name="prod_seq")

# Build setup-cost matrix at order granularity.
# CSPLib data is usually already order-indexed (+ a trailing dummy row/col),
# but we also support item-type matrices.
if len(changeCosts) >= nOrders and all(len(row) >= nOrders for row in changeCosts[:nOrders]):
    setup_matrix = [row[:nOrders] for row in changeCosts[:nOrders]]
else:
    setup_matrix = [[changeCosts[itemTypes[i]][itemTypes[j]] for j in O] for i in O]

M = ElementMatrix(
    matrix=setup_matrix,
    last_value=[0] * nOrders,
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
    M[i][next_arg(prod_seq, orders[i], last_value=M.last_type, absent_value=M.absent_type)]
    for i in O
)
inventory_cost = Sum(inventoryCosts[itemTypes[i]] * (duePeriods[i] - start_time(orders[i])) for i in O)

minimize(setup_cost + inventory_cost)
