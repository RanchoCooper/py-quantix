"""
策略工具函数
提供仓位计算、止损止盈计算等辅助功能
"""
from typing import Optional
import pandas as pd
import numpy as np


def calculate_position_size(
    balance: float,
    price: float,
    risk_pct: float = 0.02,
) -> float:
    """
    计算仓位大小

    Args:
        balance: 账户余额
        price: 当前价格
        risk_pct: 风险比例

    Returns:
        仓位数量
    """
    position_value = balance * risk_pct
    return position_value / price


def calculate_stop_loss(
    entry_price: float,
    side: str,
    atr: Optional[float] = None,
    risk_pct: float = 0.01,
) -> float:
    """
    计算止损价格

    Args:
        entry_price: 开仓价格
        side: 方向 long/short
        atr: ATR值 (可选)
        risk_pct: 风险比例

    Returns:
        止损价格
    """
    if atr:
        if side == "long":
            return entry_price - atr * 2
        else:
            return entry_price + atr * 2
    else:
        if side == "long":
            return entry_price * (1 - risk_pct)
        else:
            return entry_price * (1 + risk_pct)


def calculate_take_profit(
    entry_price: float,
    side: str,
    atr: Optional[float] = None,
    reward_pct: float = 0.02,
) -> float:
    """
    计算止盈价格

    Args:
        entry_price: 开仓价格
        side: 方向 long/short
        atr: ATR值 (可选)
        reward_pct: 止盈比例

    Returns:
        止盈价格
    """
    if atr:
        if side == "long":
            return entry_price + atr * 3
        else:
            return entry_price - atr * 3
    else:
        if side == "long":
            return entry_price * (1 + reward_pct)
        else:
            return entry_price * (1 - reward_pct)


def calculate_pnl(
    entry_price: float,
    current_price: float,
    side: str,
    amount: float,
) -> float:
    """
    计算盈亏

    Args:
        entry_price: 开仓价格
        current_price: 当前价格
        side: 方向 long/short
        amount: 数量

    Returns:
        盈亏金额
    """
    if side == "long":
        return (current_price - entry_price) * amount
    else:
        return (entry_price - current_price) * amount


def calculate_pnl_pct(
    entry_price: float,
    current_price: float,
    side: str,
) -> float:
    """
    计算盈亏比例

    Args:
        entry_price: 开仓价格
        current_price: 当前价格
        side: 方向 long/short

    Returns:
        盈亏比例
    """
    if entry_price == 0:
        return 0

    if side == "long":
        return (current_price - entry_price) / entry_price
    else:
        return (entry_price - current_price) / entry_price


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算 ATR (Average True Range)

    Args:
        df: 包含 high, low, close 的 DataFrame
        period: 周期

    Returns:
        ATR 值
    """
    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    return atr


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """
    计算 EMA (Exponential Moving Average)

    Args:
        series: 数据序列
        period: 周期

    Returns:
        EMA 值
    """
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """
    计算 SMA (Simple Moving Average)

    Args:
        series: 数据序列
        period: 周期

    Returns:
        SMA 值
    """
    return series.rolling(window=period).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    计算 RSI (Relative Strength Index)

    Args:
        series: 数据序列
        period: 周期

    Returns:
        RSI 值
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple:
    """
    计算布林带

    Args:
        series: 数据序列
        period: 周期
        std_dev: 标准差倍数

    Returns:
        (middle, upper, lower)
    """
    middle = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()

    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)

    return middle, upper, lower


def calculate_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple:
    """
    计算随机指标

    Args:
        df: 包含 high, low, close 的 DataFrame
        k_period: K周期
        d_period: D周期

    Returns:
        (%K, %D)
    """
    low_min = df['low'].rolling(window=k_period).min()
    high_max = df['high'].rolling(window=k_period).max()

    k = 100 * (df['close'] - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()

    return k, d
