from __future__ import annotations

import asyncio

from botplatform.core.event_bus import EventBus
from botplatform.engines.fake_market import FakeMarketEngine
from botplatform.engines.strategy_runtime import StrategyRuntime
from botplatform.exchanges.mock import MockExchange
from botplatform.utils.logging import configure_logging


async def app() -> None:
    logger = configure_logging("botplatform.main")
    symbols = ["BTCUSDT"]

    event_bus = EventBus()
    exchange = MockExchange()
    market = FakeMarketEngine(event_bus=event_bus, symbols=symbols, interval_ms=500, mode="sine")
    runtime = StrategyRuntime(event_bus=event_bus, exchange=exchange, symbols=symbols)

    logger.info("Starting BotPlatform demo runtime...")
    await event_bus.start()
    await market.start()

    try:
        await asyncio.sleep(5.0)
    finally:
        logger.info("Stopping...")
        await market.stop()
        await event_bus.stop()
        logger.info("Demo finished.")


if __name__ == "__main__":
    asyncio.run(app())
