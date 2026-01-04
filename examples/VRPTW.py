"""
Vehicle Routing Problem with Time Windows (VRPTW)

Objective: Minimize total travel distance using the type_of_next pattern.

TODO : change obj based on CP Optimizer pattern:
    IloNumArray2 M(env, m + 2);
    for k in vehicles:
        for i in intervals:
            distance += M[type_i][IloTypeOfNext(route[k], visit[k][i], last, abs)]
    where M is the travel time matrix between customers:
        unsigned m = _problem->getNumberClients() + 1;
        IloNumArray2 M(env, m + 2);
        IloInt last = m;  //  Type de l'activité suivante pour la dernière activité sur la machine
        IloInt abs  = m+1; // Type de l'activité suivante pour une activité non exécutée sur la machine
        for (IloInt ti = 0; ti < m; ++ti) {
            M[ti]= IloNumArray(env, m + 2);
            unsigned  i = ti + 1;//i représente le client ti+1
            if(ti == _problem->getNumberClients()) i = 0;
            for (IloInt tj = 0; tj < m; ++tj) {
                unsigned j = tj + 1;//j représente le client ti+1
                if(tj == _problem->getNumberClients()) j = 0;
                M[ti][tj] = (_problem->getDistance(i  , j ) * 100 ); // Coût de changement entre les types ti et tj
                if(i == j) M[ti][tj] = 1000000; //Mettre l'infini dans la diagonale
            }
            M[ti][last] = (_problem->getDistance(i , 0) * 100);//la distance vers le dépot
            M[ti][abs] = 0;
        }


"""

from pycsp3 import *
from pycsp3_scheduling import *
from pycsp3_scheduling.variables.interval import clear_interval_registry


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
    (30, 70, 4, 6),    # Customer 4
    (25, 60, 7, 3),    # Customer 5
    (40, 80, 5, 4),    # Customer 6
]

# Travel times matrix (symmetric)
# travel[i][j] = time to go from i to j
travel = [
    [0, 10, 15, 12, 20, 18, 25],  # From depot
    [10, 0, 8, 10, 15, 12, 20],   # From customer 1
    [15, 8, 0, 6, 10, 8, 15],     # From customer 2
    [12, 10, 6, 0, 12, 10, 18],   # From customer 3
    [20, 15, 10, 12, 0, 6, 10],   # From customer 4
    [18, 12, 8, 10, 6, 0, 8],     # From customer 5
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

# Create visit intervals for each (vehicle, customer) pair
# visits[v][c] = interval for vehicle v visiting customer c
visits = []
for v in range(n_vehicles):
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
# The sequence determines the order of visits
routes = []
for v in range(n_vehicles):
    # Customer types for transition matrix (0-indexed: 0 to n_customers-1)
    types = list(range(n_customers))  # Types 0..n_customers-1
    route = SequenceVar(
        intervals=visits[v],
        types=types,
        name=f"route_{v}"
    )
    routes.append(route)

print(f"Created {n_vehicles} route sequences")

# Build transition matrix for travel times between customers
# transition[i][j] = travel time from customer (i+1) to customer (j+1)
# Types are 0-indexed (0 to n_customers-1), mapping to customers 1 to n_customers
transition_matrix = []
for i in range(n_customers):
    row = []
    for j in range(n_customers):
        # i maps to customer i+1, j maps to customer j+1
        row.append(travel[i+1][j+1])
    transition_matrix.append(row)

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


minimize(Sum(
    end_time(main_visits[c]) for c in range(n_customers)
))

# Solve
result = solve()

if result in (SAT, OPTIMUM):
    print("Solution found!" + (" (Optimal)" if result == OPTIMUM else ""))
    print()
    
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
            
            # Calculate route distance
            route_distance = 0
            prev = 0  # Start from depot
            for _, cust_id, _ in route_visits:
                route_distance += travel[prev][cust_id]
                prev = cust_id
            route_distance += travel[prev][0]  # Return to depot
            total_distance += route_distance
            
            print(f"Vehicle {v}: 0 -> {route_str} -> 0  (demand: {route_demand}/{vehicle_capacity}, dist: {route_distance})")
        else:
            print(f"Vehicle {v}: unused")
    
    print(f"\nTotal travel distance: {total_distance}")
else:
    print("No solution found")
