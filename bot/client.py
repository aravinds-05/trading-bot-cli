import hashlib
import hmac
import time
from typing import Any, Optional

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from bot.config import Settings
from bot.exceptions import APIConnectionError, APIError, AuthenticationError
from bot.logging_config import get_logger

logger = get_logger(__name__)


def is_retryable(exception: BaseException) -> bool:
    if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code >= 500 or exception.response.status_code == 429
    return False


class BinanceFuturesTestnetClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._time_offset: int = 0
        self._exchange_info: Optional[dict[str, Any]] = None
        self._client = httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "BinanceFuturesTestnetClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def sync_time(self) -> None:
        try:
            logger.info("Synchronizing time with Binance...")
            response = await self._client.get("/fapi/v1/time")
            response.raise_for_status()
            server_time = response.json().get("serverTime")
            if server_time:
                local_time = int(time.time() * 1000)
                self._time_offset = server_time - local_time
                logger.info(f"Time synchronized. Offset is {self._time_offset}ms.")
            else:
                logger.warning("Could not find serverTime in response.")
        except Exception as e:
            logger.warning(f"Failed to synchronize time: {e}")

    async def get_exchange_info(self) -> dict[str, Any]:
        if self._exchange_info is not None:
            return self._exchange_info
            
        try:
            logger.info("Fetching exchange info...")
            response = await self._client.get("/fapi/v1/exchangeInfo")
            response.raise_for_status()
            self._exchange_info = response.json()
            return self._exchange_info
        except Exception as e:
            logger.error(f"Failed to fetch exchange info: {e}")
            raise APIConnectionError(f"Failed to fetch exchange info: {e}") from e

    async def _ensure_time_synced(self) -> None:
        """Lazily synchronise the clock before the first signed request."""
        if self._time_offset == 0:
            await self.sync_time()

    async def place_order(self, params: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_time_synced()
        return await self._signed_request("POST", "/fapi/v1/order", params)

    async def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """Query a single order's current state (used to surface MARKET fills)."""
        await self._ensure_time_synced()
        return await self._signed_request(
            "GET", "/fapi/v1/order", {"symbol": symbol, "orderId": order_id}
        )

    async def get_balance(self) -> list[dict[str, Any]]:
        await self._ensure_time_synced()
        return await self._signed_request("GET", "/fapi/v2/balance", {})

    async def get_positions(self) -> list[dict[str, Any]]:
        await self._ensure_time_synced()
        return await self._signed_request("GET", "/fapi/v2/positionRisk", {})

    async def get_recent_trades(self, limit: int = 5) -> list[dict[str, Any]]:
        await self._ensure_time_synced()
        return await self._signed_request("GET", "/fapi/v1/userTrades", {"limit": limit})

    async def _public_get(self, endpoint: str, description: str) -> Any:
        """Execute a public (unsigned) GET and return parsed JSON.

        Centralises the logging / error-wrapping that every public endpoint
        was duplicating.
        """
        try:
            logger.info("%s...", description)
            response = await self._client.get(endpoint)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error("%s failed: %s", description, e)
            raise APIConnectionError(f"{description} failed: {e}") from e

    async def get_price(self, symbol: str) -> float:
        data = await self._public_get(
            f"/fapi/v1/ticker/price?symbol={symbol}",
            f"Fetching price for {symbol}",
        )
        return float(data["price"])

    async def get_all_prices(self) -> dict[str, float]:
        data = await self._public_get(
            "/fapi/v1/ticker/price",
            "Fetching prices for all symbols",
        )
        return {item["symbol"]: float(item["price"]) for item in data}

    async def get_24hr_tickers(self) -> dict[str, dict[str, float]]:
        """Fetch 24h rolling stats (last price + % change) for all symbols.

        Public endpoint, no signing required. Returns a dict keyed by symbol:
        ``{"BTCUSDT": {"price": 61932.4, "change_pct": -1.23}, ...}``.
        """
        data = await self._public_get(
            "/fapi/v1/ticker/24hr",
            "Fetching 24hr ticker stats",
        )
        return {
            item["symbol"]: {
                "price": float(item.get("lastPrice", 0.0)),
                "change_pct": float(item.get("priceChangePercent", 0.0)),
            }
            for item in data
        }

    @retry(
        retry=retry_if_exception(is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def _signed_request(
        self, method: str, endpoint: str, params: dict[str, Any]
    ) -> Any:
        # Apply time offset to the current time to prevent clock drift issues
        current_time_ms = int(time.time() * 1000) + self._time_offset
        params["timestamp"] = current_time_ms
        params["recvWindow"] = self.settings.recv_window_ms
        params["signature"] = self._sign(params)

        headers = {
            "X-MBX-APIKEY": self.settings.api_key.get_secret_value(),
            "Content-Type": "application/x-www-form-urlencoded",
        }

        log_params = {k: v for k, v in params.items() if k != "signature"}
        logger.debug("Sending %s request to %s with params: %s", method, endpoint, log_params)

        try:
            request_kwargs = {"method": method, "url": endpoint, "headers": headers}
            if method.upper() == "GET":
                request_kwargs["params"] = params
            else:
                request_kwargs["data"] = params
                
            response = await self._client.request(**request_kwargs)
            response.raise_for_status()
            return self._handle_response(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code < 500 and e.response.status_code != 429:
                return self._handle_response(e.response)
            raise
        except httpx.RequestError as e:
            logger.error("Network error calling %s: %s", endpoint, e)
            raise APIConnectionError(f"Network error: {e}") from e

    def _handle_response(self, response: httpx.Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            raise APIError(f"Invalid JSON from Binance: {response.text}", response.status_code)

        if not response.is_success:
            if isinstance(data, dict):
                code = data.get("code", "UNKNOWN")
                msg = data.get("msg", "Unknown error")
                
                if code == -2015 or code == -1022:  # Auth errors
                    raise AuthenticationError(f"Binance Auth Error: {msg}")
                
                raise APIError(f"Binance Error [{code}]: {msg}", response.status_code, data)
            else:
                raise APIError("Binance Error", response.status_code, {"raw": data})
            
        return data

    def _sign(self, params: dict[str, Any]) -> str:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return hmac.new(
            self.settings.api_secret.get_secret_value().encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
