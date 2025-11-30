#!/usr/bin/env python3
"""
钉钉通知器单元测试
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notifications.dingtalk import DingTalkNotifier


class TestDingTalkNotifier(unittest.TestCase):
    """钉钉通知器测试类"""

    def setUp(self):
        """测试前准备"""
        self.webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=b9a18c4d67a386e4ec782df6f5bf80f7d6e5c97e7dc17ff9546f75641bb36c86"
        self.secret = "SEC75d0bccebe0b61fe9f6f608c725e1b1736358c7e439fee11425b8db0c9391006"
        self.notifier = DingTalkNotifier(self.webhook_url, self.secret)

    def test_init(self):
        """测试初始化功能"""
        # 测试带密钥的初始化
        notifier = DingTalkNotifier(self.webhook_url, self.secret)
        self.assertEqual(notifier.webhook_url, self.webhook_url)
        self.assertEqual(notifier.secret, self.secret)

        # 测试不带密钥的初始化
        notifier_no_secret = DingTalkNotifier(self.webhook_url)
        self.assertEqual(notifier_no_secret.webhook_url, self.webhook_url)
        self.assertIsNone(notifier_no_secret.secret)

    def test_generate_signature(self):
        """测试签名生成功能"""
        # 测试带密钥的签名生成
        timestamp, signature = self.notifier._generate_signature()
        self.assertIsNotNone(timestamp)
        self.assertIsNotNone(signature)

        # 测试不带密钥的签名生成
        notifier_no_secret = DingTalkNotifier(self.webhook_url)
        timestamp, signature = notifier_no_secret._generate_signature()
        self.assertIsNotNone(timestamp)
        self.assertIsNone(signature)

    @patch('notifications.dingtalk.requests.post')
    def test_send_message_success(self, mock_post):
        """测试消息发送成功的情况"""
        # 模拟成功的HTTP响应
        mock_response = MagicMock()
        mock_response.json.return_value = {'errcode': 0, 'errmsg': 'ok'}
        mock_post.return_value = mock_response

        message = {
            "msgtype": "text",
            "text": {
                "content": "测试消息"
            }
        }

        result = self.notifier._send_message(message)
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('notifications.dingtalk.requests.post')
    def test_send_message_failure(self, mock_post):
        """测试消息发送失败的情况"""
        # 模拟失败的HTTP响应
        mock_response = MagicMock()
        mock_response.json.return_value = {'errcode': 1, 'errmsg': 'error'}
        mock_post.return_value = mock_response

        message = {
            "msgtype": "text",
            "text": {
                "content": "测试消息"
            }
        }

        result = self.notifier._send_message(message)
        self.assertFalse(result)

    @patch('notifications.dingtalk.requests.post')
    def test_send_message_exception(self, mock_post):
        """测试消息发送时出现异常的情况"""
        # 模拟网络异常
        mock_post.side_effect = Exception("网络错误")

        message = {
            "msgtype": "text",
            "text": {
                "content": "测试消息"
            }
        }

        result = self.notifier._send_message(message)
        self.assertFalse(result)

    @patch('notifications.dingtalk.DingTalkNotifier._send_message')
    def test_send_text(self, mock_send_message):
        """测试发送文本消息功能"""
        mock_send_message.return_value = True

        content = "测试文本消息"
        result = self.notifier.send_text(content)

        self.assertTrue(result)
        mock_send_message.assert_called_once()

        # 检查传递给_send_message的参数
        called_args = mock_send_message.call_args[0][0]
        self.assertEqual(called_args["msgtype"], "text")
        self.assertEqual(called_args["text"]["content"], content)

    @patch('notifications.dingtalk.DingTalkNotifier.send_text')
    def test_send_trade_notification(self, mock_send_text):
        """测试发送交易通知功能"""
        mock_send_text.return_value = True

        result = self.notifier.send_trade_notification(
            symbol="BTCUSDT",
            action="buy",
            price=50000.0,
            reason="趋势跟踪信号",
            position_size=0.001
        )

        self.assertTrue(result)
        mock_send_text.assert_called_once()

        # 检查消息内容是否包含必要信息
        called_args = mock_send_text.call_args[0][0]
        self.assertIn("🚨 交易警报 🚨", called_args)
        self.assertIn("BTCUSDT", called_args)
        self.assertIn("BUY", called_args)
        self.assertIn("50000.0", called_args)
        self.assertIn("趋势跟踪信号", called_args)
        self.assertIn("0.001", called_args)

    @patch('notifications.dingtalk.DingTalkNotifier.send_text')
    def test_send_system_alert(self, mock_send_text):
        """测试发送系统警报功能"""
        mock_send_text.return_value = True

        result = self.notifier.send_system_alert(
            title="系统错误",
            message="数据库连接失败"
        )

        self.assertTrue(result)
        mock_send_text.assert_called_once()

        # 检查消息内容是否包含必要信息
        called_args = mock_send_text.call_args[0][0]
        self.assertIn("⚠️ 系统警报 ⚠️", called_args)
        self.assertIn("系统错误", called_args)
        self.assertIn("数据库连接失败", called_args)


def main():
    """运行钉钉通知器的单元测试"""
    print("正在运行钉钉通知器的单元测试...\n")

    # 运行测试
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    main()
