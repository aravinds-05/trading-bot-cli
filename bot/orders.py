from __future__ import annotations

import asyncio
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from bot.client import BinanceFuturesTestnetClient
from bot.exceptions import TradingBotError, UnknownAPIError
from bot.logging_config import get_logger
from bot.validators import validate_symbol_format, validate_against_exchange

logger = get_logger(__name__)


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderRequest(BaseModel):
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float = Field(gt=0, description="Quantity must be greater than zero.")
    price: Optional[float] = Field(None, gt=0, description="Price must be greater than zero if provided.")
    newClientOrderId: str = Field(default_factory=lambda: uuid.uuid4().hex, description="Unique ID for idempotency")

    @field_validator("symbol", mode="before")
    def _validate_symbol(cls, value: str) -> str:
        return validate_symbol_format(value)

    @model_validator(mode="after")
    def _validate_price(self) -> OrderRequest:
        if self.order_type == OrderType.LIMIT and self.price is None:
            raise ValueError("LIMIT orders need a price.")
        if self.order_type == OrderType.MARKET:
            self.price = None
        return self


class OrderResult(BaseModel):
    order_id: Optional[int]
    status: Optional[str]
    executed_qty: Optional[str]
    avg_price: Optional[str]
    raw_response: dict[str, Any]


class OrderService:
    def __init__(self, client: BinanceFuturesTestnetClient) -> None:
        self._client = client

    async def place_order(self, request: OrderRequest) -> OrderResult:
        logger.info("Validating order parameters with exchange info...")
        exchange_info = await self._client.get_exchange_info()
        self._validate_against_exchange(request, exchange_info)

        params = self._build_params(request)
        logger.info("Placing order: %s", request)

        try:
            response = await self._client.place_order(params)
        except TradingBotError:
            raise  # already one of ours, let it bubble up as-is
        except Exception as exc:  # pragma: no cover
            logger.exception("Unexpected error while placing order")
            raise UnknownAPIError(str(exc)) from exc

        logger.info("Order response: %s", response)
        result = self._to_result(response)

        # MARKET orders return an immediate ACK (status NEW, executedQty 0) because
        # fills settle asynchronously. Poll the order once or twice to surface the
        # real executedQty / avgPrice for clearer output and logging.
        if request.order_type == OrderType.MARKET and result.order_id is not None:
            enriched = await self._await_fill(request.symbol, result.order_id)
            if enriched is not None:
                result = enriched

        return result

    async def _await_fill(
        self, symbol: str, order_id: int, attempts: int = 3, delay: float = 0.4
    ) -> Optional[OrderResult]:
        """Poll a freshly placed order until it reaches a terminal state.

        Returns an enriched OrderResult, or None if the fill could not be
        confirmed (in which case the original ACK result is kept).
        """
        terminal = {"FILLED", "PARTIALLY_FILLED", "CANCELED", "EXPIRED", "REJECTED"}
        for attempt in range(attempts):
            try:
                data = await self._client.get_order(symbol, order_id)
            except TradingBotError as exc:
                logger.warning("Could not fetch fill status for order %s: %s", order_id, exc)
                return None
            if data.get("status") in terminal:
                logger.info("Order fill confirmed: %s", data)
                return self._to_result(data)
            if attempt < attempts - 1:
                await asyncio.sleep(delay)
        logger.info("Order %s not yet filled after %d checks; keeping ACK result.", order_id, attempts)
        return None

    def _validate_against_exchange(self, request: OrderRequest, exchange_info: dict[str, Any]) -> None:
        validate_against_exchange(
            symbol=request.symbol,
            order_type=request.order_type.value,
            quantity=request.quantity,
            price=request.price,
            exchange_info=exchange_info
        )

    @staticmethod
    def _build_params(request: OrderRequest) -> dict[str, Any]:
        params: dict[str, Any] = {
            "symbol": request.symbol,
            "side": request.side.value,
            "type": request.order_type.value,
            "quantity": request.quantity,
            "newClientOrderId": request.newClientOrderId,
        }
        if request.order_type == OrderType.LIMIT:
            params["price"] = request.price
            params["timeInForce"] = "GTC"
        return params

    @staticmethod
    def _to_result(response: dict[str, Any]) -> OrderResult:
        return OrderResult(
            order_id=response.get("orderId"),
            status=response.get("status"),
            executed_qty=response.get("executedQty"),
            avg_price=response.get("avgPrice"),
            raw_response=response,
        )
