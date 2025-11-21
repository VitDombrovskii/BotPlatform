from __future__ import annotations

from typing import List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate
from botplatform.legs.base import BaseLeg, LegState
from botplatform.controllers.bubble import BubbleController
from botplatform.controllers.scale import ScaleController
from botplatform.controllers.risk import RiskController


class ShortLeg(BaseLeg):
    def __init__(self, name: str, base_size: float) -> None:
        super().__init__(name)
        self.state = LegState(side="SHORT")
        self.base_size = base_size
        self.bubble = BubbleController()
        self.scale = ScaleController()
        self.risk = RiskController()

    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        intents: List[ActionIntent] = []
        if self.state.size == 0.0:
            intents.append(
                ActionIntent(
                    action="open",
                    side="SHORT",
                    size=self.base_size,
                    context={"leg": self.name},
                )
            )
        intents = self.risk.filter_intents(self.state, intents)
        return intents

    def on_order_update(self, update: OrderUpdate) -> None:
        return

    def get_state(self) -> LegState:
        return self.state

    def load_state(self, state: LegState) -> None:
        self.state = state
