from __future__ import annotations

from pydantic import BaseModel
from typing import Optional

from .models import MarketSnapshot, SignalSnapshot, PositionSnapshot


class StrategyContext(BaseModel):
    """
    Контекст, передаваемый в стратегию и Legs.

    Содержит минимально необходимый срез данных:
    - рыночное состояние,
    - рассчитанные сигналы,
    - текущую позицию (по символу),
    - технический timestamp.
    """

    symbol: str
    market: MarketSnapshot
    signals: Optional[SignalSnapshot] = None
    position: Optional[PositionSnapshot] = None
    timestamp: int  # unix ms
