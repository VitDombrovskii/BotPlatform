from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict


class Event(BaseModel):
    """
    Базовая модель события в EventBus.

    type: строковый тип события, например 'market.snapshot' или 'order.filled'.
    timestamp: UNIX ms.
    source: строковый идентификатор источника события (engine/strategy/...).
    correlation_id: идентификатор цепочки событий (для трассировки).
    payload: произвольные данные события.
    """

    type: str
    timestamp: int
    source: str
    correlation_id: Optional[str] = None
    payload: Dict = Field(default_factory=dict)
