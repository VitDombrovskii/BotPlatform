from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate


class BaseStrategy(ABC):
    """
    Базовый класс стратегии.

    Стратегия:
    - получает StrategyContext,
    - делегирует принятие решений Legs,
    - возвращает список ActionIntent.
    """

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        """Основной метод стратегии, вызывается при каждом тик-событии."""
        raise NotImplementedError

    def on_order_update(self, update: OrderUpdate) -> None:
        """
        Обновление по ордеру. Базовая реализация пустая.

        Конкретные стратегии могут переопределять этот метод.
        """
        return

    def get_state(self) -> dict:
        """Сериализуемое состояние стратегии (по умолчанию пустое)."""
        return {}

    def load_state(self, state: dict) -> None:
        """Загрузка состояния стратегии (по умолчанию ничего не делает)."""
        return
