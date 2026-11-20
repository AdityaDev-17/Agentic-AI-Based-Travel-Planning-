"""Central configuration: paths, environment settings, and shared constants."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

SUPPORTED_CITIES = [
    "Bangalore", "Chennai", "Delhi", "Goa", "Hyderabad", "Jaipur", "Kolkata", "Mumbai",
]
PLACE_TYPES = ["beach", "fort", "lake", "market", "monument", "museum", "park", "temple"]

CITY_COORDINATES = {
    "goa": (15.2993, 74.1240),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "kolkata": (22.5726, 88.3639),
    "jaipur": (26.9124, 75.7873),
}


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secrets and model name come from .env."""

    data_dir: Path = BASE_DIR / "data"
    max_agent_steps: int = 30
    default_daily_expense: int = 1000  # INR per person per day (assumption, tune freely)
    max_forecast_days: int = 16

    @property
    def model_name(self) -> str:
        return os.getenv("OPENAI_MODEL", "")

    @property
    def flights_file(self) -> str:
        """Use the extended flight file if generate_flights.py has been run."""
        extended = self.data_dir / "flights_extended.json"
        return "flights_extended.json" if extended.exists() else "flights.json"

    def validate(self) -> None:
        """Fail early with a clear message if .env is incomplete."""
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is missing. Check your .env file.")
        if not self.model_name:
            raise RuntimeError("OPENAI_MODEL is missing. Add it to your .env file.")


settings = Settings()