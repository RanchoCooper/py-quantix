"""
Schemas 模块
提取自 models.py 的 Pydantic DTO，保持向后兼容
"""
from paper_trading.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from paper_trading.schemas.order import OrderCreate, OrderResponse
from paper_trading.schemas.position import PositionUpdate, PositionResponse
from paper_trading.schemas.signal import SignalCreate, SignalResponse
from paper_trading.schemas.stats import (
    AccountStatsResponse,
    DailyStatsResponse,
    EquityCurvePoint,
    PaginatedResponse,
    FeishuConfirmRequest,
)

__all__ = [
    # account
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    # order
    "OrderCreate",
    "OrderResponse",
    # position
    "PositionUpdate",
    "PositionResponse",
    # signal
    "SignalCreate",
    "SignalResponse",
    # stats
    "AccountStatsResponse",
    "DailyStatsResponse",
    "EquityCurvePoint",
    "PaginatedResponse",
    "FeishuConfirmRequest",
]
