import base64
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from loguru import logger

from utils.logger import setup_logger


class DingTalkNotifier:
    """
    钉钉通知服务，用于发送警报和交易通知
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
            string_to_sign = '{}\n{}'.format(timestamp, self.secret)
            hmac_code = hmac.new(
                self.secret.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
            signature = urllib.parse.quote_plus(base64.b64encode(hmac_code))
            return timestamp, signature
        return timestamp, None

    def _send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息到钉钉webhook

        Args:
            message: 消息载荷

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
                data=json.dumps(message)
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
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        return self._send_message(message)

    def send_trade_notification(self, symbol: str, action: str, price: float,
                              reason: str = "", position_size: float = 0.0) -> bool:
        """
        发送包含详细信息的交易通知

        Args:
            symbol: 交易对符号
            action: 交易操作（买入/卖出）
            price: 执行价格
            reason: 交易原因
            position_size: 仓位大小

        Returns:
            表示成功与否的布尔值
        """
        content = f"🚨 交易警报 🚨\n"
        content += f"交易对: {symbol}\n"
        content += f"操作: {action.upper()}\n"
        content += f"价格: {price}\n"
        content += f"仓位大小: {position_size}\n"
        if reason:
            content += f"原因: {reason}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_text(content)

    def send_system_alert(self, title: str, message: str) -> bool:
        """
        发送系统警报通知

        Args:
            title: 警报标题
            message: 警报消息

        Returns:
            表示成功与否的布尔值
        """
        content = f"⚠️ 系统警报 ⚠️\n"
        content += f"标题: {title}\n"
        content += f"消息: {message}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

        return self.send_text(content)


# 示例用法
if __name__ == "__main__":
    # 配置（实际应用中从配置文件加载）
    config = {
        "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=your_token",
        "secret": "your_secret"
    }

    notifier = DingTalkNotifier(
        config["webhook_url"],
        config["secret"]
    )

    # 示例：发送交易通知
    notifier.send_trade_notification(
        symbol="BTCUSDT",
        action="buy",
        price=50000.0,
        reason="趋势跟踪信号",
        position_size=0.001
    )
