"""Configuration management for TripMate AI Backend."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = ""

    # External APIs (Optional)
    skyscanner_api_key: str = ""
    booking_api_key: str = ""
    google_places_api_key: str = ""

    # Environment
    environment: Literal["development", "production", "test"] = "development"

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
