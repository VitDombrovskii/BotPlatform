from __future__ import annotations

from abc import ABC, abstractmethod

from botplatform.core.models import MarketSnapshot, SignalSnapshot


class BaseSignalsEngine(ABC):
    """
    Движок сигналов.

    Получает MarketSnapshot, рассчитывает сигналы и отдает SignalSnapshot.
    """

    @abstractmethod
    async def on_market_snapshot(self, snapshot: MarketSnapshot) -> SignalSnapshot:
        """Рассчитать сигналы по новому MarketSnapshot."""
        raise NotImplementedError
