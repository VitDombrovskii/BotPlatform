
from __future__ import annotations
import asyncio

from botplatform.utils.logging import configure_logging
from botplatform.core.event_bus import EventBus
from botplatform.engines.bingx_market import BingXMarketEngine
from botplatform.engines.strategy_runtime_bingx import BingXStrategyRuntime
from botplatform.exchanges.bingx.rest import BingXRest
from botplatform.exchanges.bingx.adapter import BingXExchangeAdapter

import config_bingx_example as cfg

async def app():
    log = configure_logging("botplatform.main.bingx")

    symbols = ["BTC-USDT"]

    bus = EventBus()
    rest = BingXRest(cfg.BINGX_API_KEY, cfg.BINGX_API_SECRET, cfg.BINGX_REST_BASE_URL)
    exchange = BingXExchangeAdapter(rest)

    market = BingXMarketEngine(bus, cfg.BINGX_WS_MARKET_URL, symbols)
    runtime = BingXStrategyRuntime(bus, exchange, symbols)

    await bus.start()
    task = asyncio.create_task(market.start())

    await asyncio.sleep(15)

    await market.stop()
    await bus.stop()
    task.cancel()

if __name__ == "__main__":
    asyncio.run(app())
