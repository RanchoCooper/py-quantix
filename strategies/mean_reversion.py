"""
均值回归策略
基于布林带和RSI的均值回归策略
"""
from typing import Any, Dict

import pandas as pd
from loguru import logger

from strategies.base_strategy import (
    BaseStrategy,
    calculate_bollinger_bands,
    calculate_rsi,
)


class MeanReversionStrategy(BaseStrategy):
    """
    基于布林带和RSI的均值回归策略

    策略逻辑：
    - 入场信号：当价格触及布林带下轨且RSI处于超卖区域（<30）时买入
    - 出场信号：当价格触及布林带上轨且RSI处于超买区域（>70）时卖出

    核心假设：价格会回归到均值（移动平均线）
    """

    MIN_PERIOD = 30

    def __init__(self, **kwargs):
        """
        初始化均值回归策略

        Args:
            kwargs: 策略参数字典
                - period: 计算移动平均线和标准差的周期，默认为 20
                - std_dev_multiplier: 标准差乘数（布林带宽度），默认为 2.0
                - rsi_period: RSI 计算周期，默认为 14
                - rsi_oversold: RSI 超卖阈值，默认为 30
                - rsi_overbought: RSI 超买阈值，默认为 70
        """
        self.period = kwargs.get('period', 20)
        self.std_dev_multiplier = kwargs.get('std_dev_multiplier', 2.0)
        self.rsi_period = kwargs.get('rsi_period', 14)
        self.rsi_oversold = kwargs.get('rsi_oversold', 30)
        self.rsi_overbought = kwargs.get('rsi_overbought', 70)
        logger.info(
            f"均值回归策略初始化，周期={self.period}，"
            f"标准差乘数={self.std_dev_multiplier}，"
            f"RSI周期={self.rsi_period}"
        )

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为均值回归策略计算技术指标（布林带和RSI）

        Args:
            df: 包含K线数据的DataFrame

        Returns:
            包含计算指标的DataFrame
        """
        df = df.copy()

        # 计算布林带
        df = calculate_bollinger_bands(
            df,
            period=self.period,
            std_multiplier=self.std_dev_multiplier
        )

        # 计算 RSI
        df = calculate_rsi(df, period=self.rsi_period)

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基于均值回归指标生成买卖信号

        Args:
            df: 包含计算指标的DataFrame

        Returns:
            包含操作和元数据的信号字典:
                - action: 操作指令 ('buy', 'sell', 'hold')
                - reason: 信号产生的原因
                - target_price: 目标价格
                - price: 当前价格

        信号逻辑:
            - 买入信号：价格低于下轨且RSI < rsi_oversold（超卖）
            - 卖出信号：价格高于上轨且RSI > rsi_overbought（超买）
            - 持有信号：其他情况
        """
        if len(df) < self.period:
            return {"action": "hold", "reason": "数据不足"}

        # 检查必要字段
        required_cols = ['upper_band', 'lower_band', 'rsi']
        if not all(col in df.columns for col in required_cols):
            return {"action": "hold", "reason": "指标计算不完整"}

        current = df.iloc[-1]

        # 检查是否有 NaN
        if pd.isna(current.get('upper_band')) or pd.isna(current.get('rsi')):
            return {"action": "hold", "reason": "指标数据不完整"}

        close = current['close']
        upper_band = current['upper_band']
        lower_band = current['lower_band']
        rsi = current['rsi']
        ma = current.get('bb_ma', close)  # 布林带中轨作为均值

        # 买入信号：价格低于下轨且RSI超卖
        if close < lower_band and rsi < self.rsi_oversold:
            return {
                "action": "buy",
                "reason": f"价格低于下轨({lower_band:.2f})且RSI超卖({rsi:.1f})",
                "target_price": float(ma) if not pd.isna(ma) else float(close),
                "price": float(close)
            }

        # 卖出信号：价格高于上轨且RSI超买
        elif close > upper_band and rsi > self.rsi_overbought:
            return {
                "action": "sell",
                "reason": f"价格高于上轨({upper_band:.2f})且RSI超买({rsi:.1f})",
                "target_price": float(ma) if not pd.isna(ma) else float(close),
                "price": float(close)
            }

        return {"action": "hold", "reason": "无明确信号"}
