"""LangChain tool wrappers. The descriptions and Field text are what the LLM reads."""

import json
from datetime import date

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from config import PLACE_TYPES, SUPPORTED_CITIES, settings
from data_loader import DataLoader
from services.budget_estimator import BudgetEstimator
from services.flight_search import FlightSearch
from services.hotel_search import HotelSearch
from services.places_search import PlacesSearch
from services.weather_lookup import WeatherLookup

CITY_LIST = ", ".join(SUPPORTED_CITIES)


class FlightArgs(BaseModel):
    origin: str = Field(description=f"Departure city, one of: {CITY_LIST}")
    destination: str = Field(description=f"Arrival city, one of: {CITY_LIST}")
    sort_by: str = Field(default="cheapest", description="'cheapest' or 'fastest'")


class HotelArgs(BaseModel):
    city: str = Field(description=f"City, one of: {CITY_LIST}")
    min_stars: int = Field(default=0, description="Minimum star rating, 0-5")
    max_price_per_night: float | None = Field(default=None, description="Max price per night in INR")
    sort_by: str = Field(default="rating", description="'rating' (highest stars) or 'cheapest'")


class PlacesArgs(BaseModel):
    city: str = Field(description=f"City, one of: {CITY_LIST}")
    place_types: list[str] | None = Field(
        default=None, description=f"Attraction types to include, from: {', '.join(PLACE_TYPES)}"
    )
    min_rating: float = Field(default=0.0, description="Minimum rating, 0-5")
    limit: int = Field(default=6, description="Maximum places to return")


class WeatherArgs(BaseModel):
    city: str = Field(description=f"City, one of: {CITY_LIST}")
    start_date: str = Field(description="First trip day, format YYYY-MM-DD")
    end_date: str = Field(description="Last trip day, format YYYY-MM-DD")


class BudgetArgs(BaseModel):
    flight_prices: list[float] = Field(description="Price per person of each selected flight leg")
    hotel_price_per_night: float = Field(description="Selected hotel price per night in INR")
    nights: int = Field(description="Number of nights (trip days minus 1)")
    travelers: int = Field(default=1, description="Number of travelers")


class TravelToolkit:
    """Builds the service objects and exposes them as LangChain tools."""

    def __init__(self, loader: DataLoader):
        self.flights = FlightSearch(loader, settings.flights_file)
        self.hotels = HotelSearch(loader)
        self.places = PlacesSearch(loader)
        self.weather = WeatherLookup()
        self.budget = BudgetEstimator()

    @staticmethod
    def _dump(result: dict) -> str:
        return json.dumps(result, ensure_ascii=False)

    def _search_flights(self, origin: str, destination: str, sort_by: str = "cheapest") -> str:
        return self._dump(self.flights.search(origin, destination, sort_by))

    def _search_hotels(self, city: str, min_stars: int = 0, max_price_per_night=None,
                       sort_by: str = "rating") -> str:
        return self._dump(self.hotels.search(city, min_stars, max_price_per_night, sort_by))

    def _search_places(self, city: str, place_types=None, min_rating: float = 0.0,
                       limit: int = 6) -> str:
        return self._dump(self.places.search(city, place_types, min_rating, limit))

    def _get_weather(self, city: str, start_date: str, end_date: str) -> str:
        try:
            start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        except ValueError:
            return self._dump({"available": False, "message": "Dates must be YYYY-MM-DD."})
        return self._dump(self.weather.get_forecast(city, start, end))

    def _estimate_budget(self, flight_prices: list, hotel_price_per_night: float,
                         nights: int, travelers: int = 1) -> str:
        return self._dump(
            self.budget.estimate(flight_prices, hotel_price_per_night, nights, travelers)
        )

    def get_tools(self) -> list:
        """Return all five tools for the agent."""
        return [
            StructuredTool.from_function(
                func=self._search_flights, name="search_flights", args_schema=FlightArgs,
                description=(
                    "Find flights between two cities in the flight dataset. Returns JSON with the "
                    "selected flight and options. If found is false, no flight exists on that "
                    "route; tell the user and never invent a flight."
                ),
            ),
            StructuredTool.from_function(
                func=self._search_hotels, name="search_hotels", args_schema=HotelArgs,
                description=(
                    "Find hotels in a city, filtered by minimum stars and maximum nightly price. "
                    "If found is false, relax the filters and try again."
                ),
            ),
            StructuredTool.from_function(
                func=self._search_places, name="search_places", args_schema=PlacesArgs,
                description=(
                    "Find top-rated attractions in a city, optionally filtered by type. "
                    "The result lists available_types and a note if the filter was relaxed."
                ),
            ),
            StructuredTool.from_function(
                func=self._get_weather, name="get_weather", args_schema=WeatherArgs,
                description=(
                    "Get the daily weather forecast for a city and date range. Only about the "
                    "next 16 days are available; if available is false, say the forecast is "
                    "unavailable and never guess the weather."
                ),
            ),
            StructuredTool.from_function(
                func=self._estimate_budget, name="estimate_budget", args_schema=BudgetArgs,
                description=(
                    "Compute the trip budget from selected flights, hotel, nights and travelers. "
                    "Always use this tool for money totals; never do the arithmetic yourself."
                ),
            ),
        ]