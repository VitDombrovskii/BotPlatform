from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict


class Event(BaseModel):
    type: str
    timestamp: int
    source: str
    correlation_id: Optional[str] = None
    payload: Dict = Field(default_factory=dict)
