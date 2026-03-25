"""
统计 Schema
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AccountStatsResponse(BaseModel):
    """账户统计响应"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    largest_win: float
    largest_loss: float
    current_positions: int
    open_position_pnl: float


class DailyStatsResponse(BaseModel):
    """每日统计响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    date: str
    opening_balance: float
    closing_balance: float
    daily_pnl: float
    daily_pnl_pct: float
    trade_count: int
    win_count: int
    lose_count: int
    largest_win: float
    largest_loss: float
    win_rate: float


class EquityCurvePoint(BaseModel):
    """权益曲线数据点"""
    date: str
    balance: float
    daily_pnl: float


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


class FeishuConfirmRequest(BaseModel):
    """飞书确认请求"""
    signal_id: str
    action: str = Field(..., pattern="^(confirm|reject)$")
    account_id: Optional[str] = None
