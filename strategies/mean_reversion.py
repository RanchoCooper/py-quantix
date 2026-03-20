from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from strategies.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    基于布林带和RSI的均值回归策略

    该策略结合了布林带和相对强弱指数(RSI)来识别价格偏离均值的机会。
    当价格触及布林带下轨且RSI处于超卖区域时产生买入信号，
    当价格触及布林带上轨且RSI处于超买区域时产生卖出信号。
    """

    MIN_PERIOD = 30

    def __init__(self, **kwargs):
        """
        初始化均值回归策略

        Args:
            kwargs: 策略参数字典
                - period (int, optional): 计算移动平均线和标准差的周期. 默认为 20.
                - std_dev_multiplier (float, optional): 标准差乘数（布林带宽度）. 默认为 2.0.

        Attributes:
            period (int): 计算周期
            std_dev_multiplier (float): 标准差乘数

        Example:
            >>> strategy = MeanReversionStrategy(period=20, std_dev_multiplier=2.0)
            >>> logger.info("均值回归策略初始化成功")
        """
        self.period = kwargs.get('period', 20)
        self.std_dev_multiplier = kwargs.get('std_dev_multiplier', 2.0)
        logger.info(f"均值回归策略初始化，周期={self.period}，标准差乘数={self.std_dev_multiplier}")

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        为均值回归策略计算技术指标（布林带和RSI）

        Args:
            df: 包含K线数据的DataFrame

        Returns:
            pd.DataFrame: 包含计算指标的DataFrame
        """
        # 计算移动平均线和标准差
        df['ma'] = df['close'].rolling(window=self.period).mean()
        df['std'] = df['close'].rolling(window=self.period).std()

        # 计算布林带
        df['upper_band'] = df['ma'] + (df['std'] * self.std_dev_multiplier)
        df['lower_band'] = df['ma'] - (df['std'] * self.std_dev_multiplier)

        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基于均值回归指标生成买卖信号

        Args:
            df (pd.DataFrame): 包含计算指标的DataFrame

        Returns:
            Dict[str, Any]: 包含操作和元数据的信号字典，可能的键值：
                - action (str): 操作指令 ('buy', 'sell', 'hold')
                - reason (str): 信号产生的原因
                - target_price (float, optional): 目标价格
                - price (float, optional): 当前价格

        Signal Logic:
            买入信号：当价格低于下轨且RSI < 30（超卖）
            卖出信号：当价格高于上轨且RSI > 70（超买）
            持有信号：其他情况

        Example:
            >>> signal = strategy.generate_signals(df)
            >>> if signal['action'] == 'buy':
            ...     print(f"买入信号: {signal['reason']}")
        """
        if len(df) < self.period:
            return {"action": "hold", "reason": "数据不足"}

        current = df.iloc[-1]

        # 检查买入信号：价格低于下轨且RSI < 30（超卖）
        if (current['close'] < current['lower_band'] and
            current['rsi'] < 30):
            return {
                "action": "buy",
                "reason": "价格低于下轨且RSI超卖",
                "target_price": float(current['ma']),  # 目标价格回归到移动平均线
                "price": float(current['close'])
            }

        # 检查卖出信号：价格高于上轨且RSI > 70（超买）
        elif (current['close'] > current['upper_band'] and
              current['rsi'] > 70):
            return {
                "action": "sell",
                "reason": "价格高于上轨且RSI超买",
                "target_price": float(current['ma']),  # 目标价格回归到移动平均线
                "price": float(current['close'])
            }

        return {"action": "hold", "reason": "无明确信号"}
