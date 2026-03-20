"""
趋势跟踪策略
基于移动平均线和动量的趋势跟踪策略
"""
from typing import Any, Dict

import pandas as pd
from loguru import logger

from strategies.base_strategy import BaseStrategy, calculate_atr, calculate_ma, calculate_momentum


class TrendFollowingStrategy(BaseStrategy):
    """
    基于移动平均线和动量的趋势跟踪策略

    策略逻辑：
    - 入场信号：短期均线向上穿越长期均线且动量为正
    - 出场信号：短期均线向下穿越长期均线且动量为负
    - 止损止盈：基于 ATR 计算
    """

    MIN_PERIOD = 25

    def __init__(self, **kwargs):
        """
        初始化趋势跟踪策略

        Args:
            kwargs: 策略参数字典
                - period: 计算移动平均线的周期，默认为14
                - multiplier: 止损和止盈水平的乘数，默认为2.0
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
        df = df.copy()

        # 计算移动平均线
        ma_df = calculate_ma(df, periods=[self.period // 2, self.period])
        df['ma_short'] = ma_df[f'ma{self.period // 2}']
        df['ma_long'] = ma_df[f'ma{self.period}']

        # 计算 ATR
        df = calculate_atr(df, period=self.period)

        # 计算动量
        df = calculate_momentum(df, period=self.period)

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

        # 检查必要字段
        required_cols = ['ma_short', 'ma_long', 'atr', 'momentum']
        if not all(col in df.columns for col in required_cols):
            return {"action": "hold", "reason": "指标计算不完整"}

        current = df.iloc[-1]

        # 检查是否有 NaN
        if pd.isna(current['ma_short']) or pd.isna(current['ma_long']):
            return {"action": "hold", "reason": "指标数据不完整"}

        if len(df) < 2:
            return {"action": "hold", "reason": "数据不足"}

        previous = df.iloc[-2]

        # 检查买入信号：短期均线向上穿越长期均线且动量为正
        if (current['ma_short'] > current['ma_long'] and
            previous['ma_short'] <= previous['ma_long'] and
            current.get('momentum', 0) > 0):
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
              current.get('momentum', 0) < 0):
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
