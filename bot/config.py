"""Loads config/settings from environment variables using Pydantic.

This replaces manual os.getenv parsing and automatically enforces type
safety and provides defaults.

Each field is bound to an explicit environment-variable name via
``validation_alias`` so the variables documented in ``.env.example``
(BINANCE_API_KEY, REQUEST_TIMEOUT_SECONDS, LOG_DIR, ...) are the exact
names that take effect. ``populate_by_name=True`` keeps the plain field
names usable for direct instantiation (e.g. in tests).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "trading_bot.log"
RECV_WINDOW_MS = 5000


class Settings(BaseSettings):
    api_key: SecretStr = Field(validation_alias="BINANCE_API_KEY")
    api_secret: SecretStr = Field(validation_alias="BINANCE_API_SECRET")
    base_url: str = Field(default=TESTNET_BASE_URL, validation_alias="BINANCE_BASE_URL")
    timeout_seconds: int = Field(default=DEFAULT_TIMEOUT, validation_alias="REQUEST_TIMEOUT_SECONDS")
    log_dir: str = Field(default=DEFAULT_LOG_DIR, validation_alias="LOG_DIR")
    log_file: str = Field(default=DEFAULT_LOG_FILE, validation_alias="LOG_FILE")
    recv_window_ms: int = Field(default=RECV_WINDOW_MS, validation_alias="RECV_WINDOW_MS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    @property
    def log_path(self) -> Path:
        project_root = Path(__file__).parent.parent
        directory = project_root / self.log_dir
        directory.mkdir(parents=True, exist_ok=True)
        return directory / self.log_file


def get_settings() -> Settings:
    """Load settings from .env file and validate."""
    from bot.exceptions import AuthenticationError
    from pydantic import ValidationError

    try:
        return Settings()
    except ValidationError as exc:
        # Check if the missing fields are the required api keys
        errors = exc.errors()
        for error in errors:
            if error["loc"] == ("api_key",) or error["loc"] == ("api_secret",):
                raise AuthenticationError(
                    "Missing Binance API credentials. Set BINANCE_API_KEY and "
                    "BINANCE_API_SECRET in .env (copy .env.example to get started)."
                ) from exc
        raise
