from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from botplatform.core.models import OrderIntent, OrderUpdate


class BaseExecutionEngine(ABC):
    """
    Абстрактный Execution Engine.

    Получает OrderIntent и превращает их в реальные ордера через ExchangeAdapter.
    """

    @abstractmethod
    async def submit(self, intents: List[OrderIntent]) -> None:
        """Передать список ордерных намерений на исполнение."""
        raise NotImplementedError

    @abstractmethod
    async def handle_update(self, update: OrderUpdate) -> None:
        """Обработка обновления ордера (OrderUpdate) от биржи."""
        raise NotImplementedError
