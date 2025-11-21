from __future__ import annotations

from typing import List

from botplatform.core.models import ActionIntent
from botplatform.legs.base import LegState


class RiskController:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def filter_intents(self, state: LegState, intents: List[ActionIntent]) -> List[ActionIntent]:
        return intents
