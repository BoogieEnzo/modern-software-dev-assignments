from __future__ import annotations

import os
import sys

# Add parent directory to path for imports when running directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Annotated

from mcp.server.fastmcp import FastMCP

from server.logging_config import configure_logging
from server.openweather_client import OpenWeatherClient
from server.errors import (
    CityNotFoundError,
    MissingApiKeyError,
    OpenWeatherError,
    RateLimitError,
)
from server.models import CurrentWeather, WeatherForecast


configure_logging()

mcp = FastMCP("OpenWeather MCP Server")
client = OpenWeatherClient()


@mcp.tool()
def get_current_weather(
    city: Annotated[str, "City name, e.g. 'Beijing' or 'San Francisco'"],
    country_code: Annotated[
        str | None,
        "Optional ISO 3166-1 alpha-2 country code, e.g. 'CN', 'US'.",
    ] = None,
    units: Annotated[
        str,
        "Units for temperature/wind: 'standard', 'metric', or 'imperial'.",
    ] = "metric",
) -> dict:
    """
    Get the current weather for a city using OpenWeather.

    Returns a structured JSON object with temperature, humidity, wind speed,
    description, and observation time.
    """
    try:
        lat, lon, display_name = client.geocode_city(city=city, country_code=country_code)
        raw = client.fetch_current_weather(lat=lat, lon=lon, units=units)
        model = CurrentWeather.from_openweather(raw, city_name=display_name)
        return {
            "city": model.city,
            "temperature": model.temperature,
            "feels_like": model.feels_like,
            "humidity": model.humidity,
            "wind_speed": model.wind_speed,
            "description": model.description,
            "observed_at": model.observed_at,
        }
    except MissingApiKeyError as exc:
        raise OpenWeatherError(
            "OPENWEATHER_API_KEY is not configured. Please set it before using this tool."
        ) from exc
    except CityNotFoundError as exc:
        raise OpenWeatherError(str(exc)) from exc
    except RateLimitError as exc:
        raise OpenWeatherError(
            "OpenWeather rate limit exceeded. Please wait a bit before trying again."
        ) from exc


@mcp.tool()
def get_weather_forecast(
    city: Annotated[str, "City name, e.g. 'Beijing' or 'San Francisco'"],
    country_code: Annotated[
        str | None,
        "Optional ISO 3166-1 alpha-2 country code, e.g. 'CN', 'US'.",
    ] = None,
    units: Annotated[
        str,
        "Units for temperature/wind: 'standard', 'metric', or 'imperial'.",
    ] = "metric",
    hours: Annotated[
        int,
        "How many hours of forecast you need (approximate, multiple of 3).",
    ] = 12,
) -> dict:
    """
    Get a short-term weather forecast for a city using OpenWeather.

    Returns a list of forecast entries with time, temperature, description,
    and probability of precipitation.
    """
    if hours <= 0:
        hours = 12
    if hours > 120:
        hours = 120

    try:
        lat, lon, display_name = client.geocode_city(city=city, country_code=country_code)
        raw = client.fetch_forecast(lat=lat, lon=lon, units=units, hours=hours)
        model = WeatherForecast.from_openweather(raw, city_name=display_name)
        return {
            "city": model.city,
            "entries": [
                {
                    "time": e.time,
                    "temperature": e.temperature,
                    "description": e.description,
                    "probability_of_precipitation": e.probability_of_precipitation,
                }
                for e in model.entries
            ],
        }
    except MissingApiKeyError as exc:
        raise OpenWeatherError(
            "OPENWEATHER_API_KEY is not configured. Please set it before using this tool."
        ) from exc
    except CityNotFoundError as exc:
        raise OpenWeatherError(str(exc)) from exc
    except RateLimitError as exc:
        raise OpenWeatherError(
            "OpenWeather rate limit exceeded. Please wait a bit before trying again."
        ) from exc


if __name__ == "__main__":
    mcp.run()
