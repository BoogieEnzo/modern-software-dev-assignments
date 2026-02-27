import os


class Settings:
    """Simple configuration holder for the OpenWeather MCP server."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            # 不直接退出，让上层在真正调用时给出清晰错误信息
            self.api_key: str | None = None
        else:
            self.api_key = api_key

        self.base_url: str = os.getenv(
            "OPENWEATHER_BASE_URL",
            "https://api.openweathermap.org",
        ).rstrip("/")

        timeout_env = os.getenv("REQUEST_TIMEOUT_SECONDS", "10")
        try:
            self.request_timeout_seconds: float = float(timeout_env)
        except ValueError:
            self.request_timeout_seconds = 10.0


settings = Settings()

