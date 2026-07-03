import pytest
import respx
import httpx
from bot.client import BinanceFuturesTestnetClient
from bot.config import Settings

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
