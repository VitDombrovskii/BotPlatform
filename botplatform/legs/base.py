from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate
from pydantic import BaseModel


class LegState(BaseModel):
    """
    Состояние Leg, которое может сохраняться и восстанавливаться из Storage.

    На этом уровне определены только общие поля; конкретные реализации могут
    добавлять свои расширения через наследование или поле extra.
    """

    side: str  # LONG / SHORT / custom
    size: float = 0.0
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    extra: dict = {}


class BaseLeg(ABC):
    """
    Абстрактная торговая нога (Leg).

    Leg управляет одной направленной позицией и инкапсулирует:
    - bubble логику,
    - scale логику,
    - локальный риск-контроль.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        """Вызывается на каждом тике. Должен вернуть список ActionIntent."""
        raise NotImplementedError

    @abstractmethod
    def on_order_update(self, update: OrderUpdate) -> None:
        """Обновление состояния по событию ордера."""
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> LegState:
        """Текущее состояние Leg для сохранения."""
        raise NotImplementedError

    @abstractmethod
    def load_state(self, state: LegState) -> None:
        """Загрузка состояния Leg из сохранённого снапшота."""
        raise NotImplementedError
