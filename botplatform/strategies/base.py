from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate


class BaseStrategy(ABC):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        raise NotImplementedError

    def on_order_update(self, update: OrderUpdate) -> None:
        return

    def get_state(self) -> dict:
        return {}

    def load_state(self, state: dict) -> None:
        return
