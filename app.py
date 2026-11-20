"""Streamlit UI for the travel planning agent."""

from datetime import date, timedelta

import streamlit as st

from agent import TravelAgent
from config import PLACE_TYPES, SUPPORTED_CITIES
from formatter import ItineraryFormatter


@st.cache_resource
def load_agent() -> TravelAgent:
    """Build the agent once per Streamlit server process."""
    return TravelAgent()


class TravelPlannerApp:
    """Form, agent call, and result rendering."""

    def __init__(self):
        st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="centered")

    @staticmethod
    def render_form() -> tuple:
        """Draw the input form and return (submitted, params)."""
        with st.form("trip_form"):
            left, right = st.columns(2)
            origin = left.selectbox("From", SUPPORTED_CITIES, index=SUPPORTED_CITIES.index("Delhi"))
            destination = right.selectbox("To", SUPPORTED_CITIES, index=SUPPORTED_CITIES.index("Goa"))
            start_date = left.date_input(
                "Start date", value=date.today() + timedelta(days=3), min_value=date.today()
            )
            days = right.number_input("Trip length (days)", min_value=3, max_value=7, value=3)
            travelers = left.number_input("Travelers", min_value=1, max_value=8, value=1)
            budget = right.number_input(
                "Total budget (₹, 0 = no limit)", min_value=0, max_value=1_000_000, value=0, step=1000
            )
            interests = st.multiselect("Interests", PLACE_TYPES)
            preference = st.radio("Flight preference", ["cheapest", "fastest"], horizontal=True)
            submitted = st.form_submit_button("Plan my trip")
        params = {
            "origin": origin, "destination": destination, "start_date": start_date,
            "days": int(days), "travelers": int(travelers), "budget": int(budget),
            "interests": interests, "preference": preference,
        }
        return submitted, params

    @staticmethod
    def build_query(params: dict) -> str:
        """Turn form values into the natural-language request the agent receives."""
        parts = [
            f"Plan a {params['days']}-day trip ({params['days'] - 1} nights) from "
            f"{params['origin']} to {params['destination']} starting {params['start_date'].isoformat()} "
            f"for {params['travelers']} traveler(s).",
            f"Budget: {params['budget']} INR total." if params["budget"] else "No budget limit.",
            f"Interests: {', '.join(params['interests'])}." if params["interests"] else "",
            f"Prefer the {params['preference']} flights.",
        ]
        return " ".join(part for part in parts if part)

    @staticmethod
    def render_result(itinerary, trace: list) -> None:
        """Show the itinerary, raw JSON, and the agent's tool calls in tabs."""
        text_tab, json_tab, trace_tab = st.tabs(["Itinerary", "JSON", "Agent trace"])
        with text_tab:
            st.markdown(ItineraryFormatter.render(itinerary))
        with json_tab:
            st.json(itinerary.model_dump())
        with trace_tab:
            st.code("\n".join(trace) or "No tool calls recorded.")

    def run(self) -> None:
        st.title("✈️ AI Travel Planner")
        st.caption("Agentic planner: flights, hotels, places, weather and budget.")

        submitted, params = self.render_form()
        if submitted:
            if params["origin"] == params["destination"]:
                st.error("Origin and destination must be different.")
            else:
                try:
                    with st.spinner("The agent is planning your trip..."):
                        agent = load_agent()
                        itinerary = agent.plan_trip(self.build_query(params))
                        st.session_state["result"] = (itinerary, agent.last_trace)
                except Exception as error:  # surface any API/agent failure in the UI
                    st.error(f"Planning failed: {error}")

        if "result" in st.session_state:
            self.render_result(*st.session_state["result"])


TravelPlannerApp().run()