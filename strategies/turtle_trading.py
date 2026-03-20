from typing import Any, Dict, List

import pandas as pd
from loguru import logger

from strategies.base_strategy import BaseStrategy


class TurtleTradingStrategy(BaseStrategy):
    """
    海龟交易策略

    基于唐奇安通道突破和ATR的海龟交易系统：
    1. 入场信号：价格突破过去N天的最高点（上轨）时买入，跌破过去N天的最低点（下轨）时卖出
    2. 出场信号：价格反向突破过去M天的最低点（上轨）时卖出，突破过去M天的最高点（下轨）时买入
    3. 止损：基于ATR的波动性止损
    4. 头寸规模：根据ATR调整头寸规模
    """

    MIN_PERIOD = 20

    def __init__(self, **kwargs):
        """
        初始化海龟交易策略

        Args:
            kwargs: 策略参数字典
                - entry_period (int, optional): 入场突破计算周期（唐奇安通道），默认为20
                - exit_period (int, optional): 出场突破计算周期（唐奇安通道），默认为10
                - atr_period (int, optional): ATR计算周期，默认为20
        """
        super().__init__(**kwargs)
        self.entry_period = kwargs.get('entry_period', 20)
        self.exit_period = kwargs.get('exit_period', 10)
        self.atr_period = kwargs.get('atr_period', 20)
        logger.info(
            f"海龟交易策略初始化，入场周期={self.entry_period}，"
            f"出场周期={self.exit_period}，ATR周期={self.atr_period}"
        )

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算海龟交易策略所需的技术指标

        Args:
            df: 包含K线数据的DataFrame

        Returns:
            包含所有技术指标的DataFrame
        """
        # 需要有足够的数据进行所有计算
        required_length = max(self.entry_period, self.exit_period, self.atr_period) + 1
        if len(df) < required_length:
            return df

        # 计算唐奇安通道（入场）
        df['entry_upper'] = df['high'].rolling(window=self.entry_period).max()
        df['entry_lower'] = df['low'].rolling(window=self.entry_period).min()

        # 计算唐奇安通道（出场）
        df['exit_upper'] = df['high'].rolling(window=self.exit_period).max()
        df['exit_lower'] = df['low'].rolling(window=self.exit_period).min()

        # 计算ATR用于仓位管理
        df['tr0'] = abs(df["high"] - df["low"])
        df['tr1'] = abs(df["high"] - df["close"].shift())
        df['tr2'] = abs(df["low"] - df["close"].shift())
        df["tr"] = df[['tr0', 'tr1', 'tr2']].max(axis=1)
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()

        return df

    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基于技术指标生成交易信号

        Args:
            df: 包含技术指标的DataFrame

        Returns:
            包含信号的评估结果
        """
        # 检查是否有足够的指标数据
        if len(df) < max(self.entry_period, self.exit_period, self.atr_period) + 1:
            return {"action": "hold", "reason": "数据不足"}

        current = df.iloc[-1]

        # 检查是否有NaN值
        if pd.isna(current['entry_upper']) or pd.isna(current['entry_lower']) or pd.isna(current['atr']):
            return {"action": "hold", "reason": "指标数据不完整"}

        current_price = current['close']
        entry_upper = current['entry_upper']
        entry_lower = current['entry_lower']
        atr = current['atr']

        # 获取前一个周期的数据用于趋势判断
        if len(df) >= 2:
            previous = df.iloc[-2]
            prev_entry_upper = previous['entry_upper']
            prev_entry_lower = previous['entry_lower']
        else:
            prev_entry_upper = prev_entry_lower = None

        # 根据通道突破确定市场方向
        # 如果价格突破上轨，为看涨信号
        # 如果价格跌破下轨，为看跌信号
        long_signal = (
            entry_upper is not None and
            current_price > entry_upper and
            prev_entry_upper is not None and
            previous['close'] <= prev_entry_upper
        )

        short_signal = (
            entry_lower is not None and
            current_price < entry_lower and
            prev_entry_lower is not None and
            previous['close'] >= prev_entry_lower
        )

        # 基于ATR的仓位管理（每次交易风险账户的1%）
        # 使用固定账户规模作为示例
        account_size = 10000  # 美元
        risk_per_trade = account_size * 0.01  # 每次交易风险1%

        # 计算仓位规模：风险金额 / (ATR * 合约规模)
        # 对于合约，我们简化直接使用ATR
        position_size = risk_per_trade / atr if atr > 0 else 0
        position_size = round(position_size, 3)  # 四舍五入到小数点后3位

        # 生成信号
        if long_signal:
            # 基于ATR计算止损
            stop_loss = current_price - (2 * atr)
            take_profit = current_price + (2 * atr)  # 简单的2:1盈亏比

            return {
                "action": "buy",
                "reason": "突破唐奇安通道上轨 - 多头信号",
                "price": float(current_price),
                "position_size": position_size,
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "indicators": {
                    "entry_upper": float(entry_upper),
                    "atr": float(atr)
                }
            }
        elif short_signal:
            # 基于ATR计算止损
            stop_loss = current_price + (2 * atr)
            take_profit = current_price - (2 * atr)  # 简单的2:1盈亏比

            return {
                "action": "sell",
                "reason": "跌破唐奇安通道下轨 - 空头信号",
                "price": float(current_price),
                "position_size": position_size,
                "stop_loss": float(stop_loss),
                "take_profit": float(take_profit),
                "indicators": {
                    "entry_lower": float(entry_lower),
                    "atr": float(atr)
                }
            }
        else:
            return {"action": "hold", "reason": "无明显突破信号"}
