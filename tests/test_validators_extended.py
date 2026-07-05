"""Extended tests for bot.validators – covers edge-cases not hit in the
original test suite (empty symbol, whitespace-only, exchange validation
branches).
"""

from __future__ import annotations

import pytest

from bot.exceptions import InvalidSymbolError, ValidationError as CustomValidationError
from bot.validators import validate_against_exchange, validate_symbol_format


class TestValidateSymbolFormat:
    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidSymbolError, match="must not be empty"):
            validate_symbol_format("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(InvalidSymbolError, match="must not be empty"):
            validate_symbol_format("   ")

    def test_normalizes_to_uppercase(self) -> None:
        assert validate_symbol_format("btcusdt") == "BTCUSDT"

    def test_strips_whitespace(self) -> None:
        assert validate_symbol_format("  ETHUSDT  ") == "ETHUSDT"

    def test_too_short_raises(self) -> None:
        with pytest.raises(InvalidSymbolError):
            validate_symbol_format("BTC")

    def test_special_characters_raise(self) -> None:
        with pytest.raises(InvalidSymbolError):
            validate_symbol_format("BTC-USDT")


class TestValidateAgainstExchange:
    @staticmethod
    def _exchange_info(
        symbol: str = "BTCUSDT",
        step_size: str = "0.001",
        tick_size: str = "0.10",
    ) -> dict:
        return {
            "symbols": [
                {
                    "symbol": symbol,
                    "filters": [
                        {"filterType": "LOT_SIZE", "stepSize": step_size},
                        {"filterType": "PRICE_FILTER", "tickSize": tick_size},
                    ],
                }
            ]
        }

    def test_unknown_symbol_raises(self) -> None:
        with pytest.raises(CustomValidationError, match="not found on the exchange"):
            validate_against_exchange("XYZUSDT", "MARKET", 1.0, None, self._exchange_info())

    def test_invalid_quantity_step_size(self) -> None:
        with pytest.raises(CustomValidationError, match="must be a multiple"):
            validate_against_exchange("BTCUSDT", "MARKET", 0.0005, None, self._exchange_info())

    def test_valid_quantity_passes(self) -> None:
        validate_against_exchange("BTCUSDT", "MARKET", 0.001, None, self._exchange_info())

    def test_limit_invalid_tick_size(self) -> None:
        with pytest.raises(CustomValidationError, match="must be a multiple"):
            validate_against_exchange("BTCUSDT", "LIMIT", 0.001, 50000.05, self._exchange_info())

    def test_limit_valid_tick_size(self) -> None:
        validate_against_exchange("BTCUSDT", "LIMIT", 0.001, 50000.10, self._exchange_info())

    def test_market_order_skips_price_validation(self) -> None:
        # MARKET orders don't validate price even if price is provided
        validate_against_exchange("BTCUSDT", "MARKET", 0.001, 99999.99, self._exchange_info())

    def test_no_filters_passes(self) -> None:
        info = {"symbols": [{"symbol": "BTCUSDT", "filters": []}]}
        validate_against_exchange("BTCUSDT", "MARKET", 0.001, None, info)
