from __future__ import annotations

from abc import ABC, abstractmethod

from botplatform.core.models import MarketSnapshot, SignalSnapshot


class BaseSignalsEngine(ABC):
    @abstractmethod
    async def on_market_snapshot(self, snapshot: MarketSnapshot) -> SignalSnapshot:
        raise NotImplementedError
