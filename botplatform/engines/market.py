from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, List

from botplatform.core.models import MarketSnapshot


class BaseMarketEngine(ABC):
    """
    Абстрактный движок рыночных данных.

    Отвечает за получение MarketSnapshot (через WS/REST) и передачу их
    в StrategyEngine и SignalsEngine.
    """

    @abstractmethod
    async def start(self) -> None:
        """Запуск источников данных (подписки, коннекты и т.д.)."""
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """Остановка всех источников данных."""
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable[[MarketSnapshot], Awaitable[None]]) -> None:
        """Подписка на обновления для указанных символов."""
        raise NotImplementedError
