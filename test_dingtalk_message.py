#!/usr/bin/env python3
"""
测试脚本，用于发送测试消息到钉钉机器人
"""

import os
import sys

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notifications.dingtalk import DingTalkNotifier
from utils.config_manager import ConfigManager


def send_test_message():
    """发送测试消息到钉钉机器人"""
    try:
        # 加载配置
        config = ConfigManager.load_config("config/config.json")

        # 获取钉钉配置
        dingtalk_config = config['notifications']['dingtalk']

        # 初始化钉钉通知器
        notifier = DingTalkNotifier(
            webhook_url=dingtalk_config['webhook_url'],
            secret=dingtalk_config.get('secret')
        )

        print("正在发送测试消息...")

        # 发送测试消息
        success = notifier.send_text("🔔 量化交易系统测试通知 🔔\n\n系统测试消息发送成功！\n此消息用于测试钉钉机器人通知功能。")

        if success:
            print("✅ 测试消息发送成功!")
            print("请检查钉钉群聊是否收到消息。")
        else:
            print("❌ 测试消息发送失败!")
            return False

        # 发送交易通知测试
        print("\n正在发送交易通知测试...")
        trade_success = notifier.send_trade_notification(
            symbol="BTCUSDT",
            action="buy",
            price=50000.0,
            reason="测试信号",
            position_size=0.001
        )

        if trade_success:
            print("✅ 交易通知测试发送成功!")
        else:
            print("❌ 交易通知测试发送失败!")
            return False

        # 发送系统警报测试
        print("\n正在发送系统警报测试...")
        alert_success = notifier.send_system_alert(
            title="系统测试",
            message="这是一个系统警报测试消息"
        )

        if alert_success:
            print("✅ 系统警报测试发送成功!")
            print("\n🎉 所有钉钉通知测试都已成功完成!")
        else:
            print("❌ 系统警报测试发送失败!")
            return False

        return True

    except Exception as e:
        print(f"❌ 发送测试消息时出错: {e}")
        return False


if __name__ == "__main__":
    print("钉钉机器人测试消息发送工具")
    print("=" * 30)

    if send_test_message():
        print("\n✅ 所有测试都已成功完成!")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查配置和网络连接!")
        sys.exit(1)
