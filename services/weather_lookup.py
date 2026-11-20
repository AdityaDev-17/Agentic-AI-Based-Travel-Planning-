"""Weather lookup service backed by the free Open-Meteo API."""

from datetime import date, timedelta

import requests

from config import CITY_COORDINATES, settings


class WeatherLookup:
    """Fetches daily forecasts. Never raises; failures come back as available=False."""

    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT_SECONDS = 10

    WMO_CODES = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Fog",
        51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
        61: "Light rain", 63: "Rain", 65: "Heavy rain",
        80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
    }

    def _coordinates(self, city: str) -> tuple:
        """Known dataset cities use fixed coordinates; others fall back to name lookup."""
        known = CITY_COORDINATES.get(city.strip().lower())
        if known:
            return known
        response = requests.get(
            self.GEOCODE_URL,
            params={"name": city, "count": 1, "countryCode": "IN"},
            timeout=self.TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json().get("results")
        if not results:
            raise ValueError(f"City not found: {city}")
        return results[0]["latitude"], results[0]["longitude"]

    def get_forecast(self, city: str, start_date: date, end_date: date) -> dict:
        """Return daily weather for the date range, clipped to the forecast window."""
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        today = date.today()
        last_available = today + timedelta(days=settings.max_forecast_days - 1)
        if start_date < today or start_date > last_available:
            return {
                "available": False,
                "city": city,
                "message": (
                    f"Forecast only covers {today} to {last_available}; "
                    f"requested start {start_date} is outside it."
                ),
            }

        end_used = min(end_date, last_available)
        try:
            latitude, longitude = self._coordinates(city)
            response = requests.get(
                self.FORECAST_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                             "precipitation_probability_max",
                    "start_date": start_date.isoformat(),
                    "end_date": end_used.isoformat(),
                    "timezone": "auto",
                },
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            daily = response.json()["daily"]
        except (requests.RequestException, ValueError, KeyError) as error:
            return {"available": False, "city": city, "message": f"Weather lookup failed: {error}"}

        days = []
        for index, day in enumerate(daily["time"]):
            code = daily["weather_code"][index]
            days.append({
                "date": day,
                "summary": self.WMO_CODES.get(code, f"Weather code {code}"),
                "temp_max_c": daily["temperature_2m_max"][index],
                "temp_min_c": daily["temperature_2m_min"][index],
                "rain_chance_pct": daily["precipitation_probability_max"][index],
            })

        note = ""
        if end_used < end_date:
            note = f"Forecast available only up to {end_used}; later days not covered."
        return {"available": True, "city": city, "days": days, "note": note}