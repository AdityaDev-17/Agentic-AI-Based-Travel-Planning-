"""Deterministic budget maths. The LLM must never do this arithmetic."""

import math

from config import settings


class BudgetEstimator:
    """Sums flights, hotel and local expenses with explicit, documented assumptions."""

    PEOPLE_PER_ROOM = 2

    def __init__(self, daily_local_expense=None):
        self.daily_local_expense = daily_local_expense or settings.default_daily_expense

    def estimate(self, flight_prices, hotel_price_per_night, nights, travelers=1) -> dict:
        """flight_prices are per person, one entry per leg."""
        nights = max(int(nights), 0)
        travelers = max(int(travelers), 1)
        rooms = math.ceil(travelers / self.PEOPLE_PER_ROOM)

        flights_total = sum(flight_prices) * travelers
        hotel_total = hotel_price_per_night * nights * rooms
        local_total = self.daily_local_expense * (nights + 1) * travelers
        return {
            "flights": flights_total,
            "hotel": hotel_total,
            "food_and_local_travel": local_total,
            "total": flights_total + hotel_total + local_total,
            "assumptions": (
                f"{travelers} traveler(s), {rooms} room(s) at {self.PEOPLE_PER_ROOM} per room, "
                f"{nights} night(s), Rs {self.daily_local_expense}/person/day for food and local travel."
            ),
        }