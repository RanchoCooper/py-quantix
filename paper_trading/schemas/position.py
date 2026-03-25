"""
持仓 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PositionUpdate(BaseModel):
    """更新持仓请求"""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class PositionResponse(BaseModel):
    """持仓响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime
    updated_at: datetime
