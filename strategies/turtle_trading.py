"""
海龟交易策略
基于唐奇安通道突破和ATR的海龟交易系统
"""
from typing import Any, Dict

import pandas as pd
from loguru import logger

from strategies.base_strategy import (
    BaseStrategy,
    calculate_atr,
    calculate_donchian_channel,
)


class TurtleTradingStrategy(BaseStrategy):
    """
    海龟交易策略

    基于唐奇安通道突破和ATR的海龟交易系统：
    1. 入场信号：价格突破过去N天的最高点（上轨）时买入，跌破过去N天的最低点（下轨）时卖出
    2. 出场信号：价格反向突破过去M天的最低点时卖出，突破过去M天的最高点时买入
    3. 止损：基于ATR的波动性止损
    4. 头寸规模：根据ATR调整头寸规模
    """

    MIN_PERIOD = 20

    def __init__(self, **kwargs):
        """
        初始化海龟交易策略

        Args:
            kwargs: 策略参数字典
                - entry_period: 入场突破计算周期（唐奇安通道），默认为20
                - exit_period: 出场突破计算周期（唐奇安通道），默认为10
                - atr_period: ATR计算周期，默认为20
                - risk_per_trade: 每次交易风险比例，默认为 0.01 (1%)
                - account_size: 账户规模，默认为 10000
                - risk_reward_ratio: 盈亏比，默认为 2.0
        """
        super().__init__(**kwargs)
        self.entry_period = kwargs.get('entry_period', 20)
        self.exit_period = kwargs.get('exit_period', 10)
        self.atr_period = kwargs.get('atr_period', 20)
        self.risk_per_trade = kwargs.get('risk_per_trade', 0.01)
        self.account_size = kwargs.get('account_size', 10000)
        self.risk_reward_ratio = kwargs.get('risk_reward_ratio', 2.0)

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
        df = df.copy()

        # 需要有足够的数据进行所有计算
        required_length = max(self.entry_period, self.exit_period, self.atr_period) + 1
        if len(df) < required_length:
            return df

        # 计算入场唐奇安通道
        entry_df = calculate_donchian_channel(df, period=self.entry_period)
        df['entry_upper'] = entry_df['upper']
        df['entry_lower'] = entry_df['lower']

        # 计算 ATR
        df = calculate_atr(df, period=self.atr_period, drop_columns=False)

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
        required_length = max(self.entry_period, self.exit_period, self.atr_period) + 1
        if len(df) < required_length:
            return {"action": "hold", "reason": "数据不足"}

        # 检查必要字段
        required_cols = ['entry_upper', 'entry_lower', 'atr']
        if not all(col in df.columns for col in required_cols):
            return {"action": "hold", "reason": "指标计算不完整"}

        current = df.iloc[-1]

        # 检查是否有 NaN
        if (pd.isna(current.get('entry_upper')) or
            pd.isna(current.get('entry_lower')) or
            pd.isna(current.get('atr'))):
            return {"action": "hold", "reason": "指标数据不完整"}

        current_price = current['close']
        entry_upper = current['entry_upper']
        entry_lower = current['entry_lower']
        atr = current['atr']

        # 获取前一个周期的数据用于趋势判断
        if len(df) >= 2:
            previous = df.iloc[-2]
            prev_entry_upper = previous.get('entry_upper')
            prev_entry_lower = previous.get('entry_lower')
            prev_close = previous.get('close')
        else:
            return {"action": "hold", "reason": "数据不足"}

        # 检查是否有有效的前值
        if (prev_entry_upper is None or prev_entry_lower is None or
            prev_close is None or pd.isna(prev_entry_upper) or
            pd.isna(prev_entry_lower) or pd.isna(prev_close)):
            return {"action": "hold", "reason": "指标数据不完整"}

        # 多头信号：价格向上突破上轨
        long_signal = (
            current_price > entry_upper and
            prev_close <= prev_entry_upper
        )

        # 空头信号：价格向下跌破下轨
        short_signal = (
            current_price < entry_lower and
            prev_close >= prev_entry_lower
        )

        # 计算仓位规模
        risk_amount = self.account_size * self.risk_per_trade
        position_size = round(risk_amount / atr, 3) if atr > 0 else 0

        # 生成信号
        if long_signal:
            stop_loss = current_price - (atr * self.risk_reward_ratio)
            take_profit = current_price + (atr * self.risk_reward_ratio)

            return {
                "action": "buy",
                "reason": f"突破唐奇安通道上轨({entry_upper:.2f}) - 多头信号",
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
            stop_loss = current_price + (atr * self.risk_reward_ratio)
            take_profit = current_price - (atr * self.risk_reward_ratio)

            return {
                "action": "sell",
                "reason": f"跌破唐奇安通道下轨({entry_lower:.2f}) - 空头信号",
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
