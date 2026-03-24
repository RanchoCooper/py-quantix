"""
技术指标计算模块
提供公共的技术指标计算函数
"""
from typing import Dict

import pandas as pd


def calculate_atr(
    df: pd.DataFrame,
    period: int = 14,
    drop_columns: bool = True
) -> pd.DataFrame:
    """
    计算平均真实波幅 (Average True Range, ATR)

    ATR 是衡量市场波动性的指标，由 J. Welles Wilder Jr. 创建。
    它考虑了三种价格波动：当日高低差、前一日收盘价与当日最高价之差、
    前一日收盘价与当日最低价之差。

    Args:
        df: 包含 high, low, close 列的 DataFrame
        period: ATR 计算周期
        drop_columns: 是否删除中间计算列

    Returns:
        包含 ATR 指标的 DataFrame
    """
    df = df.copy()

    # 计算真实波幅 (True Range)
    df['tr0'] = df['high'] - df['low']
    df['tr1'] = abs(df['high'] - df['close'].shift(1))
    df['tr2'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

    # 计算 ATR
    df['atr'] = df['tr'].rolling(window=period).mean()

    if drop_columns:
        # 只删除我们创建的中间列
        for col in ['tr0', 'tr1', 'tr2', 'tr']:
            if col in df.columns:
                df = df.drop(columns=[col])

    return df


def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_multiplier: float = 2.0,
    column: str = 'close',
    drop_columns: bool = True
) -> pd.DataFrame:
    """
    计算布林带 (Bollinger Bands)

    布林带由中轨（移动平均线）和上下两条轨道组成，
    用于衡量价格的相对高低和波动性。

    Args:
        df: 包含 close 列的 DataFrame
        period: 移动平均线周期
        std_multiplier: 标准差乘数
        column: 计算的列名
        drop_columns: 是否删除中间计算列

    Returns:
        包含布林带的 DataFrame (ma, upper_band, lower_band)
    """
    df = df.copy()

    # 计算移动平均线和标准差
    df['bb_ma'] = df[column].rolling(window=period).mean()
    df['bb_std'] = df[column].rolling(window=period).std()

    # 计算布林带
    df['upper_band'] = df['bb_ma'] + (df['bb_std'] * std_multiplier)
    df['lower_band'] = df['bb_ma'] - (df['bb_std'] * std_multiplier)

    if drop_columns:
        df = df.drop(columns=['bb_ma', 'bb_std'])

    return df


def calculate_rsi(
    df: pd.DataFrame,
    period: int = 14,
    column: str = 'close',
    drop_columns: bool = True
) -> pd.DataFrame:
    """
    计算相对强弱指数 (Relative Strength Index, RSI)

    RSI 是衡量价格变动速度和幅度的动量指标，
    值域为 0-100，通常用于判断超买超卖状态。

    Args:
        df: 包含 close 列的 DataFrame
        period: RSI 计算周期
        column: 计算的列名
        drop_columns: 是否删除中间计算列

    Returns:
        包含 RSI 的 DataFrame
    """
    df = df.copy()

    # 计算价格变化
    delta = df[column].diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder 平滑 RSI
    # 第一值使用 SMA，后续使用 (prev * (period-1) + current) / period
    avg_gain = pd.Series(index=df.index, dtype=float)
    avg_loss = pd.Series(index=df.index, dtype=float)

    # 初始化第一个值
    avg_gain.iloc[period - 1] = gain.iloc[:period].mean()
    avg_loss.iloc[period - 1] = loss.iloc[:period].mean()

    # Wilder 平滑
    for i in range(period, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    # 计算 RS 和 RSI
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].clip(0, 100)


    return df


def calculate_ma(
    df: pd.DataFrame,
    periods: list = None,
    column: str = 'close'
) -> pd.DataFrame:
    """
    计算移动平均线

    Args:
        df: 包含 close 列的 DataFrame
        periods: MA 周期列表，如 [5, 10, 20]
        column: 计算的列名

    Returns:
        包含 MA 的 DataFrame
    """
    df = df.copy()

    if periods is None:
        periods = [5, 10, 20]

    for period in periods:
        df[f'ma{period}'] = df[column].rolling(window=period).mean()

    return df


def calculate_momentum(
    df: pd.DataFrame,
    period: int = 14,
    column: str = 'close'
) -> pd.DataFrame:
    """
    计算动量指标

    动量是当前价格与 N 天前价格的差值，用于衡量价格变化的速率。

    Args:
        df: 包含 close 列的 DataFrame
        period: 动量计算周期
        column: 计算的列名

    Returns:
        包含动量的 DataFrame
    """
    df = df.copy()
    df['momentum'] = df[column] - df[column].shift(period)
    return df


def calculate_donchian_channel(
    df: pd.DataFrame,
    period: int = 20
) -> pd.DataFrame:
    """
    计算唐奇安通道 (Donchian Channel)

    唐奇安通道是基于价格突破的趋势跟踪指标，
    常用于海龟交易策略。

    Args:
        df: 包含 high, low 列的 DataFrame
        period: 通道计算周期

    Returns:
        包含唐奇安通道的 DataFrame (upper, lower)
    """
    df = df.copy()

    df['upper'] = df['high'].rolling(window=period).max()
    df['lower'] = df['low'].rolling(window=period).min()

    return df


def calculate_all_indicators(
    df: pd.DataFrame,
    ma_periods: list = None,
    rsi_period: int = 14,
    atr_period: int = 14,
    bb_period: int = 20,
    bb_std: float = 2.0
) -> pd.DataFrame:
    """
    计算所有常用技术指标

    Args:
        df: 原始 K 线数据 DataFrame
        ma_periods: 移动平均线周期列表
        rsi_period: RSI 周期
        atr_period: ATR 周期
        bb_period: 布林带周期
        bb_std: 布林带标准差乘数

    Returns:
        包含所有指标的 DataFrame
    """
    if ma_periods is None:
        ma_periods = [5, 10, 20, 50]

    df = df.copy()

    # 计算移动平均线
    df = calculate_ma(df, periods=ma_periods)

    # 计算 RSI
    df = calculate_rsi(df, period=rsi_period)

    # 计算 ATR
    df = calculate_atr(df, period=atr_period)

    # 计算布林带
    df = calculate_bollinger_bands(df, period=bb_period, std_multiplier=bb_std)

    # 计算动量
    df = calculate_momentum(df, period=ma_periods[0])

    # 计算唐奇安通道
    df = calculate_donchian_channel(df, period=ma_periods[1])

    return df
