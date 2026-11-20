"""Flight search service over the flights dataset."""

from datetime import datetime

from data_loader import DataLoader
from services.utils import same_text


class FlightSearch:
    """Searches flights by route. Dataset dates are historic, so only route, price
    and time-of-day are used."""

    VALID_SORTS = ("cheapest", "fastest")

    def __init__(self, loader: DataLoader, filename: str = "flights.json"):
        self.flights = loader.load(filename)

    def search(self, origin: str, destination: str, sort_by: str = "cheapest") -> dict:
        """Return the best flight plus up to 3 options, or found=False with alternatives."""
        if sort_by not in self.VALID_SORTS:
            sort_by = "cheapest"

        matches = [
            f for f in self.flights
            if same_text(f["from"], origin) and same_text(f["to"], destination)
        ]
        if not matches:
            reachable = sorted({f["to"] for f in self.flights if same_text(f["from"], origin)})
            return {
                "found": False,
                "origin": origin,
                "destination": destination,
                "message": f"No flight found from {origin} to {destination}.",
                "destinations_from_origin": reachable,
            }

        options = [self._to_option(f) for f in matches]
        if sort_by == "cheapest":
            options.sort(key=lambda o: (o["price"], o["duration_minutes"]))
        else:
            options.sort(key=lambda o: (o["duration_minutes"], o["price"]))

        return {
            "found": True,
            "selected": options[0],
            "options": options[:3],
            "selection_reason": f"Chosen as the {sort_by} of {len(options)} flight(s) on this route.",
        }

    @staticmethod
    def _to_option(flight: dict) -> dict:
        departure = datetime.fromisoformat(flight["departure_time"])
        arrival = datetime.fromisoformat(flight["arrival_time"])
        return {
            "flight_id": flight["flight_id"],
            "airline": flight["airline"],
            "from": flight["from"],
            "to": flight["to"],
            "departs": departure.strftime("%H:%M"),
            "arrives": arrival.strftime("%H:%M"),
            "duration_minutes": int((arrival - departure).total_seconds() // 60),
            "price": flight["price"],
        }