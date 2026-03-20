"""
策略模型
定义交易信号、持仓信息等核心数据结构
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

import pandas as pd
from loguru import logger


class SignalType(Enum):
    """交易信号类型"""
    BUY = "buy"
    SELL = "sell"
    SHORT = "short"
    COVER = "cover"
    CLOSE = "close"
    HOLD = "hold"


class Signal:
    """交易信号"""

    def __init__(
        self,
        signal_type: SignalType,
        symbol: str,
        price: float,
        amount: float = 0,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.signal_type = signal_type
        self.symbol = symbol
        self.price = price
        self.amount = amount
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.reason = reason
        self.metadata = metadata or {}

    def __repr__(self):
        return (
            f"Signal({self.signal_type.value}, {self.symbol}, "
            f"price={self.price}, amount={self.amount}, reason={self.reason})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "signal_type": self.signal_type.value,
            "symbol": self.symbol,
            "price": self.price,
            "amount": self.amount,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "reason": self.reason,
            "metadata": self.metadata,
        }


class Position:
    """持仓信息"""

    def __init__(
        self,
        symbol: str,
        side: str = "long",
        amount: float = 0,
        entry_price: float = 0,
        unrealized_pnl: float = 0,
    ):
        self.symbol = symbol
        self.side = side
        self.amount = amount
        self.entry_price = entry_price
        self.unrealized_pnl = unrealized_pnl

    @property
    def is_empty(self) -> bool:
        """是否空仓"""
        return self.amount == 0

    @property
    def value(self) -> float:
        """持仓价值"""
        return self.amount * self.entry_price

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "amount": self.amount,
            "entry_price": self.entry_price,
            "unrealized_pnl": self.unrealized_pnl,
        }


# K线列名常量
KLINE_COLUMNS = [
    'timestamp', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'number_of_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
]


def convert_klines_to_dataframe(klines: List) -> pd.DataFrame:
    """
    将K线数据转换为DataFrame

    Args:
        klines: K线数据列表

    Returns:
        转换后的DataFrame
    """
    if not klines:
        return pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

    first_item = klines[0]
    if isinstance(first_item, dict):
        df = pd.DataFrame(klines)
    else:
        df = pd.DataFrame(klines, columns=KLINE_COLUMNS)

    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df
