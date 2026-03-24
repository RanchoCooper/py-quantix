"""
模拟交易数据模型
包含 SQLite ORM 模型和 Pydantic 请求/响应模型
"""
import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Enum as SAEnum,
    Text, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from paper_trading.database import Base, _utcnow


# ==================== ORM Models ====================

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


# ==================== Pydantic Models ====================

class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    initial_balance: float = Field(..., gt=0)
    leverage: int = Field(default=10, ge=1, le=125)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    leverage: Optional[int] = Field(None, ge=1, le=125)


class AccountResponse(BaseModel):
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


class PositionUpdate(BaseModel):
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class PositionResponse(BaseModel):
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


class OrderCreate(BaseModel):
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


class SignalCreate(BaseModel):
    symbol: str
    timeframe: Optional[str] = None
    signal_type: str
    reason: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    symbol: str
    timeframe: Optional[str]
    signal_type: str
    reason: Optional[str]
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: SignalStatus
    created_at: datetime
    confirmed_at: Optional[datetime]


class DailyStatsResponse(BaseModel):
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


class AccountStatsResponse(BaseModel):
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


class EquityCurvePoint(BaseModel):
    date: str
    balance: float
    daily_pnl: float


class FeishuConfirmRequest(BaseModel):
    signal_id: str
    action: str = Field(..., pattern="^(confirm|reject)$")
    account_id: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
