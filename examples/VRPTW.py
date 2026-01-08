"""
Vehicle Routing Problem with Time Windows (VRPTW)

Objective: Minimize total travel distance using the type_of_next pattern,
including depot departure via a fictive depot visit per vehicle.

This example demonstrates the CP Optimizer-style distance objective:

    for k in vehicles:
        for i in intervals:
            distance += M[type_i, type_of_next(route[k], visit[k][i], last, absent)]

Where:
- M is the transition matrix with travel distances between customers
- type_i is the type of interval i (0=depot, 1..n=customers)
- type_of_next returns the type of the next interval in the sequence
- last_value = distance back to depot (when interval is last in route)
- absent_value = 0 (no cost if interval is not scheduled)

Key functions used:
- ElementMatrix: 2D matrix indexed by expressions (like CP Optimizer's IloNumArray2)
- type_of_next: Returns type of next interval in sequence (pycsp3 variable)
- SeqNoOverlap: Ensures non-overlapping intervals with transition times
- alternative: Assigns each customer to exactly one vehicle
"""

from pycsp3 import *
from pycsp3_scheduling import *
from pycsp3_scheduling.variables.interval import clear_interval_registry
from pycsp3_scheduling.expressions.element import ElementMatrix
from pycsp3_scheduling.expressions.sequence_expr import type_of_next


# =============================================================================
# Problem Data
# =============================================================================
# Problem data
n_vehicles = 3
n_customers = 6
vehicle_capacity = 15

# Customer data: (earliest, latest, service_time, demand)
# Index 0 is depot, 1-6 are customers
customers = [
    (0, 100, 0, 0),    # Depot: available [0,100], no service time, no demand
    (10, 40, 5, 3),    # Customer 1
    (20, 50, 8, 5),    # Customer 2
    (15, 45, 6, 4),    # Customer 3
    (15, 20, 4, 6),    # Customer 4
    (25, 50, 7, 3),    # Customer 5
    (40, 80, 5, 4),    # Customer 6
]

# Travel times matrix (symmetric)
# travel[i][j] = time to go from i to j
travel = [
    [0, 10, 15, 12, 20, 20, 25],  # From depot
    [10, 0, 8, 10, 15, 12, 20],   # From customer 1
    [15, 8, 0, 6, 10, 8, 15],     # From customer 2
    [12, 10, 6, 0, 12, 10, 18],   # From customer 3
    [20, 15, 10, 12, 0, 6, 10],   # From customer 4
    [20, 12, 8, 10, 6, 0, 8],     # From customer 5
    [25, 20, 15, 18, 10, 8, 0],   # From customer 6
]

print("VRPTW Instance:")
print(f"  Vehicles: {n_vehicles} (capacity: {vehicle_capacity})")
print(f"  Customers: {n_customers}")
print()
print("Customer data:")
print(f"  {'ID':<4} {'Window':<12} {'Service':<8} {'Demand':<6}")
for i, (e, l, s, d) in enumerate(customers):
    if i == 0:
        print(f"  {i:<4} [{e:>3}, {l:>3}]     {'depot':<8} {'-':<6}")
    else:
        print(f"  {i:<4} [{e:>3}, {l:>3}]     {s:<8} {d:<6}")

# =============================================================================
# Clear any previous model state
clear()
clear_interval_registry()

# Create a depot interval per vehicle (fictive visit fixed at time 0)
depots = []

# Create visit intervals for each (vehicle, customer) pair
# visits[v][c] = interval for vehicle v visiting customer c
visits = []
for v in range(n_vehicles):
    depot = IntervalVar(
        start=0,
        size=0,
        name=f"V{v}_Depot"
    )
    depots.append(depot)
    vehicle_visits = []
    for c in range(1, n_customers + 1):  # Skip depot (index 0)
        earliest, latest, service, demand = customers[c]
        visit = IntervalVar(
            start=(earliest, latest),  # Time window constraint built into bounds
            size=service,
            optional=True,
            name=f"V{v}_C{c}"
        )
        vehicle_visits.append(visit)
    visits.append(vehicle_visits)

print(f"Created {n_vehicles} depot intervals fixed at time 0")
print(f"Created {n_vehicles * n_customers} optional visit intervals")
print(f"  visits[vehicle][customer-1] for customer 1..{n_customers}")

# Create main (abstract) visit interval for each customer
# This represents "customer c is visited" regardless of which vehicle
main_visits = []
for c in range(1, n_customers + 1):
    earliest, latest, service, demand = customers[c]
    main = IntervalVar(
        start=(earliest, latest),
        size=service,
        name=f"C{c}"
    )
    main_visits.append(main)

print(f"Created {n_customers} main visit intervals")

# Alternative constraint: each customer visited by exactly one vehicle
# Only for customer visits (indices 0..n_customers-1), not depot
for c in range(n_customers):
    alternatives_for_c = [visits[v][c] for v in range(n_vehicles)]
    satisfy(alternative(main_visits[c], alternatives_for_c))

print("Alternative constraints: each customer assigned to exactly one vehicle")

# Create sequence variable for each vehicle route
# The sequence determines the order of visits (depot + customers)
routes = []
for v in range(n_vehicles):
    # Types align with travel matrix indices: 0=depot, 1..n_customers=customers
    types = [0] + [c + 1 for c in range(n_customers)]
    route = SequenceVar(
        intervals=[depots[v]] + visits[v],
        types=types,
        name=f"route_{v}"
    )
    routes.append(route)

print(f"Created {n_vehicles} route sequences")

# Build transition matrix for travel times (includes depot as type 0)
# transition[i][j] = travel time from type i to type j
transition_matrix = [row[:] for row in travel]

# No-overlap with travel times on each route
for v in range(n_vehicles):
    satisfy(SeqNoOverlap(routes[v], transition_matrix=transition_matrix))

print("Travel time constraints added via SeqNoOverlap with transition matrix")
print(f"  Example: C2 -> C3 requires {travel[2][3]} time units")

# Capacity constraint: total demand on each route <= capacity
# Only sum over customer visits (indices 0..n_customers-1), not depot
for v in range(n_vehicles):
    route_demand = Sum(
        customers[c+1][3] * presence_time(visits[v][c])  # demand * presence
        for c in range(n_customers)  # Customer indices only
    )
    satisfy(route_demand <= vehicle_capacity)

print(f"Capacity constraints: each route demand <= {vehicle_capacity}")


# =============================================================================
# Objective: Minimize total travel distance using type_of_next pattern
# =============================================================================
# This is the CP Optimizer-style objective using ElementMatrix and type_of_next.
#
# Matrix structure:
#   M[type_i, type_j] = distance from type_i to type_j (type 0 is depot)
#   M[type_i, last_type] = distance from type_i back to depot
#   M[type_i, absent_type] = 0 (no cost if interval is absent)
#
# For each vehicle route and each interval:
#   cost += M[type_i, type_of_next(route, interval, last_value, absent_value)]

# Build the transition cost matrix (includes depot as type 0)
cost_matrix = [row[:] for row in travel]

# Distance back to depot for each type (when interval is last)
# Row 0 (depot) has 0 cost when no customer is visited
depot_distances = [0] + [travel[i][0] for i in range(1, n_customers + 1)]

# Create ElementMatrix with special values for boundary cases
M = ElementMatrix(
    matrix=cost_matrix,
    last_value=depot_distances,  # Return to depot when last in route
    absent_value=0,              # No cost if interval not scheduled
)

print(f"\nDistance objective using type_of_next pattern:")
print(f"  Matrix size: {M.n_rows}x{M.n_cols} (+ last_type={M.last_type}, absent_type={M.absent_type})")
print(f"  Example: Depot->C1 = {M.get_value(0, 1)}, C2->depot = {M.get_value(2, M.last_type)}")

# Build objective: sum of M[type_i, type_of_next(route, interval)]
distance_terms = []
for v in range(n_vehicles):
    depot_next = type_of_next(
        routes[v],
        depots[v],
        last_value=M.last_type,
        absent_value=M.absent_type,
    )
    distance_terms.append(M[0, depot_next])
    for c in range(n_customers):
        type_i = c + 1  # Type of this interval (1-indexed customer)
        next_type = type_of_next(
            routes[v],
            visits[v][c],
            last_value=M.last_type,    # Use matrix's last column index
            absent_value=M.absent_type,  # Use matrix's absent column index
        )
        # M[type_i, next_type] gives the transition cost
        distance_terms.append(M[type_i, next_type])

# Note: This objective covers depot departure, customer-to-customer,
# and return-to-depot distances.

minimize(Sum(distance_terms))

# Solve
result = solve(sols=5, verbose=True)

if result in (SAT, OPTIMUM):
    print("\n" + "=" * 60)
    print("Solution found!" + (" (Optimal)" if result == OPTIMUM else ""))
    print("=" * 60)

    total_distance = 0

    # Extract routes
    for v in range(n_vehicles):
        route_visits = []
        route_demand = 0

        # Check customer visits only (not depot)
        for c in range(n_customers):
            val = interval_value(visits[v][c])
            if val is not None:  # This visit is selected
                customer_id = c + 1
                route_visits.append((val.start, customer_id, val.end))
                route_demand += customers[customer_id][3]

        route_visits.sort()  # Sort by start time

        if route_visits:
            route_str = " -> ".join(f"C{c}[{s},{e}]" for s, c, e in route_visits)

            # Calculate route distance (depot -> customers -> depot)
            route_distance = travel[0][route_visits[0][1]]  # Depot to first
            for i in range(len(route_visits) - 1):
                from_cust = route_visits[i][1]
                to_cust = route_visits[i+1][1]
                route_distance += travel[from_cust][to_cust]
            route_distance += travel[route_visits[-1][1]][0]  # Last to depot
            total_distance += route_distance

            print(f"Vehicle {v}: 0 -> {route_str} -> 0")
            print(f"           demand: {route_demand}/{vehicle_capacity}, distance: {route_distance}")
        else:
            print(f"Vehicle {v}: unused")

    print(f"\nTotal travel distance: {total_distance}")
    print(f"Objective value (departure + inter-customer + return): {bound()}")
else:
    print("No solution found")

if result in (SAT, OPTIMUM):
    # Extract visualization data (convert to plain Python ints to avoid pycsp3 issues)
    panels = []

    # One panel per vehicle
    for v in range(n_vehicles):
        intervals = []
        for c in range(n_customers):
            val = interval_value(visits[v][c])
            if val is not None:
                customer_id = c + 1
                intervals.append((int(val.start), int(val.end), f"C{customer_id}", customer_id))
        panels.append({"name": f"Vehicle {v}", "intervals": intervals})

    # Panel showing all visits (overview)
    all_intervals = []
    for c in range(n_customers):
        val = interval_value(main_visits[c])
        customer_id = c + 1
        all_intervals.append((int(val.start), int(val.end), f"C{customer_id}", customer_id))
    panels.append({"name": "All Customers", "intervals": all_intervals})

    visu_data = {"panels": panels}

    # Compute makespan and tightest deadline
    makespan = max(intv[1] for intv in all_intervals)
    tightest_deadline = min(customers[c][1] for c in range(1, n_customers + 1))

    # Build legend entries
    legends = [(f"Customer {c}", c) for c in range(1, n_customers + 1)]

    # Build vertical line markers
    vlines = [(tightest_deadline, "red", "dashed", "Tight deadline")]

    # Use subprocess-safe visualization to avoid pycsp3 operator conflicts
    if visu.is_visu_enabled():
        visu.savefig_safe(
            "vrptw_schedule.png",
            visu_data,
            title="VRPTW Schedule",
            horizon=makespan + 10,
            legends=legends,
            vlines=vlines,
        )
    else:
        print("Visualization disabled (matplotlib not available)")
