import re
from typing import Any, Optional
from bot.exceptions import InvalidSymbolError, ValidationError as CustomValidationError

SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")

def validate_symbol_format(value: str) -> str:
    if not value or not value.strip():
        raise InvalidSymbolError("Symbol must not be empty.")
    normalized = value.strip().upper()
    if not SYMBOL_RE.match(normalized):
        raise InvalidSymbolError(
            f"'{value}' doesn't look like a valid symbol - expected "
            "something like BTCUSDT (uppercase, 5-20 chars)."
        )
    return normalized

def validate_against_exchange(
    symbol: str, order_type: str, quantity: float, price: Optional[float], exchange_info: dict[str, Any]
) -> None:
    symbols = exchange_info.get("symbols", [])
    symbol_info = next((s for s in symbols if s["symbol"] == symbol), None)
    if not symbol_info:
        raise CustomValidationError(f"Symbol {symbol} not found on the exchange.")
        
    filters = {f["filterType"]: f for f in symbol_info.get("filters", [])}
    
    # Step Size validation
    lot_size_filter = filters.get("LOT_SIZE")
    if lot_size_filter:
        step_size = float(lot_size_filter["stepSize"])
        remainder = round(quantity % step_size, 8)
        if remainder != 0 and remainder != step_size:
            raise CustomValidationError(f"Quantity {quantity} is invalid. It must be a multiple of {step_size}.")
            
    # Tick Size validation
    if order_type == "LIMIT" and price is not None:
        price_filter = filters.get("PRICE_FILTER")
        if price_filter:
            tick_size = float(price_filter["tickSize"])
            remainder = round(price % tick_size, 8)
            if remainder != 0 and remainder != tick_size:
                raise CustomValidationError(f"Price {price} is invalid. It must be a multiple of {tick_size}.")
