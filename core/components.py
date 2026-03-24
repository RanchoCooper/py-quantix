"""
交易引擎组件模块
拆分 TradingEngine 的职责到多个专门的组件类
"""
import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger


def _run_async(coro):
    """
    安全运行异步函数

    如果已经在事件循环中，使用现有循环；否则创建新循环
    """
    try:
        loop = asyncio.get_running_loop()
        # 已经在循环中，异步调用
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # 没有运行中的循环，创建新循环
        return asyncio.run(coro)


class SignalProcessor:
    """
    信号处理器 - 负责评估策略和生成交易信号
    """

    def __init__(self, strategies: Dict[str, Any], client: Any):
        """
        初始化信号处理器

        Args:
            strategies: 策略字典 {symbol: strategy_instance}
            client: 交易所客户端
        """
        self.strategies = strategies
        self.client = client
        self.last_signals: Dict[str, Any] = {}

    def evaluate_strategy(self, symbol: str) -> Dict[str, Any]:
        """
        评估指定交易对的策略

        Args:
            symbol: 交易对符号

        Returns:
            策略信号字典
        """
        try:
            # 获取市场数据
            klines = _run_async(
                self.client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe="1h",
                    limit=100
                )
            )

            # 获取对应交易对的策略
            strategy = self.strategies.get(symbol)
            if not strategy:
                logger.error(f"未找到交易对 {symbol} 的策略")
                return {"action": "hold", "reason": f"未找到交易对 {symbol} 的策略"}

            # 评估策略
            signal = strategy.evaluate(klines)

            logger.info(f"交易对 {symbol} 的策略信号: {signal}")
            return signal

        except Exception as e:
            logger.error(f"评估交易对 {symbol} 的策略失败: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}

    def evaluate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """评估所有交易对的策略"""
        signals = {}
        for symbol in self.strategies.keys():
            signals[symbol] = self.evaluate_strategy(symbol)
        return signals

    def has_new_signal(self, symbol: str, signal: Dict[str, Any]) -> bool:
        """检查是否是新信号"""
        return signal != self.last_signals.get(symbol)

    def update_signal(self, symbol: str, signal: Dict[str, Any]) -> None:
        """更新最后信号"""
        self.last_signals[symbol] = signal


class TradeExecutor:
    """
    交易执行器 - 负责执行交易订单
    """

    def __init__(self, client: Any, config: Dict[str, Any]):
        """
        初始化交易执行器

        Args:
            client: 交易所客户端
            config: 配置字典
        """
        self.client = client
        self.config = config
        self.mode = "monitor"  # 默认监控模式

    def set_mode(self, mode: str) -> None:
        """设置运行模式"""
        self.mode = mode

    def get_position_size(self, symbol: str) -> float:
        """获取交易对的仓位大小"""
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
        """
        执行交易信号

        Args:
            symbol: 交易对符号
            signal: 交易信号

        Returns:
            执行是否成功
        """
        if signal.get('action') == 'hold':
            return True

        position_size = self.get_position_size(symbol)

        # 监控模式不执行交易
        if self.mode == "monitor":
            logger.info(f"[监控模式] 发现交易信号但不执行下单: {signal}")
            return True

        # 自动模式执行交易
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
        """下单"""
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


class PositionManager:
    """
    仓位管理器 - 负责管理持仓信息
    """

    def __init__(self):
        """初始化仓位管理器"""
        self.positions: Dict[str, Dict[str, Any]] = {}

    def update_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float
    ) -> None:
        """更新持仓信息"""
        self.positions[symbol] = {
            'side': side,
            'size': size,
            'entry_price': entry_price
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓信息"""
        return self.positions.get(symbol)

    def clear_position(self, symbol: str) -> None:
        """清除持仓信息"""
        if symbol in self.positions:
            del self.positions[symbol]

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取所有持仓"""
        return self.positions.copy()


class NotificationManager:
    """
    通知管理器 - 负责发送交易信号和系统通知
    """

    def __init__(self, notifiers: Dict[str, Any], config: Dict[str, Any]):
        """
        初始化通知管理器

        Args:
            notifiers: 通知器字典
            config: 配置字典
        """
        self.notifiers = notifiers
        self.config = config

    def send_signal_notification(
        self,
        symbol: str,
        signal: Dict[str, Any],
        position_size: float
    ) -> None:
        """发送交易信号通知"""
        # 获取信号输出配置
        signal_output = self.config.get(
            'signal_output',
            self.config.get('trading', {}).get('signal_output', ['console'])
        )
        if isinstance(signal_output, str):
            signal_output = [signal_output]

        message = (
            f"[信号输出] 交易对: {symbol}, "
            f"操作: {signal['action']}, "
            f"价格: {signal.get('price', 0)}, "
            f"原因: {signal.get('reason', '')}, "
            f"头寸大小: {position_size}"
        )

        for output in signal_output:
            if output == 'console':
                logger.info(message)
            elif output == 'dingtalk' and 'dingtalk' in self.notifiers:
                self.notifiers['dingtalk'].send_trade_notification(
                    symbol=symbol,
                    action=signal['action'],
                    price=signal.get('price', 0),
                    reason=signal.get('reason', ''),
                    position_size=position_size
                )
            elif output == 'feishu' and 'feishu' in self.notifiers:
                self.notifiers['feishu'].send_trade_notification(
                    symbol=symbol,
                    action=signal['action'],
                    price=signal.get('price', 0),
                    reason=signal.get('reason', ''),
                    position_size=position_size
                )

    def send_system_alert(self, title: str, message: str) -> None:
        """发送系统警报"""
        for channel, notifier in self.notifiers.items():
            try:
                notifier.send_system_alert(title, message)
            except Exception as e:
                logger.error(f"发送 {channel} 系统警报失败: {e}")
