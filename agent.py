"""Travel planning agent: builds the LLM, binds tools, runs the loop, grounds the output."""

import json
import sys
from datetime import date, timedelta

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from config import settings
from data_loader import DataLoader
from formatter import ItineraryFormatter
from schemas import BudgetBreakdown, Itinerary
from services.budget_estimator import BudgetEstimator
from tools import TravelToolkit

SYSTEM_PROMPT = """You are a travel planning agent for trips between Indian cities. Today's date is {today}.

Rules:
1. Never invent flights, hotels, places, prices or weather. Use only data returned by your tools, and copy flight_id and hotel_id exactly.
2. Use search_flights for an outbound flight (origin to destination) and a return flight (destination to origin). Honour the user's cheapest/fastest preference. If a leg has no flights, leave it out and add a warning.
3. Use search_hotels for the destination. If the user gave a budget, pass a sensible max_price_per_night and relax it if nothing matches.
4. Use get_weather for the destination for the trip dates (YYYY-MM-DD). If it is unavailable, write 'Forecast unavailable' for those days and add a warning.
5. Use search_places for the destination, with the user's interests as place_types. Plan trip_days = nights + 1 days, 2-3 activities per day, no repeated places unless the data has too few (then add a warning). Write each activity as 'Name (type, rating)'.
6. Use estimate_budget with the selected flight prices, hotel price per night, nights and travelers. Copy its numbers into the budget. Never do arithmetic yourself.
7. If the total exceeds the user's budget, try a cheaper flight or hotel once before finalising. If it is still over, say so in budget_note.
8. Give 3-5 reasoning bullets explaining why you chose the flights, hotel and places.
"""


class TravelAgent:
    """Wraps the LangChain agent and verifies its output against the datasets."""

    def __init__(self):
        settings.validate()
        self.loader = DataLoader(settings.data_dir)
        self.toolkit = TravelToolkit(self.loader)
        self.budget = BudgetEstimator()
        self.last_trace = []
        self.llm = ChatOpenAI(model=settings.model_name)
        self.agent = create_agent(
            model=self.llm,
            tools=self.toolkit.get_tools(),
            system_prompt=SYSTEM_PROMPT.format(today=date.today().isoformat()),
            response_format=Itinerary,
        )

    def plan_trip(self, query: str) -> Itinerary:
        """Run the agent on a natural-language request and return a verified itinerary."""
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": query}]},
            config={"recursion_limit": settings.max_agent_steps},
        )
        self.last_trace = self._extract_trace(result["messages"])
        itinerary = result.get("structured_response")
        if itinerary is None:
            raise RuntimeError("The agent finished without a structured itinerary. Try again.")
        return self._ground(itinerary)

    @staticmethod
    def _extract_trace(messages) -> list:
        """List every tool call the agent made, in order."""
        trace = []
        for message in messages:
            for call in getattr(message, "tool_calls", None) or []:
                trace.append(f"{call['name']}({json.dumps(call['args'], ensure_ascii=False)})")
        return trace

    def _ground(self, itinerary: Itinerary) -> Itinerary:
        """Overwrite flight/hotel details from the datasets and recompute the budget in code."""
        warnings = list(itinerary.warnings)
        flights_by_id = {f["flight_id"]: f for f in self.loader.load(settings.flights_file)}
        hotels_by_id = {h["hotel_id"]: h for h in self.loader.load("hotels.json")}

        for flight in itinerary.flights:
            record = flights_by_id.get(flight.flight_id)
            if record is None:
                warnings.append(f"Flight {flight.flight_id} is not in the dataset; details unverified.")
                continue
            flight.airline = record["airline"]
            flight.origin = record["from"]
            flight.destination = record["to"]
            flight.departs = record["departure_time"][11:16]
            flight.arrives = record["arrival_time"][11:16]
            flight.price_per_person = record["price"]

        hotel = itinerary.hotel
        if hotel:
            record = hotels_by_id.get(hotel.hotel_id)
            if record is None:
                warnings.append(f"Hotel {hotel.hotel_id} is not in the dataset; details unverified.")
            else:
                hotel.name = record["name"]
                hotel.stars = record["stars"]
                hotel.price_per_night = record["price_per_night"]
                hotel.amenities = record["amenities"]

        nights = max(len(itinerary.days) - 1, 0)
        estimate = self.budget.estimate(
            [f.price_per_person for f in itinerary.flights],
            hotel.price_per_night if hotel else 0,
            nights,
            itinerary.travelers,
        )
        itinerary.budget = BudgetBreakdown(**estimate)
        itinerary.warnings = warnings
        return itinerary


if __name__ == "__main__":
    start = date.today() + timedelta(days=5)
    default_query = (
        f"Plan a 3-day trip from Delhi to Goa starting {start.isoformat()} for 2 travelers. "
        "Budget 40000 INR total. We like forts and markets. Prefer the cheapest flights."
    )
    query = " ".join(sys.argv[1:]) or default_query
    print("Query:", query, "\n")

    travel_agent = TravelAgent()
    plan = travel_agent.plan_trip(query)
    print(ItineraryFormatter.render(plan))
    print("\n--- Tool calls ---")
    print("\n".join(travel_agent.last_trace))
    print("\n--- JSON ---")
    print(plan.model_dump_json(indent=2))