import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from loguru import logger

from notifications.base import BaseNotifier


class FeishuNotifier(BaseNotifier):
    """
    飞书通知服务，用于发送警报和交易通知

    当配置中启用飞书通知时，交易信号将通过此服务发送到飞书群聊。
    支持文本消息、交易通知和系统警报三种消息类型。
    """

    # 趋势信息映射
    TREND_INFO = {
        "bull": {"emoji": "📈", "text": "看涨"},
        "bear": {"emoji": "📉", "text": "看跌"},
        "neutral": {"emoji": "➡️", "text": "震荡"}
    }

    def __init__(self, webhook_url: str, template_id: str = None, template_version: str = None):
        """
        初始化飞书通知器

        Args:
            webhook_url: 飞书机器人webhook URL
            template_id: 消息模板ID（可选）
            template_version: 消息模板版本（可选）
        """
        self.webhook_url = webhook_url
        self.template_id = template_id
        self.template_version = template_version
        logger.info("飞书通知器已初始化")

    def _send_message(self, payload: Dict[str, Any]) -> bool:
        """
        发送消息到飞书webhook

        Args:
            payload: 消息载荷

        Returns:
            表示成功与否的布尔值
        """
        try:
            # 发送POST请求
            response = requests.post(
                self.webhook_url,
                headers={'Content-Type': 'application/json'},
                json=payload
            )

            result = response.json()

            if result.get('code') == 0:
                logger.info("飞书通知发送成功")
                return True
            else:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"飞书通知发送失败: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"发送飞书通知时出错: {e}")
            return False

    def send_text(self, content: str) -> bool:
        """
        发送文本消息

        Args:
            content: 要发送的文本内容

        Returns:
            表示成功与否的布尔值
        """
        payload = {
            "msg_type": "text",
            "content": {"text": content}
        }
        return self._send_message(payload)

    def _send_trade_text(self, content: str) -> bool:
        """重写父类方法，使用飞书格式"""
        return self.send_text(content)

    def send_rich_text(self, title: str, content: str) -> bool:
        """
        发送富文本消息

        Args:
            title: 标题
            content: 内容

        Returns:
            表示成功与否的布尔值
        """
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [[{"tag": "text", "text": content}]]
                    }
                }
            }
        }
        return self._send_message(payload)

    def send_card(self, title: str, content: str, color: str = "blue") -> bool:
        """
        发送卡片消息

        Args:
            title: 标题
            content: 内容
            color: 卡片颜色 (blue, green, red, yellow, grey)

        Returns:
            表示成功与否的布尔值
        """
        content_lines = content.split('\n')
        elements = []

        for line in content_lines:
            if line.strip():
                elements.append({
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": line}
                })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": title},
                    "template": color
                },
                "elements": elements
            }
        }
        return self._send_message(payload)

    def send_analysis_report(
        self,
        symbol: str,
        analysis_result: str,
        trend: str = "neutral"
    ) -> bool:
        """
        发送分析报告

        Args:
            symbol: 交易对
            analysis_result: 分析结果
            trend: 趋势 (bull/bear/neutral)

        Returns:
            表示成功与否的布尔值
        """
        info = self.TREND_INFO.get(trend, self.TREND_INFO["neutral"])
        title = f"{info['emoji']} {symbol} 行情分析 | {info['text']}"

        # 构建消息内容
        content = f"\n\n--- 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        if self.template_id:
            # 使用模板卡片格式
            payload = {
                "msg_type": "interactive",
                "card": {
                    "type": "template",
                    "data": {
                        "template_id": self.template_id,
                        "template_variable": {
                            "title": title,
                            "content": analysis_result + content
                        }
                    }
                }
            }
            if self.template_version:
                payload["card"]["data"]["template_version_name"] = self.template_version
        else:
            # 使用富文本消息
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [[{"tag": "text", "text": analysis_result + content}]]
                        }
                    }
                }
            }

        return self._send_message(payload)


# 示例用法
if __name__ == "__main__":
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_url"

    notifier = FeishuNotifier(webhook_url)

    notifier.send_trade_notification(
        symbol="BTCUSDT",
        action="buy",
        price=50000.0,
        reason="趋势跟踪信号",
        position_size=0.001
    )
