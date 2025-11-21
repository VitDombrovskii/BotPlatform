from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict


class OrderBookLevel(BaseModel):
    price: float
    size: float


class Trade(BaseModel):
    price: float
    size: float
    side: Literal["BUY", "SELL"]
    timestamp: int  # unix ms


class MarketSnapshot(BaseModel):
    symbol: str
    price: float
    bid: float
    ask: float
    bids: List[OrderBookLevel] = Field(default_factory=list)
    asks: List[OrderBookLevel] = Field(default_factory=list)
    trades: List[Trade] = Field(default_factory=list)
    timestamp: int  # unix ms


class SignalSnapshot(BaseModel):
    symbol: str
    data: Dict[str, float] = Field(default_factory=dict)
    timestamp: int  # unix ms


class PositionSnapshot(BaseModel):
    symbol: str
    side: Optional[Literal["LONG", "SHORT"]] = None
    size: float = 0.0
    entry_price: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    leverage: Optional[float] = None


class ActionIntent(BaseModel):
    action: str
    side: Optional[Literal["LONG", "SHORT"]] = None
    size: Optional[float] = None
    price: Optional[float] = None
    context: Optional[Dict] = None


class OrderIntent(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    type: Literal["MARKET", "LIMIT"]
    size: float
    price: Optional[float] = None
    client_id: str
    source: str
    context: Optional[Dict] = None


class OrderUpdate(BaseModel):
    order_id: str
    client_id: str
    symbol: str
    status: Literal["NEW", "PARTIAL", "FILLED", "CANCELLED", "REJECTED"]
    filled_size: float
    remaining_size: float
    avg_fill_price: Optional[float] = None
    timestamp: int  # unix ms
    raw: Dict
