"""
信号 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# SignalStatus 定义在 models.py 中，通过延迟导入避免循环依赖
SignalStatus = None  # 类型注解用，实际类型由运行时导入填充


def _get_signal_status():
    """延迟导入 SignalStatus 以避免循环依赖"""
    from paper_trading.models import SignalStatus as SS
    return SS


class SignalCreate(BaseModel):
    """创建信号请求"""
    symbol: str
    timeframe: Optional[str] = None
    signal_type: str
    reason: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class SignalResponse(BaseModel):
    """信号响应"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    timeframe: Optional[str]
    signal_type: str
    reason: Optional[str]
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    quantity: Optional[float]
    status: str  # 使用 str 而非 SignalStatus enum，避免循环导入
    created_at: datetime
    confirmed_at: Optional[datetime]
