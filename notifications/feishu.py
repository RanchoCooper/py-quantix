import json
import time
from datetime import datetime
from typing import Any, Dict

import requests
from loguru import logger


class FeishuNotifier:
    """
    飞书通知服务，用于发送警报和交易通知

    当配置中启用飞书通知时，交易信号将通过此服务发送到飞书群聊。
    支持文本消息、交易通知和系统警报三种消息类型。
    """

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

    def _send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息到飞书webhook

        Args:
            message: 消息载荷

        Returns:
            表示成功与否的布尔值
        """
        try:
            # 构建请求体
            payload = {
                "msg_type": message.get("msg_type", "text"),
                "content": message.get("content", {})
            }
            if payload.get("msg_type") == "interactive":
                payload["card"] = message.get("card", {})

            # 发送POST请求
            response = requests.post(
                self.webhook_url,
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
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
        message = {
            "msg_type": "text",
            "content": {
                "text": content
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
        content = "🚨 交易警报 🚨\n"
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
        content = "⚠️ 系统警报 ⚠️\n"
        content += f"标题: {title}\n"
        content += f"消息: {message}\n"
        content += f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

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
        发送分析报告 - 模板卡片格式

        Args:
            symbol: 交易对
            analysis_result: 分析结果
            trend: 趋势 (bull/bear/neutral)

        Returns:
            表示成功与否的布尔值
        """
        # 如果配置了 template_id，使用模板卡片格式
        if self.template_id:
            trend_info = {
                "bull": {"emoji": "📈", "text": "看涨"},
                "bear": {"emoji": "📉", "text": "看跌"},
                "neutral": {"emoji": "➡️", "text": "震荡"}
            }

            info = trend_info.get(trend, trend_info["neutral"])
            title = f"{info['emoji']} {symbol} 行情分析 | {info['text']}"

            # 添加时间戳到内容
            content = analysis_result
            content += f"\n\n---\n🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            payload = {
                "msg_type": "interactive",
                "card": {
                    "type": "template",
                    "data": {
                        "template_id": self.template_id,
                        "template_variable": {
                            "title": title,
                            "content": content
                        }
                    }
                }
            }
            if self.template_version:
                payload["card"]["data"]["template_version_name"] = self.template_version
        else:
            # 否则使用普通消息格式
            trend_info = {
                "bull": {"emoji": "📈", "text": "看涨"},
                "bear": {"emoji": "📉", "text": "看跌"},
                "neutral": {"emoji": "➡️", "text": "震荡"}
            }

            info = trend_info.get(trend, trend_info["neutral"])
            title = f"{info['emoji']} {symbol} 行情分析 | {info['text']}"

            # 清理内容
            # content = self._clean_analysis(analysis_result)

            # 添加时间戳
            content = f"\n\n--- 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

            # 使用富文本消息
            payload = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": title,
                            "content": [
                                [
                                    {
                                        "tag": "text",
                                        "text": content
                                    }
                                ]
                            ]
                        }
                    }
                }
            }

        return self._send_message(payload)

    # def _clean_analysis(self, text: str) -> str:
    #     """清理分析文本，保留核心内容"""
    #     lines = text.split('\n')
    #     cleaned_lines = []
    #
    #     for line in lines:
    #         # 去除 # * 等符号
    #         line = line.strip().replace('#', '').replace('*', '').strip()
    #
    #         # 跳过空行和简单分隔线
    #         if not line or line == '---':
    #             continue
    #
    #         # 跳过包含时间戳的行
    #         if '🕐' in line or '时间' in line:
    #             continue
    #
    #         cleaned_lines.append(line)
    #
    #     return '\n'.join(cleaned_lines)


# 示例用法
if __name__ == "__main__":
    # 配置（实际应用中从配置文件加载）
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_url"

    notifier = FeishuNotifier(webhook_url)

    # 示例：发送交易通知
    notifier.send_trade_notification(
        symbol="BTCUSDT",
        action="buy",
        price=50000.0,
        reason="趋势跟踪信号",
        position_size=0.001
    )
