from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import httpx

from .config import settings
from .errors import (
    CityNotFoundError,
    MissingApiKeyError,
    RateLimitError,
    UpstreamServiceError,
)


class OpenWeatherClient:
    """Thin wrapper around the OpenWeather HTTP API."""

    def __init__(self) -> None:
        self._base_url = settings.base_url
        self._api_key = settings.api_key
        self._timeout = settings.request_timeout_seconds

    def _require_api_key(self) -> None:
        if not self._api_key:
            raise MissingApiKeyError(
                "OPENWEATHER_API_KEY is not set. Please configure it before calling this tool."
            )

    def _build_client(self) -> httpx.Client:
        # Disable proxies to avoid SOCKS issues
        return httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            proxy=None
        )
        # Disable proxies to avoid SOCKS issues
        return httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            proxies={"http://": None, "https://": None}
        )
    def geocode_city(self, city: str, country_code: Optional[str] = None) -> Tuple[float, float, str]:
        """Resolve a city name (and optional country code) to (lat, lon, display_name)."""
        self._require_api_key()

        query = city.strip()
        if country_code:
            query = f"{query},{country_code.strip()}"

        params = {
            "q": query,
            "limit": 5,
            "appid": self._api_key,
        }

        with self._build_client() as client:
            resp = client.get("/geo/1.0/direct", params=params)

        if resp.status_code == 429:
            raise RateLimitError("OpenWeather rate limit exceeded while resolving city.")
        if resp.status_code >= 500:
            raise UpstreamServiceError(
                f"OpenWeather geocoding service error (status {resp.status_code})."
            )
        resp.raise_for_status()

        data: List[Dict[str, Any]] = resp.json()
        if not data:
            raise CityNotFoundError(f"Could not resolve city '{city}'. Try including a country code.")

        first = data[0]
        lat = float(first["lat"])
        lon = float(first["lon"])
        name_parts = [first.get("name")]
        if first.get("state"):
            name_parts.append(first["state"])
        if first.get("country"):
            name_parts.append(first["country"])
        display_name = ", ".join([p for p in name_parts if p])
        return lat, lon, display_name

    def fetch_current_weather(
        self,
        lat: float,
        lon: float,
        units: str = "metric",
    ) -> Dict[str, Any]:
        """Fetch current weather for given coordinates."""
        self._require_api_key()

        params = {
            "lat": lat,
            "lon": lon,
            "units": units,
            "appid": self._api_key,
        }

        with self._build_client() as client:
            resp = client.get("/data/2.5/weather", params=params)

        if resp.status_code == 429:
            raise RateLimitError("OpenWeather rate limit exceeded while fetching current weather.")
        if resp.status_code >= 500:
            raise UpstreamServiceError(
                f"OpenWeather current weather service error (status {resp.status_code})."
            )
        resp.raise_for_status()
        return resp.json()

    def fetch_forecast(
        self,
        lat: float,
        lon: float,
        units: str = "metric",
        hours: int = 12,
    ) -> Dict[str, Any]:
        """Fetch forecast data and truncate to the requested horizon in hours."""
        self._require_api_key()

        if hours <= 0:
            hours = 12

        params = {
            "lat": lat,
            "lon": lon,
            "units": units,
            "appid": self._api_key,
        }

        with self._build_client() as client:
            resp = client.get("/data/2.5/forecast", params=params)

        if resp.status_code == 429:
            raise RateLimitError("OpenWeather rate limit exceeded while fetching forecast.")
        if resp.status_code >= 500:
            raise UpstreamServiceError(
                f"OpenWeather forecast service error (status {resp.status_code})."
            )
        resp.raise_for_status()

        data: Dict[str, Any] = resp.json()
        entries: List[Dict[str, Any]] = data.get("list", [])

        # Each entry is a 3-hour step. Compute how many we need.
        steps = max(1, hours // 3)
        data["list"] = entries[:steps]
        return data

