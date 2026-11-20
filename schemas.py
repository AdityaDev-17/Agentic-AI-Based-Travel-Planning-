"""Pydantic models describing the final itinerary."""

from pydantic import BaseModel, Field


class FlightInfo(BaseModel):
    leg: str = Field(description="'outbound' or 'return'")
    flight_id: str = Field(description="flight_id exactly as returned by search_flights")
    airline: str
    origin: str
    destination: str
    departs: str = Field(description="Departure time, HH:MM")
    arrives: str = Field(description="Arrival time, HH:MM")
    price_per_person: float


class HotelInfo(BaseModel):
    hotel_id: str = Field(description="hotel_id exactly as returned by search_hotels")
    name: str
    stars: int
    price_per_night: float
    amenities: list[str]


class DayPlan(BaseModel):
    day: int
    date: str = Field(description="YYYY-MM-DD")
    weather: str = Field(description="From get_weather, or 'Forecast unavailable'")
    activities: list[str] = Field(description="Each as 'Name (type, rating)'")


class BudgetBreakdown(BaseModel):
    flights: float
    hotel: float
    food_and_local_travel: float
    total: float
    assumptions: str


class Itinerary(BaseModel):
    title: str = Field(description="e.g. 'Your 3-Day Trip to Goa (Nov 25-27)'")
    summary: str
    travelers: int
    flights: list[FlightInfo]
    hotel: HotelInfo | None = Field(description="null if no hotel could be found")
    days: list[DayPlan]
    budget: BudgetBreakdown
    budget_note: str = Field(description="Within/over the user's budget, or 'No budget given'")
    reasoning: list[str] = Field(description="3-5 bullets: why we selected this")
    warnings: list[str] = Field(description="Missing routes, unavailable weather, thin data; [] if none")