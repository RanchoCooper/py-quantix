from typing import Any, Dict, List

from loguru import logger


class TurtleTradingStrategy:
    """
    基于突破系统的海龟交易策略
    """

    def __init__(self, entry_period: int = 20, exit_period: int = 10, atr_period: int = 20):
        """
        初始化海龟交易策略

        Args:
            entry_period: 入场突破计算周期（唐奇安通道）
            exit_period: 出场突破计算周期（唐奇安通道）
            atr_period: ATR计算周期
        """
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
        logger.info(
            f"海龟交易策略初始化，入场周期={entry_period}，"
            f"出场周期={exit_period}，ATR周期={atr_period}"
        )

    def _calculate_donchian_channels(self, highs: List[float], lows: List[float], period: int) -> tuple:
        """
        计算唐奇安通道

        Args:
            highs: 最高价列表
            lows: 最低价列表
            period: 计算周期

        Returns:
            (上轨, 下轨)元组
        """
        upper_channel = max(highs[-period:]) if len(highs) >= period else None
        lower_channel = min(lows[-period:]) if len(lows) >= period else None
        return upper_channel, lower_channel

    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int) -> float:
        """
        计算平均真实波幅(ATR)

        Args:
            highs: 最高价列表
            lows: 最低价列表
            closes: 收盘价列表
            period: 计算周期

        Returns:
            ATR值
        """
        if len(closes) < period + 1:
            return 0

        tr_list = []
        for i in range(len(closes) - period, len(closes)):
            high = highs[i]
            low = lows[i]
            prev_close = closes[i - 1] if i > 0 else closes[i]

            tr = max(
                high - low,  # 当前最高 - 当前最低
                abs(high - prev_close),  # 绝对值(当前最高 - 上一收盘)
                abs(low - prev_close)  # 绝对值(当前最低 - 上一收盘)
            )
            tr_list.append(tr)

        return sum(tr_list) / len(tr_list) if tr_list else 0

    def evaluate(self, klines: List[List]) -> Dict[str, Any]:
        """
        基于K线数据评估策略

        Args:
            klines: 来自币安API的K线数据

        Returns:
            包含信号的评估结果
        """
        try:
            # 提取价格数据
            highs = [float(kline[2]) for kline in klines]
            lows = [float(kline[3]) for kline in klines]
            closes = [float(kline[4]) for kline in klines]

            # 需要有足够的数据进行所有计算
            required_length = max(self.entry_period, self.exit_period, self.atr_period) + 1
            if len(closes) < required_length:
                return {"action": "hold", "reason": "数据不足"}

            current_price = closes[-1]

            # 计算入场和出场通道
            entry_upper, entry_lower = self._calculate_donchian_channels(highs, lows, self.entry_period)
            exit_upper, exit_lower = self._calculate_donchian_channels(highs, lows, self.exit_period)

            # 计算ATR用于仓位管理
            atr = self._calculate_atr(highs, lows, closes, self.atr_period)

            # 获取之前的通道用于趋势判断
            if len(highs) >= self.entry_period + 1:
                prev_entry_upper, prev_entry_lower = self._calculate_donchian_channels(
                    highs[:-1], lows[:-1], self.entry_period
                )
            else:
                prev_entry_upper, prev_entry_lower = None, None

            # 根据通道突破确定市场方向
            # 如果价格突破上轨，为看涨信号
            # 如果价格跌破下轨，为看跌信号
            long_signal = (
                entry_upper is not None and
                current_price > entry_upper and
                prev_entry_upper is not None and
                current_price > prev_entry_upper
            )

            short_signal = (
                entry_lower is not None and
                current_price < entry_lower and
                prev_entry_lower is not None and
                current_price < prev_entry_lower
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
                    "price": current_price,
                    "position_size": position_size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "indicators": {
                        "entry_upper": entry_upper,
                        "atr": atr
                    }
                }
            elif short_signal:
                # 基于ATR计算止损
                stop_loss = current_price + (2 * atr)
                take_profit = current_price - (2 * atr)  # 简单的2:1盈亏比

                return {
                    "action": "sell",
                    "reason": "跌破唐奇安通道下轨 - 空头信号",
                    "price": current_price,
                    "position_size": position_size,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "indicators": {
                        "entry_lower": entry_lower,
                        "atr": atr
                    }
                }
            else:
                return {"action": "hold", "reason": "无明显突破信号"}

        except Exception as e:
            logger.error(f"评估海龟交易策略时出错: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}


# 示例用法
if __name__ == "__main__":
    # 示例K线数据（实际应用中来自币安API）
    sample_klines = [
        [1617590400000, "57648.57", "57715.00", "57560.00", "57663.21", "305.94734000", 1617590699999, "17644864.26770240", 1234, "153.23582000", "8827865.18270240", "0"],
        # ... 更多K线数据
    ]

    strategy = TurtleTradingStrategy(entry_period=20, exit_period=10, atr_period=20)
    result = strategy.evaluate(sample_klines)
    print("策略结果:", result)
