from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict


# -----------------------------
# Market Models
# -----------------------------


class OrderBookLevel(BaseModel):
    """Уровень стакана цен."""

    price: float
    size: float


class Trade(BaseModel):
    """Сделка по рынку."""

    price: float
    size: float
    side: Literal["BUY", "SELL"]
    timestamp: int  # unix ms


class MarketSnapshot(BaseModel):
    """
    Снимок состояния рынка в один момент времени.

    Используется MarketEngine, SignalsEngine и StrategyEngine.
    """

    symbol: str
    price: float
    bid: float
    ask: float
    bids: List[OrderBookLevel] = Field(default_factory=list)
    asks: List[OrderBookLevel] = Field(default_factory=list)
    trades: List[Trade] = Field(default_factory=list)
    timestamp: int  # unix ms


# -----------------------------
# Signals
# -----------------------------


class SignalSnapshot(BaseModel):
    """
    Снимок рассчитанных сигналов.

    values/data: произвольный набор индикаторов и метрик.
    """

    symbol: str
    data: Dict[str, float] = Field(default_factory=dict)
    timestamp: int  # unix ms


# -----------------------------
# Position Model
# -----------------------------


class PositionSnapshot(BaseModel):
    """
    Унифицированная модель позиции на бирже.

    Используется Legs, StrategyEngine и ExecutionEngine.
    """

    symbol: str
    side: Optional[Literal["LONG", "SHORT"]] = None
    size: float = 0.0
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    leverage: Optional[float] = None


# -----------------------------
# Intents
# -----------------------------


class ActionIntent(BaseModel):
    """
    Высокоуровневое намерение Leg / стратегии.

    Описывает "что сделать", но не обязано содержать все биржевые детали.
    """

    action: str  # open / close / scale_in / scale_out / bubble_entry / bubble_exit / ...
    side: Optional[Literal["LONG", "SHORT"]] = None
    size: Optional[float] = None
    price: Optional[float] = None
    context: Optional[Dict] = None


class OrderIntent(BaseModel):
    """
    Ордерное намерение, которое получит ExecutionEngine.

    Почти готовый ордер, но ещё не адаптированный под конкретную биржу.
    """

    symbol: str
    side: Literal["BUY", "SELL"]
    type: Literal["MARKET", "LIMIT"]
    size: float
    price: Optional[float] = None
    client_id: str
    source: str  # имя стратегии / Leg
    context: Optional[Dict] = None


# -----------------------------
# Order Updates
# -----------------------------


class OrderUpdate(BaseModel):
    """
    Обновление состояния ордера от биржи.

    Используется ExecutionEngine, StrategyEngine и Legs.
    """

    order_id: str
    client_id: str
    symbol: str
    status: Literal["NEW", "PARTIAL", "FILLED", "CANCELLED", "REJECTED"]
    filled_size: float
    remaining_size: float
    avg_fill_price: Optional[float] = None
    timestamp: int  # unix ms
    raw: Dict  # сырые данные от биржи
