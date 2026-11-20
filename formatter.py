"""Renders an Itinerary as readable Markdown (works in the terminal and Streamlit)."""

from schemas import Itinerary


class ItineraryFormatter:
    """Turns the structured itinerary into human-readable text."""

    @staticmethod
    def _money(value: float) -> str:
        return f"₹{value:,.0f}"

    @classmethod
    def render(cls, itinerary: Itinerary) -> str:
        lines = [f"# {itinerary.title}", "", itinerary.summary, "", "## Flights"]
        if itinerary.flights:
            for flight in itinerary.flights:
                lines.append(
                    f"- **{flight.leg.title()}:** {flight.airline}, {flight.origin} → "
                    f"{flight.destination}, departs {flight.departs}, arrives {flight.arrives} "
                    f"({cls._money(flight.price_per_person)} per person)"
                )
        else:
            lines.append("- No flights found")

        lines += ["", "## Hotel"]
        hotel = itinerary.hotel
        if hotel:
            lines.append(
                f"- {hotel.name} ({hotel.stars}-star, {cls._money(hotel.price_per_night)}/night) "
                f"- {', '.join(hotel.amenities)}"
            )
        else:
            lines.append("- No hotel found")

        lines += ["", "## Day-wise Itinerary"]
        for day in itinerary.days:
            lines.append(f"### Day {day.day} ({day.date})")
            lines.append(f"- Weather: {day.weather}")
            lines += [f"- {activity}" for activity in day.activities]

        budget = itinerary.budget
        lines += [
            "", "## Estimated Budget",
            f"- Flights: {cls._money(budget.flights)}",
            f"- Hotel: {cls._money(budget.hotel)}",
            f"- Food & local travel: {cls._money(budget.food_and_local_travel)}",
            f"- **Total: {cls._money(budget.total)}**",
            f"- Assumptions: {budget.assumptions}",
            f"- {itinerary.budget_note}",
            "", "## Why we selected this",
        ]
        lines += [f"- {reason}" for reason in itinerary.reasoning]

        if itinerary.warnings:
            lines += ["", "## Warnings"]
            lines += [f"- {warning}" for warning in itinerary.warnings]
        return "\n".join(lines)