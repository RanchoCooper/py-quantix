#!/usr/bin/env python3
"""
测试不同运行模式的功能
"""

import os
import sys

from core.engine import TradingEngine
from utils.logger import setup_logger

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_auto_mode():
    """测试自动交易模式"""
    print("测试自动交易模式 (auto)...")

    # 设置日志
    setup_logger("INFO")

    # 初始化交易引擎（自动模式）
    engine = TradingEngine("config/config.json", mode="auto")

    # 为测试目的手动设置一个交易对
    symbol = "BNBUSDT"
    engine.last_signals[symbol] = None
    engine.positions[symbol] = {}

    # 创建一个模拟信号用于测试
    mock_signal = {
        "action": "buy",
        "reason": "测试信号",
        "price": 50000,
        "position_size": 0.001
    }

    # 测试执行交易（在自动模式下应该尝试下单）
    result = engine._execute_trade(symbol, mock_signal)
    print(f"自动模式交易执行结果: {result}")
    print("在自动模式下，系统会尝试执行实际交易订单。")
    print()


def test_monitor_mode():
    """测试监控模式"""
    print("测试监控模式 (monitor)...")

    # 设置日志
    setup_logger("INFO")

    # 初始化交易引擎（监控模式）
    engine = TradingEngine("config/config.json", mode="monitor")

    # 为测试目的手动设置一个交易对
    symbol = "BNBUSDT"
    engine.last_signals[symbol] = None
    engine.positions[symbol] = {}

    # 创建一个模拟信号用于测试
    mock_signal = {
        "action": "sell",
        "reason": "测试信号",
        "price": 49000,
        "position_size": 0.001
    }

    # 测试执行交易（在监控模式下应该只发送通知，不实际下单）
    result = engine._execute_trade(symbol, mock_signal)
    print(f"监控模式交易执行结果: {result}")
    print("在监控模式下，系统只会发送通知，不会执行实际交易订单。")
    print()


def main():
    """运行所有模式测试"""
    print("测试不同的运行模式")
    print("=" * 30)

    test_auto_mode()
    test_monitor_mode()

    print("所有模式测试完成!")
    print("\n使用说明:")
    print("  python main.py --mode auto     # 自动交易模式（发现信号时自动下单）")
    print("  python main.py --mode monitor  # 监控模式（发现信号时仅发送通知）")


if __name__ == "__main__":
    main()
