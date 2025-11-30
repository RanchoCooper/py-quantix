from typing import Any, Dict, List

import pandas as pd
from loguru import logger


class TrendFollowingStrategy:
    """
    基于移动平均线和动量的趋势跟踪策略
    """

    def __init__(self, period: int = 14, multiplier: float = 2.0):
        """
        初始化趋势跟踪策略

        Args:
            period: 计算移动平均线的周期
            multiplier: 止损和止盈水平的乘数
        """
        self.period = period
        self.multiplier = multiplier
        logger.info(f"趋势跟踪策略初始化，周期={period}，乘数={multiplier}")

    def calculate_indicators(self, klines: List[List]) -> pd.DataFrame:
        """
        为趋势跟踪策略计算技术指标

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
            logger.error(f"评估趋势跟踪策略时出错: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}


# 示例用法
if __name__ == "__main__":
    # 示例K线数据（实际应用中来自币安API）
    sample_klines = [
        [1617590400000, "57648.57", "57715.00", "57560.00", "57663.21", "305.94734000", 1617590699999, "17644864.26770240", 1234, "153.23582000", "8827865.18270240", "0"],
        # ... 更多K线数据
    ]

    strategy = TrendFollowingStrategy(period=14, multiplier=2.0)
    result = strategy.evaluate(sample_klines)
    print("策略结果:", result)
