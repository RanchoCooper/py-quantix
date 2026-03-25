"""
交易执行器
负责执行交易订单
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


class TradeExecutor:
    """交易执行器 - 负责执行交易订单"""

    def __init__(self, client: Any, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.mode = "monitor"

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def get_position_size(self, symbol: str) -> float:
        trading_symbols = self.config.get('trading', {}).get('symbols', [])

        if isinstance(trading_symbols, list):
            for item in trading_symbols:
                if isinstance(item, dict) and item.get('symbol') == symbol:
                    return item.get('position_size', 0.001)
        elif isinstance(trading_symbols, dict):
            symbol_config = trading_symbols.get(symbol, {})
            return symbol_config.get('position_size', 0.001)

        return 0.001

    def execute(self, symbol: str, signal: Dict[str, Any]) -> bool:
        if signal.get('action') == 'hold':
            return True

        position_size = self.get_position_size(symbol)

        if self.mode == "monitor":
            logger.info(f"[监控模式] 发现交易信号但不执行下单: {signal}")
            return True

        if self.mode == "auto":
            return self._place_order(symbol, signal, position_size)

        logger.warning(f"未知的运行模式: {self.mode}，默认不执行交易")
        return False

    def _place_order(
        self,
        symbol: str,
        signal: Dict[str, Any],
        position_size: float
    ) -> bool:
        try:
            VALID_ACTIONS = {'buy', 'sell'}
            action = signal.get('action', '').lower()
            if action not in VALID_ACTIONS:
                logger.error(f"Invalid action: {action}")
                return False
            if position_size <= 0:
                logger.error(f"Invalid position size: {position_size}")
                return False

            side = action.upper()

            order = _run_async(
                self.client.create_order(
                    symbol=symbol,
                    side=side.lower(),
                    order_type="market",
                    quantity=position_size
                )
            )

            logger.info(f"订单已下单: {order}")
            return True

        except Exception as e:
            logger.error(f"执行交易失败: {e}")
            return False
