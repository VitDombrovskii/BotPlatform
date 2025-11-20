from __future__ import annotations

from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent
from botplatform.legs.base import LegState


class ScaleController:
    """
    Контроллер scale-in / scale-out логики внутри Leg.

    Детали поведения описаны в 21-scale-controller.md.
    Здесь пока только каркас интерфейса.
    """

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def on_tick(self, ctx: StrategyContext, state: LegState) -> List[ActionIntent]:
        """
        Анализирует движение цены относительно позиции и возвращает scale-действия.

        Сейчас возвращает пустой список — заглушка.
        """
        return []
