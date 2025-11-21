from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from pydantic import BaseModel

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate


class LegState(BaseModel):
    side: str
    size: float = 0.0
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    extra: dict = {}


class BaseLeg(ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        raise NotImplementedError

    @abstractmethod
    def on_order_update(self, update: OrderUpdate) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> LegState:
        raise NotImplementedError

    @abstractmethod
    def load_state(self, state: LegState) -> None:
        raise NotImplementedError
