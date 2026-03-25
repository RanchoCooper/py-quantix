"""
信号处理器
负责评估策略和生成交易信号
"""
import asyncio
from typing import Any, Dict

from loguru import logger


def _run_async(coro):
    """安全运行异步函数"""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        return asyncio.run(coro)


class SignalProcessor:
    """信号处理器 - 负责评估策略和生成交易信号"""

    def __init__(self, strategies: Dict[str, Any], client: Any):
        self.strategies = strategies
        self.client = client
        self.last_signals: Dict[str, Any] = {}

    def evaluate_strategy(self, symbol: str) -> Dict[str, Any]:
        try:
            klines = _run_async(
                self.client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe="1h",
                    limit=100
                )
            )

            strategy = self.strategies.get(symbol)
            if not strategy:
                logger.error(f"未找到交易对 {symbol} 的策略")
                return {"action": "hold", "reason": f"未找到交易对 {symbol} 的策略"}

            signal = strategy.evaluate(klines)
            logger.info(f"交易对 {symbol} 的策略信号: {signal}")
            return signal

        except Exception as e:
            logger.error(f"评估交易对 {symbol} 的策略失败: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}

    def evaluate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        signals = {}
        for symbol in self.strategies.keys():
            signals[symbol] = self.evaluate_strategy(symbol)
        return signals

    def has_new_signal(self, symbol: str, signal: Dict[str, Any]) -> bool:
        return signal != self.last_signals.get(symbol)

    def update_signal(self, symbol: str, signal: Dict[str, Any]) -> None:
        self.last_signals[symbol] = signal
