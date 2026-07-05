"""Unit tests for bot.config – Settings model and get_settings()."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bot.config import Settings, get_settings
from bot.exceptions import AuthenticationError


class TestSettings:
    def test_defaults(self) -> None:
        s = Settings(api_key="k", api_secret="s")
        assert s.base_url == "https://testnet.binancefuture.com"
        assert s.timeout_seconds == 10
        assert s.log_dir == "logs"
        assert s.log_file == "trading_bot.log"
        assert s.recv_window_ms == 5000

    def test_secret_str_values(self) -> None:
        s = Settings(api_key="mykey", api_secret="mysecret")
        assert s.api_key.get_secret_value() == "mykey"
        assert s.api_secret.get_secret_value() == "mysecret"

    def test_log_path_creates_directory(self, tmp_path: Path) -> None:
        s = Settings(api_key="k", api_secret="s", log_dir=str(tmp_path / "newdir"))
        log_path = s.log_path
        assert log_path.parent.exists()
        assert log_path.name == "trading_bot.log"

    def test_custom_overrides(self) -> None:
        s = Settings(
            api_key="k",
            api_secret="s",
            base_url="https://custom.url",
            timeout_seconds=30,
            log_file="custom.log",
            recv_window_ms=10000,
        )
        assert s.base_url == "https://custom.url"
        assert s.timeout_seconds == 30
        assert s.log_file == "custom.log"
        assert s.recv_window_ms == 10000


class TestGetSettings:
    def test_raises_auth_error_when_keys_missing(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError, match="Missing Binance API credentials"):
                get_settings()

    def test_returns_settings_when_env_set(self) -> None:
        env = {"BINANCE_API_KEY": "key123", "BINANCE_API_SECRET": "secret456"}
        with patch.dict("os.environ", env, clear=True):
            s = get_settings()
            assert s.api_key.get_secret_value() == "key123"
            assert s.api_secret.get_secret_value() == "secret456"
