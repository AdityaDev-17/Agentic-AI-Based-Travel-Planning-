"""Adds synthetic flights for routes missing from flights.json.
Writes data/flights_extended.json (originals + generated). State this in the README."""

import json
import random
from datetime import datetime, timedelta
from itertools import permutations

from config import SUPPORTED_CITIES, settings
from data_loader import DataLoader


class FlightGenerator:
    """Generates reproducible fake flights for uncovered routes."""

    AIRLINES = ["IndiGo", "Air India", "SpiceJet", "Vistara", "Akasa Air"]

    def __init__(self, seed: int = 42, per_route: int = 3):
        self.rng = random.Random(seed)
        self.per_route = per_route

    def generate(self) -> list:
        original = DataLoader(settings.data_dir).load("flights.json")
        covered = {(f["from"], f["to"]) for f in original}
        generated = []
        for origin, destination in permutations(SUPPORTED_CITIES, 2):
            if (origin, destination) in covered:
                continue
            for _ in range(self.per_route):
                generated.append(self._make_flight(len(generated) + 1, origin, destination))
        return original + generated

    def _make_flight(self, number: int, origin: str, destination: str) -> dict:
        departure = datetime(2025, 1, 1) + timedelta(
            days=self.rng.randint(0, 364),
            hours=self.rng.randint(5, 22),
            minutes=self.rng.choice([0, 15, 30, 45]),
        )
        arrival = departure + timedelta(minutes=self.rng.randint(90, 240))
        return {
            "flight_id": f"FLX{number:04d}",
            "airline": self.rng.choice(self.AIRLINES),
            "from": origin,
            "to": destination,
            "departure_time": departure.strftime("%Y-%m-%dT%H:%M:%S"),
            "arrival_time": arrival.strftime("%Y-%m-%dT%H:%M:%S"),
            "price": self.rng.randrange(2500, 9000, 50),
        }


if __name__ == "__main__":
    flights = FlightGenerator().generate()
    output = settings.data_dir / "flights_extended.json"
    with open(output, "w", encoding="utf-8") as file:
        json.dump(flights, file, indent=2)
    print(f"Wrote {len(flights)} flights to {output}")