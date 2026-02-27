from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class CurrentWeather:
    city: str
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    description: str
    observed_at: str  # ISO 8601 string

    @classmethod
    def from_openweather(cls, payload: Dict[str, Any], city_name: str) -> "CurrentWeather":
        main = payload.get("main", {})
        wind = payload.get("wind", {})
        weather_list = payload.get("weather") or []
        description = weather_list[0].get("description", "") if weather_list else ""

        timestamp = payload.get("dt")
        if isinstance(timestamp, (int, float)):
            observed = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        else:
            observed = datetime.now(tz=timezone.utc).isoformat()

        return cls(
            city=city_name,
            temperature=float(main.get("temp", 0.0)),
            feels_like=float(main.get("feels_like", 0.0)),
            humidity=int(main.get("humidity", 0)),
            wind_speed=float(wind.get("speed", 0.0)),
            description=description,
            observed_at=observed,
        )


@dataclass
class ForecastEntry:
    time: str
    temperature: float
    description: str
    probability_of_precipitation: float


@dataclass
class WeatherForecast:
    city: str
    entries: List[ForecastEntry]

    @classmethod
    def from_openweather(cls, payload: Dict[str, Any], city_name: str) -> "WeatherForecast":
        raw_entries = payload.get("list") or []
        entries: List[ForecastEntry] = []
        for item in raw_entries:
            main = item.get("main", {})
            weather_list = item.get("weather") or []
            description = weather_list[0].get("description", "") if weather_list else ""
            pop = float(item.get("pop", 0.0))
            time_str = item.get("dt_txt")
            if not time_str:
                # Fallback to timestamp if available
                dt_val = item.get("dt")
                if isinstance(dt_val, (int, float)):
                    time_str = datetime.fromtimestamp(dt_val, tz=timezone.utc).isoformat()
                else:
                    time_str = datetime.now(tz=timezone.utc).isoformat()

            entries.append(
                ForecastEntry(
                    time=time_str,
                    temperature=float(main.get("temp", 0.0)),
                    description=description,
                    probability_of_precipitation=pop,
                )
            )
        return cls(city=city_name, entries=entries)

