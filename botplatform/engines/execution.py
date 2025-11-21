from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from botplatform.core.models import OrderIntent, OrderUpdate


class BaseExecutionEngine(ABC):
    @abstractmethod
    async def submit(self, intents: List[OrderIntent]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def handle_update(self, update: OrderUpdate) -> None:
        raise NotImplementedError
