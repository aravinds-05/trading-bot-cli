from __future__ import annotations

from bot.client import BinanceFuturesTestnetClient
from bot.orders import OrderRequest, OrderResult, OrderService

async def execute_order_with_client(client: BinanceFuturesTestnetClient, request: OrderRequest) -> OrderResult:
    """Executes an order using a pre-existing client to preserve connection pooling and caching."""
    service = OrderService(client)
    return await service.place_order(request)
