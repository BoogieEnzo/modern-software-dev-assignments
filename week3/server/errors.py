class OpenWeatherError(Exception):
    """Base class for OpenWeather-related errors."""


class MissingApiKeyError(OpenWeatherError):
    """Raised when OPENWEATHER_API_KEY is not configured."""


class CityNotFoundError(OpenWeatherError):
    """Raised when the geocoding API cannot resolve the requested city."""


class RateLimitError(OpenWeatherError):
    """Raised when OpenWeather responds with a rate limit status (e.g. 429)."""


class UpstreamServiceError(OpenWeatherError):
    """Raised when OpenWeather returns an unexpected 5xx or similar error."""

