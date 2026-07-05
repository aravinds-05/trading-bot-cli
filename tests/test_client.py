import pytest
import respx
import httpx
from bot.client import BinanceFuturesTestnetClient
from bot.config import Settings
from bot.exceptions import APIConnectionError, AuthenticationError, BinanceAPIError

@pytest.fixture
def settings():
    return Settings(api_key="test_key", api_secret="test_secret", base_url="https://testnet.binancefuture.com")

@pytest.fixture
def client(settings):
    return BinanceFuturesTestnetClient(settings)

@pytest.mark.asyncio
@respx.mock
async def test_sync_time(client):
    respx.get("https://testnet.binancefuture.com/fapi/v1/time").mock(return_value=httpx.Response(200, json={"serverTime": 1000000000000}))
    await client.sync_time()
    assert client._time_offset != 0

@pytest.mark.asyncio
@respx.mock
async def test_place_order(client):
    respx.get("https://testnet.binancefuture.com/fapi/v1/time").mock(return_value=httpx.Response(200, json={"serverTime": 1000000000000}))
    respx.post("https://testnet.binancefuture.com/fapi/v1/order").mock(return_value=httpx.Response(200, json={"orderId": 123}))
    
    result = await client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 1})
    assert result["orderId"] == 123


@pytest.mark.asyncio
@respx.mock
async def test_binance_error_propagates_with_code(client):
    """A Binance error response surfaces as a typed BinanceAPIError, preserving
    the numeric error code and status instead of a generic APIError string."""
    respx.get("https://testnet.binancefuture.com/fapi/v1/time").mock(
        return_value=httpx.Response(200, json={"serverTime": 1000000000000})
    )
    respx.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    with pytest.raises(BinanceAPIError) as exc_info:
        await client.place_order({"symbol": "NOPE", "side": "BUY", "type": "MARKET", "quantity": 1})

    assert exc_info.value.code == -1121
    assert exc_info.value.status_code == 400
    assert "Invalid symbol." in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_auth_error_maps_to_authentication_error(client):
    respx.get("https://testnet.binancefuture.com/fapi/v1/time").mock(
        return_value=httpx.Response(200, json={"serverTime": 1000000000000})
    )
    respx.post("https://testnet.binancefuture.com/fapi/v1/order").mock(
        return_value=httpx.Response(401, json={"code": -2015, "msg": "Invalid API-key."})
    )

    with pytest.raises(AuthenticationError):
        await client.place_order({"symbol": "BTCUSDT", "side": "BUY", "type": "MARKET", "quantity": 1})


@pytest.mark.asyncio
@respx.mock
async def test_public_get_error_is_not_masked_as_connection_error(client):
    """A Binance error on a public endpoint must not be flattened into a
    generic APIConnectionError — the real code should propagate."""
    respx.get("https://testnet.binancefuture.com/fapi/v1/ticker/price").mock(
        return_value=httpx.Response(400, json={"code": -1121, "msg": "Invalid symbol."})
    )

    with pytest.raises(BinanceAPIError) as exc_info:
        await client.get_price("NOPE")

    assert exc_info.value.code == -1121


@pytest.mark.asyncio
@respx.mock
async def test_public_get_network_error_becomes_connection_error(client):
    respx.get("https://testnet.binancefuture.com/fapi/v1/ticker/price").mock(
        side_effect=httpx.ConnectError("boom")
    )

    with pytest.raises(APIConnectionError):
        await client.get_price("BTCUSDT")
