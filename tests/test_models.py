from pydantic import ValidationError
import pytest
from bot.orders import OrderRequest, OrderType, Side
from bot.exceptions import InvalidSymbolError

def test_valid_market_order():
    req = OrderRequest(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=1.0)
    assert req.symbol == "BTCUSDT"

def test_valid_limit_order():
    req = OrderRequest(symbol="BTCUSDT", side="SELL", order_type="LIMIT", quantity=1.0, price=50000.0)
    assert req.price == 50000.0

def test_invalid_symbol():
    with pytest.raises(InvalidSymbolError):
        OrderRequest(symbol="invalid-symbol!", side="BUY", order_type="MARKET", quantity=1.0)

def test_negative_quantity():
    with pytest.raises(ValidationError):
        OrderRequest(symbol="BTCUSDT", side="BUY", order_type="MARKET", quantity=-1.0)

def test_limit_order_missing_price():
    with pytest.raises(ValidationError):
        OrderRequest(symbol="BTCUSDT", side="BUY", order_type="LIMIT", quantity=1.0)
