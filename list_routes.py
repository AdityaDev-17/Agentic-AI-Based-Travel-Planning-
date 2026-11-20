from collections import defaultdict

from data_loader import DataLoader

flights = DataLoader().load("flights.json")
routes = defaultdict(list)
for flight in flights:
    routes[(flight["from"], flight["to"])].append(flight["price"])

print(f"{len(routes)} distinct routes out of 56 possible\n")
for (origin, destination), prices in sorted(routes.items()):
    print(f"{origin:10} -> {destination:10} {len(prices)} flight(s), prices {sorted(prices)}")

round_trips = [(a, b) for (a, b) in routes if (b, a) in routes and a < b]
print("\nCities with flights both ways:", round_trips)

