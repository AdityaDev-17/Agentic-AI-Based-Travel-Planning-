"""Places (attractions) search service over the places dataset."""

from data_loader import DataLoader
from services.utils import same_text


class PlacesSearch:
    """Searches attractions by city, type and rating. Names in the dataset are
    synthetic, so type and rating are what matter."""

    def __init__(self, loader: DataLoader):
        self.places = loader.load("places.json")

    def search(self, city: str, place_types=None, min_rating: float = 0.0, limit: int = 6) -> dict:
        """Return the top-rated places, falling back to any type if the filter matches nothing."""
        in_city = [p for p in self.places if same_text(p["city"], city)]
        if not in_city:
            return {"found": False, "city": city, "message": f"No places listed for {city}."}

        available_types = sorted({p["type"] for p in in_city})
        wanted = {t.strip().lower() for t in place_types} if place_types else None

        matches = [
            p for p in in_city
            if p["rating"] >= min_rating and (wanted is None or p["type"].lower() in wanted)
        ]

        note = ""
        if not matches and wanted is not None:
            matches = [p for p in in_city if p["rating"] >= min_rating]
            note = (
                f"No {sorted(wanted)} places in {city}; showing top-rated places of any type instead."
            )
        if not matches:
            return {
                "found": False,
                "city": city,
                "message": "No places match the filters.",
                "available_types": available_types,
            }

        matches.sort(key=lambda p: -p["rating"])
        places = [
            {"place_id": p["place_id"], "name": p["name"], "type": p["type"], "rating": p["rating"]}
            for p in matches[:limit]
        ]
        return {
            "found": True,
            "city": city,
            "places": places,
            "available_types": available_types,
            "note": note,
            "selection_reason": f"Top {len(places)} by rating out of {len(matches)} matching place(s).",
        }