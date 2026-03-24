"""
飞书订单确认集成
复用现有 notifications/feishu.py 的 webhook 能力
"""
import json
from datetime import datetime, timezone
from typing import Optional

import httpx
from loguru import logger

from paper_trading import storage


class FeishuOrderIntegration:
    """
    飞书订单确认集成
    - 发送订单确认卡片到飞书
    - 接收并解析飞书回调
    - 执行或取消订单
    """

    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        self.webhook_url = webhook_url
        self.secret = secret

    async def _send_message_async(self, payload: dict) -> bool:
        """异步发送消息到飞书 webhook"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                )
            result = response.json()
            if result.get("code") == 0:
                logger.info("飞书订单确认卡片发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False

    def _send_message(self, payload: dict) -> bool:
        """发送消息到飞书 webhook（同步版本，兼容非异步场景）"""
        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0,
            )
            result = response.json()
            if result.get("code") == 0:
                logger.info("飞书订单确认卡片发送成功")
                return True
            else:
                logger.error(f"飞书消息发送失败: {result.get('msg')}")
                return False
        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False

    async def send_order_confirmation(
        self,
        signal_id: str,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> bool:
        """
        发送订单确认卡片到飞书

        Args:
            signal_id: 信号ID（用于回调标识）
            account_id: 账户ID
            symbol: 交易对
            side: 方向 (long/short)
            quantity: 数量
            entry_price: 入场价
            stop_loss: 止损价
            take_profit: 止盈价
            reason: 交易原因

        Returns:
            发送是否成功
        """
        side_emoji = "🟢" if side == "long" else "🔴"
        side_text = "做多" if side == "long" else "做空"

        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**品种:** {symbol}\n"
                               f"**方向:** {side_emoji} {side_text}\n"
                               f"**数量:** {quantity}\n"
                               f"**入场价:** ${entry_price:,.2f}\n"
                               f"{f'**止损价:** ${stop_loss:,.2f}\n' if stop_loss is not None else ''}"
                               f"{f'**止盈价:** ${take_profit:,.2f}\n' if take_profit is not None else ''}"
                               f"**信号ID:** `{signal_id}`\n"
                               f"**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                },
            }
        ]

        if reason:
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**交易理由:**\n{reason}"
                },
            })

        elements.append({"tag": "hr"})
        elements.append({
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "✅ 确认下单"},
                    "type": "primary",
                    "value": json.dumps({"action": "confirm", "signal_id": signal_id, "account_id": account_id}),
                },
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "❌ 取消"},
                    "type": "danger",
                    "value": json.dumps({"action": "reject", "signal_id": signal_id, "account_id": account_id}),
                },
            ],
        })

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "📊 模拟交易确认请求",
                    },
                    "template": "blue" if side == "long" else "red",
                },
                "elements": elements,
            },
        }

        return await self._send_message_async(payload)

    def parse_callback(self, body: dict) -> Optional[dict]:
        """
        解析飞书回调消息体

        飞书卡片按钮回调格式:
        {
            "action": {...},
            "chat_id": "...",
            "open_id": "...",
            ...
        }

        action.value 中包含 JSON 字符串: {"action": "confirm/reject", "signal_id": "...", "account_id": "..."}
        """
        try:
            action_value = body.get("action", {}).get("value", {})
            if isinstance(action_value, str):
                action_value = json.loads(action_value)

            return {
                "action": action_value.get("action"),
                "signal_id": action_value.get("signal_id"),
                "account_id": action_value.get("account_id"),
                "user_id": body.get("open_id"),
                "chat_id": body.get("chat_id"),
            }
        except Exception as e:
            logger.warning(f"飞书回调解析失败: {e}")
            return None

    async def process_confirmation(
        self,
        signal_id: str,
        action: str,
        account_id: Optional[str] = None,
    ) -> dict:
        """
        处理确认/拒绝指令

        Args:
            signal_id: 信号ID
            action: confirm 或 reject
            account_id: 账户ID（可选，从回调中获取）

        Returns:
            处理结果
        """
        signal = await storage.get_signal(signal_id)
        if not signal:
            return {"success": False, "error": "信号不存在"}

        if signal.status.value != "pending":
            return {"success": False, "error": f"信号状态已是 {signal.status.value}"}

        if action == "confirm":
            await storage.update_signal(
                signal_id,
                status="confirmed",
                confirmed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            return {
                "success": True,
                "action": "confirmed",
                "signal": signal,
            }
        elif action == "reject":
            await storage.update_signal(
                signal_id,
                status="rejected",
                confirmed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            return {
                "success": True,
                "action": "rejected",
                "signal": signal,
            }
        else:
            return {"success": False, "error": f"未知动作: {action}"}


# 单例
_feishu_integration: Optional[FeishuOrderIntegration] = None


def get_feishu_integration() -> Optional[FeishuOrderIntegration]:
    global _feishu_integration
    return _feishu_integration


def init_feishu_integration(webhook_url: str, secret: Optional[str] = None):
    global _feishu_integration
    _feishu_integration = FeishuOrderIntegration(webhook_url, secret)
    return _feishu_integration
