from __future__ import annotations

from typing import Dict, List

from botplatform.core.context import StrategyContext
from botplatform.core.models import ActionIntent, OrderUpdate
from botplatform.strategies.base import BaseStrategy


class StrategyEngine:
    def __init__(self) -> None:
        self._strategies: Dict[str, BaseStrategy] = {}

    def register_strategy(self, strategy: BaseStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def on_tick(self, ctx: StrategyContext) -> List[ActionIntent]:
        intents: List[ActionIntent] = []
        for strategy in self._strategies.values():
            intents.extend(strategy.on_tick(ctx))
        return intents

    def on_order_update(self, update: OrderUpdate) -> None:
        for strategy in self._strategies.values():
            strategy.on_order_update(update)
