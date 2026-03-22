import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from loguru import logger

from notifications.base import BaseNotifier


class DingTalkNotifier(BaseNotifier):
    """
    钉钉通知服务，用于发送警报和交易通知

    当配置中 signal_output 设置为 'dingtalk' 时，交易信号将通过此服务发送到钉钉群聊。
    支持文本消息、交易通知和系统警报三种消息类型。
    """

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """
        初始化钉钉通知器

        Args:
            webhook_url: 钉钉机器人webhook URL
            secret: 签名密钥（可选但推荐）
        """
        self.webhook_url = webhook_url
        self.secret = secret
        logger.info("钉钉通知器已初始化")

    def _generate_signature(self) -> tuple:
        """
        生成时间戳和签名用于安全webhook

        Returns:
            (时间戳, 签名)元组
        """
        timestamp = str(round(time.time() * 1000))
        if self.secret:
            string_to_sign = f"{timestamp}\n{self.secret}"
            hmac_code = hmac.new(
                self.secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return timestamp, signature
        return timestamp, None

    def _send_message(self, payload: Dict[str, Any]) -> bool:
        """
        发送消息到钉钉webhook

        Args:
            payload: 消息载荷

        Returns:
            表示成功与否的布尔值
        """
        try:
            timestamp, signature = self._generate_signature()

            # 准备带参数的URL
            url = self.webhook_url
            if signature:
                url += f"&timestamp={timestamp}&sign={signature}"

            # 发送POST请求
            response = requests.post(
                url,
                headers={'Content-Type': 'application/json'},
                json=payload
            )

            result = response.json()
            if result.get('errcode') == 0:
                logger.info("钉钉通知发送成功")
                return True
            else:
                logger.error(f"钉钉通知发送失败: {result}")
                return False

        except Exception as e:
            logger.error(f"发送钉钉通知时出错: {e}")
            return False

    def send_text(self, content: str) -> bool:
        """
        发送文本消息

        Args:
            content: 要发送的文本内容

        Returns:
            表示成功与否的布尔值
        """
        return self._send_message({
            "msgtype": "text",
            "text": {"content": content}
        })

    def _send_trade_text(self, content: str) -> bool:
        """重写父类方法，使用钉钉格式"""
        return self.send_text(content)


# 示例用法
if __name__ == "__main__":
    config = {
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=your_token",
        "secret": "your_secret"
    }

    notifier = DingTalkNotifier(
        config["webhook_url"],
        config["secret"]
    )

    notifier.send_trade_notification(
        symbol="BTCUSDT",
        action="buy",
        price=50000.0,
        reason="趋势跟踪信号",
        position_size=0.001
    )
