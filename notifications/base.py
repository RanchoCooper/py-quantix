# -*- coding: utf-8 -*-
"""
通知器基类
定义通用通知方法和接口
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseNotifier(ABC):
    """
    通知器基类

    定义通用的交易通知和系统警报方法，
    子类只需实现 _send_message 方法
    """

    @abstractmethod
    def _send_message(self, payload: Dict[str, Any]) -> bool:
        """
        发送消息到 webhook

        Args:
            payload: 消息载荷

        Returns:
            表示成功与否的布尔值
        """
        pass

    def send_trade_notification(
        self,
        symbol: str,
        action: str,
        price: float,
        reason: str = "",
        position_size: float = 0.0
    ) -> bool:
        """
        发送交易通知

        Args:
            symbol: 交易对符号
            action: 交易操作（买入/卖出）
            price: 执行价格
            reason: 交易原因
            position_size: 仓位大小

        Returns:
            表示成功与否的布尔值
        """
        content = "🚨 交易警报 🚨\n"
        content += f"交易对: {symbol}\n"
        content += f"操作: {action.upper()}\n"
        content += f"价格: {price}\n"
        content += f"仓位大小: {position_size}\n"
        if reason:
            content += f"原因: {reason}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        return self._send_trade_text(content)

    def send_system_alert(self, title: str, message: str) -> bool:
        """
        发送系统警报

        Args:
            title: 警报标题
            message: 警报消息

        Returns:
            表示成功与否的布尔值
        """
        content = "⚠️ 系统警报 ⚠️\n"
        content += f"标题: {title}\n"
        content += f"消息: {message}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        return self._send_trade_text(content)

    def _send_trade_text(self, content: str) -> bool:
        """子类可重写此方法以自定义文本发送格式"""
        return self._send_message({"msg_type": "text", "content": {"text": content}})
