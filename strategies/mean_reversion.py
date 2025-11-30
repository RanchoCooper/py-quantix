from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from utils.logger import setup_logger


class MeanReversionStrategy:
    """
    基于布林带和RSI的均值回归策略

    该策略结合了布林带和相对强弱指数(RSI)来识别价格偏离均值的机会。
    当价格触及布林带下轨且RSI处于超卖区域时产生买入信号，
    当价格触及布林带上轨且RSI处于超买区域时产生卖出信号。
    """

    def __init__(self, period: int = 20, std_dev_multiplier: float = 2.0):
        """
        初始化均值回归策略

        Args:
            period (int, optional): 计算移动平均线和标准差的周期. 默认为 20.
            std_dev_multiplier (float, optional): 标准差乘数（布林带宽度）. 默认为 2.0.

        Attributes:
            period (int): 计算周期
            std_dev_multiplier (float): 标准差乘数

        Example:
            >>> strategy = MeanReversionStrategy(period=20, std_dev_multiplier=2.0)
            >>> logger.info("均值回归策略初始化成功")
        """
        self.period = period
        self.std_dev_multiplier = std_dev_multiplier
        logger.info(f"均值回归策略初始化，周期={period}，标准差乘数={std_dev_multiplier}")

    def calculate_indicators(self, klines: List[List]) -> pd.DataFrame:
        """
        为均值回归策略计算技术指标（布林带和RSI）

        Args:
            klines (List[List]): 来自币安API的K线数据，每个元素包含：
                [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]

        Returns:
            pd.DataFrame: 包含计算指标的DataFrame，列包括：
                - timestamp: 开盘时间
                - open: 开盘价
                - high: 最高价
                - low: 最低价
                - close: 收盘价
                - volume: 成交量
                - ma: 移动平均线
                - upper_band: 布林带上轨
                - lower_band: 布林带下轨
                - rsi: 相对强弱指数

        Example:
            >>> klines = [[1617590400000, "57648.57", "57715.00", "57560.00", "57663.21", "305.94734000", ...]]
            >>> df = strategy.calculate_indicators(klines)
            >>> print(df[['close', 'ma', 'rsi']].tail(1))
                  close        ma    rsi
            0  57663.21  57500.15  45.32
        """
        # 将klines转换为DataFrame
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        # 转换为数值
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])

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

    def evaluate(self, klines: List[List]) -> Dict[str, Any]:
        """
        基于K线数据评估策略并生成交易信号

        Args:
            klines (List[List]): 来自币安API的K线数据

        Returns:
            Dict[str, Any]: 包含信号的评估结果

        Example:
            >>> signal = strategy.evaluate(klines)
            >>> print(signal['action'])
            hold
        """
        try:
            df = self.calculate_indicators(klines)
            signal = self.generate_signals(df)
            return signal
        except Exception as e:
            logger.error(f"评估均值回归策略时出错: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}


# 示例用法
if __name__ == "__main__":
    # 示例K线数据（实际应用中来自币安API）
    sample_klines = [
        [1617590400000, "57648.57", "57715.00", "57560.00", "57663.21", "305.94734000", 1617590699999, "17644864.26770240", 1234, "153.23582000", "8827865.18270240", "0"],
        # ... 更多K线数据
    ]

    strategy = MeanReversionStrategy(period=20, std_dev_multiplier=2.0)
    result = strategy.evaluate(sample_klines)
    print("策略结果:", result)
