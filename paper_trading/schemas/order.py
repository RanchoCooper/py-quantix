"""
订单 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """创建订单请求"""
    account_id: str
    symbol: str = Field(..., min_length=1)
    side: str = Field(..., pattern="^(buy|sell)$")
    position_side: Optional[str] = Field(None, pattern="^(long|short)$")
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    quantity: float = Field(..., gt=0)
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    source: str = Field(default="manual", pattern="^(manual|feishu|analyzer)$")
    signal_id: Optional[str] = None
    reason: Optional[str] = None
    position_id: Optional[str] = None


class OrderResponse(BaseModel):
    """订单响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    symbol: str
    side: str
    position_side: Optional[str]
    order_type: str
    quantity: float
    price: Optional[float]
    filled_price: Optional[float]
    status: str
    position_id: Optional[str]
    signal_id: Optional[str]
    fee: float
    pnl: Optional[float]
    source: str
    reason: Optional[str]
    created_at: datetime
    filled_at: Optional[datetime]
