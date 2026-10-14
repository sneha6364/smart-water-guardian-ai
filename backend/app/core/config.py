"""Application configuration via environment variables."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_ENV: str = "demo"  # "development" | "production" | "demo"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./smart_water.db"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama3-8b-8192"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Weather
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1/forecast"

    # Optional IBM integrations (leave blank if not required)
    LANGFLOW_API_URL: str = ""
    LANGFLOW_API_KEY: str = ""

    @property
    def is_demo_mode(self) -> bool:
        return self.APP_ENV == "demo" or not self.GROQ_API_KEY

    @property
    def groq_configured(self) -> bool:
        return bool(self.GROQ_API_KEY and self.GROQ_API_KEY != "your_groq_api_key_here")


settings = Settings()
