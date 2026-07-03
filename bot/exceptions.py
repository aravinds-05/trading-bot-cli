"""Custom exceptions for the trading bot.

Keeping these separate from a generic Exception makes it easy to catch
exactly what we expect (bad input, Binance errors, network issues) and
handle each one differently, instead of one big try/except that hides
what actually went wrong.
"""

from __future__ import annotations


class TradingBotError(Exception):
    """Base class - catch this if you just want "something we expected went wrong"."""


# ---- validation errors (raised before we ever hit the network) ----

class ValidationError(TradingBotError):
    pass


class InvalidSymbolError(ValidationError):
    pass


class InvalidQuantityError(ValidationError):
    pass


class InvalidOrderTypeError(ValidationError):
    pass


class InvalidSideError(ValidationError):
    pass


class MissingLimitPriceError(ValidationError):
    pass


class InvalidPriceError(ValidationError):
    pass


# ---- errors that come from actually talking to Binance ----

class APIError(TradingBotError):
    def __init__(self, message: str, status_code: int | None = None, response: dict | None = None) -> None:
        self.status_code = status_code
        self.response = response
        super().__init__(message)


class AuthenticationError(APIError):
    pass


class BinanceAPIError(APIError):
    """Binance responded, but with an error code (e.g. -1121 invalid symbol)."""

    def __init__(self, code: int | None, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class APIConnectionError(APIError):
    """Couldn't reach Binance at all - DNS, connection refused, etc."""


class NetworkError(APIConnectionError):
    """Legacy alias"""
    pass


class TimeoutError_(APIConnectionError):
    # trailing underscore so we don't shadow the builtin TimeoutError
    pass


class UnknownAPIError(APIError):
    """Catch-all for anything from the client layer we didn't expect."""
