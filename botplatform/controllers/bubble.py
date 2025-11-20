from __future__ import annotations

from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent
from botplatform.legs.base import LegState


class BubbleController:
    """
    Контроллер пузырьковой логики для Leg.

    На этом этапе реализован только интерфейс. Детальная логика будет
    добавлена позже согласно документу 20-bubble-controller.md.
    """

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def on_tick(self, ctx: StrategyContext, state: LegState) -> List[ActionIntent]:
        """
        Анализирует состояние Leg и рынка, возвращает bubble-действия.

        Сейчас возвращает пустой список — заглушка.
        """
        return []
