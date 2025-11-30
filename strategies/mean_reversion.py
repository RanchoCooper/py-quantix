from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from loguru import logger

from utils.logger import setup_logger


class MeanReversionStrategy:
    """
    基于布林带和RSI的均值回归策略
    """

    def __init__(self, period: int = 20, std_dev_multiplier: float = 2.0):
        """
        初始化均值回归策略

        Args:
            period: 计算移动平均线和标准差的周期
            std_dev_multiplier: 标准差乘数（布林带宽度）
        """
        self.period = period
        self.std_dev_multiplier = std_dev_multiplier
        logger.info(f"均值回归策略初始化，周期={period}，标准差乘数={std_dev_multiplier}")

    def calculate_indicators(self, klines: List[List]) -> pd.DataFrame:
        """
        为均值回归策略计算技术指标

        Args:
            klines: 来自币安API的K线数据

        Returns:
            包含计算指标的DataFrame
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
            df: 包含计算指标的DataFrame

        Returns:
            包含操作和元数据的信号字典
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
        基于K线数据评估策略

        Args:
            klines: 来自币安API的K线数据

        Returns:
            包含信号的评估结果
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
