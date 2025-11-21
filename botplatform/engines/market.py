from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, List

from botplatform.core.models import MarketSnapshot


class BaseMarketEngine(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable[[MarketSnapshot], Awaitable[None]]) -> None:
        raise NotImplementedError
