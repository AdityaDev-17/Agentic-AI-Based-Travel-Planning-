"""Hotel search service over the hotels dataset."""

from data_loader import DataLoader
from services.utils import same_text


class HotelSearch:
    """Searches hotels by city, minimum stars and maximum nightly price.
    The dataset has no guest ratings, so 'rating' means star rating."""

    VALID_SORTS = ("rating", "cheapest")

    def __init__(self, loader: DataLoader):
        self.hotels = loader.load("hotels.json")

    def search(self, city: str, min_stars: int = 0, max_price_per_night=None,
               sort_by: str = "rating") -> dict:
        """Return the best hotel plus up to 3 options."""
        if sort_by not in self.VALID_SORTS:
            sort_by = "rating"

        in_city = [h for h in self.hotels if same_text(h["city"], city)]
        if not in_city:
            return {"found": False, "city": city, "message": f"No hotels listed for {city}."}

        matches = [
            h for h in in_city
            if h["stars"] >= min_stars
            and (max_price_per_night is None or h["price_per_night"] <= max_price_per_night)
        ]
        if not matches:
            return {
                "found": False,
                "city": city,
                "message": "No hotel matches the filters. Relax min_stars or max_price_per_night.",
                "cheapest_price_in_city": min(h["price_per_night"] for h in in_city),
                "max_stars_in_city": max(h["stars"] for h in in_city),
            }

        if sort_by == "cheapest":
            matches.sort(key=lambda h: (h["price_per_night"], -h["stars"]))
        else:
            matches.sort(key=lambda h: (-h["stars"], h["price_per_night"]))

        options = [
            {
                "hotel_id": h["hotel_id"],
                "name": h["name"],
                "stars": h["stars"],
                "price_per_night": h["price_per_night"],
                "amenities": h["amenities"],
            }
            for h in matches
        ]
        return {
            "found": True,
            "selected": options[0],
            "options": options[:3],
            "selection_reason": (
                f"Chosen as the {sort_by} option of {len(options)} matching hotel(s) in {city}."
            ),
        }