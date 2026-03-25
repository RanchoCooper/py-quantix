"""
通知管理器
负责发送交易信号和系统通知
"""
from typing import Any, Dict

from loguru import logger


class NotificationManager:
    """通知管理器 - 负责发送交易信号和系统通知"""

    def __init__(self, notifiers: Dict[str, Any], config: Dict[str, Any]):
        self.notifiers = notifiers
        self.config = config

    def send_signal_notification(
        self,
        symbol: str,
        signal: Dict[str, Any],
        position_size: float
    ) -> None:
        """发送交易信号通知"""
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
