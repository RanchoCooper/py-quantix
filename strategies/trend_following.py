from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from strategies.base_strategy import BaseStrategy


class TrendFollowingStrategy(BaseStrategy):
    """
    基于移动平均线和动量的趋势跟踪策略
    """

    MIN_PERIOD = 25

    def __init__(self, **kwargs):
        """
        初始化趋势跟踪策略

        Args:
            kwargs: 策略参数字典
                - period (int, optional): 计算移动平均线的周期，默认为14
                - multiplier (float, optional): 止损和止盈水平的乘数，默认为2.0
        """
        self.period = kwargs.get('period', 14)
        self.multiplier = kwargs.get('multiplier', 2.0)
        logger.info(f"趋势跟踪策略初始化，周期={self.period}，乘数={self.multiplier}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为趋势跟踪策略计算技术指标

        Args:
            df: 包含K线数据的DataFrame

        Returns:
            包含计算指标的DataFrame
        """
        # 计算移动平均线
        df['ma_short'] = df['close'].rolling(window=self.period//2).mean()
        df['ma_long'] = df['close'].rolling(window=self.period).mean()

        # 计算ATR(平均真实波幅)用于波动率
        df['tr0'] = abs(df["high"] - df["low"])
        df['tr1'] = abs(df["high"] - df["close"].shift())
        df['tr2'] = abs(df["low"] - df["close"].shift())
        df["tr"] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=self.period).mean()

        # 计算动量
        df['momentum'] = df['close'] - df['close'].shift(self.period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基于趋势跟踪指标生成买卖信号

        Args:
            df: 包含计算指标的DataFrame

        Returns:
            包含操作和元数据的信号字典
        """
        if len(df) < self.period:
            return {"action": "hold", "reason": "数据不足"}

        current = df.iloc[-1]
        previous = df.iloc[-2]

        # 检查买入信号：短期均线向上穿越长期均线且动量为正
        if (current['ma_short'] > current['ma_long'] and
            previous['ma_short'] <= previous['ma_long'] and
            current['momentum'] > 0):
            stop_loss = current['close'] - (current['atr'] * self.multiplier)
            take_profit = current['close'] + (current['atr'] * self.multiplier)
            return {
                "action": "buy",
                "reason": "均线交叉且动量为正",
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "price": float(current['close'])
            }

        # 检查卖出信号：短期均线向下穿越长期均线且动量为负
        elif (current['ma_short'] < current['ma_long'] and
              previous['ma_short'] >= previous['ma_long'] and
              current['momentum'] < 0):
            stop_loss = current['close'] + (current['atr'] * self.multiplier)
            take_profit = current['close'] - (current['atr'] * self.multiplier)
            return {
                "action": "sell",
                "reason": "均线交叉且动量为负",
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "price": float(current['close'])
            }

        return {"action": "hold", "reason": "无明确信号"}
