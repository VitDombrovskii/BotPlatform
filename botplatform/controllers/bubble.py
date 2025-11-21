from __future__ import annotations

from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent
from botplatform.legs.base import LegState


class BubbleController:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def on_tick(self, ctx: StrategyContext, state: LegState) -> List[ActionIntent]:
        return []
