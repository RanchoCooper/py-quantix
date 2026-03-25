"""
账户 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    """创建账户请求"""
    name: str = Field(..., min_length=1, max_length=100)
    initial_balance: float = Field(..., gt=0)
    leverage: int = Field(default=10, ge=1, le=125)


class AccountUpdate(BaseModel):
    """更新账户请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    leverage: Optional[int] = Field(None, ge=1, le=125)


class AccountResponse(BaseModel):
    """账户响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    initial_balance: float
    balance: float
    frozen_margin: float
    available_balance: float
    total_pnl: float
    total_pnl_pct: float
    leverage: int
    created_at: datetime
    updated_at: datetime
