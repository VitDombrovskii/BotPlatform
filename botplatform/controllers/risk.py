from __future__ import annotations

from typing import List

from botplatform.core.models import ActionIntent
from botplatform.legs.base import LegState


class RiskController:
    """
    Локальный риск-контроллер для Leg.

    Ограничивает:
    - максимальный размер позиции,
    - работу bubble/scale при определённых условиях,
    - частоту действий.

    Здесь пока только интерфейс и минимальная реализация.
    """

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def filter_intents(self, state: LegState, intents: List[ActionIntent]) -> List[ActionIntent]:
        """
        Фильтрует список ActionIntent согласно риск-политике Leg.

        Сейчас возвращает intents без изменений — заглушка.
        """
        return intents
