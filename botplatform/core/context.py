from __future__ import annotations

from pydantic import BaseModel
from typing import Optional

from .models import MarketSnapshot, SignalSnapshot, PositionSnapshot


class StrategyContext(BaseModel):
    symbol: str
    market: MarketSnapshot
    signals: Optional[SignalSnapshot] = None
    position: Optional[PositionSnapshot] = None
    timestamp: int  # unix ms
