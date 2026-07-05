"""Extended unit tests for bot.client – covers methods not exercised by the
original test_client.py (get_balance, get_positions, get_recent_trades,
get_price, get_all_prices, get_24hr_tickers, get_exchange_info, get_order,
_handle_response, _sign, is_retryable).
"""

from __future__ import annotations

import httpx
import pytest
import respx

from bot.client import BinanceFuturesTestnetClient, is_retryable
from bot.config import Settings
from bot.exceptions import APIConnectionError, APIError, AuthenticationError

BASE = "https://testnet.binancefuture.com"


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="test_key", api_secret="test_secret", base_url=BASE)


@pytest.fixture
def client(settings: Settings) -> BinanceFuturesTestnetClient:
    return BinanceFuturesTestnetClient(settings)


# ── is_retryable ──────────────────────────────────────────────────────

class TestIsRetryable:
    def test_timeout_exception_is_retryable(self) -> None:
        assert is_retryable(httpx.ReadTimeout("timeout")) is True

    def test_network_error_is_retryable(self) -> None:
        assert is_retryable(httpx.ConnectError("conn error")) is True

    def test_500_status_is_retryable(self) -> None:
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(500, request=request)
        exc = httpx.HTTPStatusError("server error", request=request, response=response)
        assert is_retryable(exc) is True

    def test_429_status_is_retryable(self) -> None:
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(429, request=request)
        exc = httpx.HTTPStatusError("rate limited", request=request, response=response)
        assert is_retryable(exc) is True

    def test_400_status_is_not_retryable(self) -> None:
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(400, request=request)
        exc = httpx.HTTPStatusError("bad request", request=request, response=response)
        assert is_retryable(exc) is False

    def test_generic_exception_is_not_retryable(self) -> None:
        assert is_retryable(ValueError("oops")) is False


# ── sync_time ─────────────────────────────────────────────────────────

class TestSyncTime:
    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_time_no_server_time(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(200, json={})
        )
        await client.sync_time()
        assert client._time_offset == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_time_exception(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(500, json={})
        )
        await client.sync_time()
        # Should not raise; offset stays 0
        assert client._time_offset == 0


# ── get_exchange_info ─────────────────────────────────────────────────

class TestGetExchangeInfo:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetches_and_caches(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/exchangeInfo").mock(
            return_value=httpx.Response(200, json={"symbols": []})
        )
        info1 = await client.get_exchange_info()
        info2 = await client.get_exchange_info()
        assert info1 == {"symbols": []}
        assert info1 is info2  # cached

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_on_failure(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/exchangeInfo").mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(APIConnectionError):
            await client.get_exchange_info()


# ── get_price ─────────────────────────────────────────────────────────

class TestGetPrice:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_float(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/price", params={"symbol": "BTCUSDT"}).mock(
            return_value=httpx.Response(200, json={"price": "61234.50"})
        )
        price = await client.get_price("BTCUSDT")
        assert price == 61234.50

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_on_failure(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(APIConnectionError):
            await client.get_price("BTCUSDT")


# ── get_all_prices ────────────────────────────────────────────────────

class TestGetAllPrices:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_dict(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"symbol": "BTCUSDT", "price": "61000.0"},
                    {"symbol": "ETHUSDT", "price": "1700.0"},
                ],
            )
        )
        prices = await client.get_all_prices()
        assert prices == {"BTCUSDT": 61000.0, "ETHUSDT": 1700.0}

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_on_failure(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/price").mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(APIConnectionError):
            await client.get_all_prices()


# ── get_24hr_tickers ──────────────────────────────────────────────────

class TestGet24hrTickers:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_dict(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/24hr").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"symbol": "BTCUSDT", "lastPrice": "61000.0", "priceChangePercent": "1.5"},
                ],
            )
        )
        tickers = await client.get_24hr_tickers()
        assert tickers["BTCUSDT"]["price"] == 61000.0
        assert tickers["BTCUSDT"]["change_pct"] == 1.5

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_on_failure(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/ticker/24hr").mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(APIConnectionError):
            await client.get_24hr_tickers()


# ── get_balance / get_positions / get_recent_trades / get_order ───────

class TestSignedEndpoints:
    @pytest.mark.asyncio
    @respx.mock
    async def test_get_balance(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(200, json={"serverTime": 1000000000000})
        )
        respx.get(f"{BASE}/fapi/v2/balance").mock(
            return_value=httpx.Response(200, json=[{"asset": "USDT", "balance": "1000"}])
        )
        result = await client.get_balance()
        assert result == [{"asset": "USDT", "balance": "1000"}]

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_positions(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(200, json={"serverTime": 1000000000000})
        )
        respx.get(f"{BASE}/fapi/v2/positionRisk").mock(
            return_value=httpx.Response(200, json=[{"symbol": "BTCUSDT"}])
        )
        result = await client.get_positions()
        assert result == [{"symbol": "BTCUSDT"}]

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_recent_trades(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(200, json={"serverTime": 1000000000000})
        )
        respx.get(f"{BASE}/fapi/v1/userTrades").mock(
            return_value=httpx.Response(200, json=[{"id": 1}])
        )
        result = await client.get_recent_trades(limit=5)
        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_order(self, client: BinanceFuturesTestnetClient) -> None:
        respx.get(f"{BASE}/fapi/v1/time").mock(
            return_value=httpx.Response(200, json={"serverTime": 1000000000000})
        )
        respx.get(f"{BASE}/fapi/v1/order").mock(
            return_value=httpx.Response(200, json={"orderId": 99, "status": "FILLED"})
        )
        result = await client.get_order("BTCUSDT", 99)
        assert result["orderId"] == 99


# ── _handle_response ─────────────────────────────────────────────────

class TestHandleResponse:
    def test_success_json(self, client: BinanceFuturesTestnetClient) -> None:
        resp = httpx.Response(200, json={"ok": True})
        assert client._handle_response(resp) == {"ok": True}

    def test_invalid_json(self, client: BinanceFuturesTestnetClient) -> None:
        resp = httpx.Response(200, text="not json", headers={"content-type": "text/plain"})
        with pytest.raises(APIError, match="Invalid JSON"):
            client._handle_response(resp)

    def test_auth_error(self, client: BinanceFuturesTestnetClient) -> None:
        request = httpx.Request("POST", f"{BASE}/fapi/v1/order")
        resp = httpx.Response(
            403, json={"code": -2015, "msg": "Invalid API-key"}, request=request
        )
        with pytest.raises(AuthenticationError):
            client._handle_response(resp)

    def test_auth_error_1022(self, client: BinanceFuturesTestnetClient) -> None:
        request = httpx.Request("POST", f"{BASE}/fapi/v1/order")
        resp = httpx.Response(
            400, json={"code": -1022, "msg": "Signature invalid"}, request=request
        )
        with pytest.raises(AuthenticationError):
            client._handle_response(resp)

    def test_generic_api_error(self, client: BinanceFuturesTestnetClient) -> None:
        request = httpx.Request("POST", f"{BASE}/fapi/v1/order")
        resp = httpx.Response(
            400, json={"code": -1121, "msg": "Invalid symbol"}, request=request
        )
        with pytest.raises(APIError, match="Invalid symbol"):
            client._handle_response(resp)

    def test_non_dict_error(self, client: BinanceFuturesTestnetClient) -> None:
        request = httpx.Request("POST", f"{BASE}/fapi/v1/order")
        resp = httpx.Response(400, json=["error list"], request=request)
        with pytest.raises(APIError, match="Binance Error"):
            client._handle_response(resp)


# ── _sign ─────────────────────────────────────────────────────────────

class TestSign:
    def test_signature_is_hex_string(self, client: BinanceFuturesTestnetClient) -> None:
        sig = client._sign({"symbol": "BTCUSDT", "timestamp": 123456789})
        assert isinstance(sig, str)
        assert len(sig) == 64  # SHA-256 hex digest

    def test_deterministic(self, client: BinanceFuturesTestnetClient) -> None:
        params = {"a": "1", "b": "2"}
        assert client._sign(params) == client._sign(params)
