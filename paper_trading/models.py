"""
数据库模型 (ORM)
SQLAlchemy 异步模型定义

Pydantic DTO 已移至 paper_trading.schemas 模块。
为保持向后兼容，以下 DTO 仍从此模块导出：
"""
import enum
from typing import Optional

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text,
    ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from paper_trading.database import Base, _utcnow

# 枚举定义（可被其他模块复用）
__all__ = [
    "PositionSide",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "SignalStatus",
    "SignalType",
    "OrderSource",
    "PaperAccount",
    "Position",
    "Order",
    "Signal",
    "DailyStats",
]

# 向后兼容：重新导出 schemas（原有的导入路径）
from paper_trading.schemas import (
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    OrderCreate,
    OrderResponse,
    PositionUpdate,
    PositionResponse,
    AccountStatsResponse,
    DailyStatsResponse,
    EquityCurvePoint,
    PaginatedResponse,
    FeishuConfirmRequest,
)
from paper_trading.schemas.signal import SignalCreate, SignalResponse

# SignalStatus 已定义在 models.py 中，不从 schemas 导出

__all__.extend([
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "OrderCreate",
    "OrderResponse",
    "PositionUpdate",
    "PositionResponse",
    "SignalCreate",
    "SignalResponse",
    "AccountStatsResponse",
    "DailyStatsResponse",
    "EquityCurvePoint",
    "PaginatedResponse",
    "FeishuConfirmRequest",
])


class PositionSide(str, enum.Enum):
    LONG = "long"
    SHORT = "short"


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, enum.Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class SignalType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class OrderSource(str, enum.Enum):
    MANUAL = "manual"
    FEISHU = "feishu"
    ANALYZER = "analyzer"


class PaperAccount(Base):
    __tablename__ = "paper_accounts"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    initial_balance = Column(Float, nullable=False, default=10000.0)
    balance = Column(Float, nullable=False, default=10000.0)
    frozen_margin = Column(Float, nullable=False, default=0.0)
    total_pnl = Column(Float, nullable=False, default=0.0)
    leverage = Column(Integer, nullable=False, default=10)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="account", cascade="all, delete-orphan")
    daily_stats = relationship("DailyStats", back_populates="account", cascade="all, delete-orphan")


class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("paper_accounts.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=False, default=0.0)
    unrealized_pnl_pct = Column(Float, nullable=False, default=0.0)
    opened_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    account = relationship("PaperAccount", back_populates="positions")

    __table_args__ = (
        Index("idx_position_account", "account_id"),
        Index("idx_position_symbol", "symbol"),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("paper_accounts.id"), nullable=False)
    symbol = Column(String(50), nullable=False)
    side = Column(String(20), nullable=False)
    position_side = Column(String(20), nullable=True)
    order_type = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    filled_price = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=True)
    signal_id = Column(String(36), ForeignKey("signals.id"), nullable=True)
    fee = Column(Float, nullable=False, default=0.0)
    pnl = Column(Float, nullable=True)
    source = Column(String(20), nullable=False, default="manual")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    filled_at = Column(DateTime, nullable=True)

    account = relationship("PaperAccount", back_populates="orders")
    position = relationship("Position")

    __table_args__ = (
        Index("idx_order_account", "account_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_symbol", "symbol"),
    )


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String(36), primary_key=True)
    symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=True)
    signal_type = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)
    entry_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    quantity = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, default=_utcnow)
    confirmed_at = Column(DateTime, nullable=True)

    orders = relationship("Order")

    __table_args__ = (
        Index("idx_signal_status", "status"),
        Index("idx_signal_symbol", "symbol"),
    )


class DailyStats(Base):
    __tablename__ = "daily_stats"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("paper_accounts.id"), nullable=False)
    date = Column(String(10), nullable=False)
    opening_balance = Column(Float, nullable=False)
    closing_balance = Column(Float, nullable=False)
    daily_pnl = Column(Float, nullable=False, default=0.0)
    daily_pnl_pct = Column(Float, nullable=False, default=0.0)
    trade_count = Column(Integer, nullable=False, default=0)
    win_count = Column(Integer, nullable=False, default=0)
    lose_count = Column(Integer, nullable=False, default=0)
    largest_win = Column(Float, nullable=False, default=0.0)
    largest_loss = Column(Float, nullable=False, default=0.0)
    win_rate = Column(Float, nullable=False, default=0.0)

    account = relationship("PaperAccount", back_populates="daily_stats")

    __table_args__ = (
        UniqueConstraint("account_id", "date", name="uq_account_date"),
        Index("idx_stats_account", "account_id"),
    )
