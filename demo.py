#!/usr/bin/env python3
"""
演示脚本，展示如何使用加密货币合约交易系统
"""

import os
import sys

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import TradingEngine
from utils.logger import setup_logger


def main():
    """运行交易系统演示"""
    print("加密货币合约交易系统 - 演示")
    print("=" * 30)

    # 设置日志
    logger = setup_logger("INFO", "logs/demo.log")
    logger.info("开始交易系统演示")

    # 展示如何初始化交易引擎（不实际连接）
    print("\n初始化交易引擎:")
    print("  engine = TradingEngine('config/config.json')")
    print("\n这将从JSON文件加载配置并初始化所有组件，包括")
    print("币安客户端、通知器和配置的交易策略。")

    # 展示系统结构
    print("\n系统组件:")
    print("- 币安合约客户端（用于市场数据和交易）")
    print("- 钉钉通知器（用于警报和通知）")
    print("- 可配置的交易策略（趋势跟踪、均值回归或海龟交易）")
    print("- 风险管理控制")
    print("- 仓位跟踪")

    # 演示策略评估概念
    print("\n可以使用市场数据评估策略以生成交易信号。")
    print("系统支持基于这些信号的自动化交易。")

    print("\n系统演示完成!")
    print("\n运行完整系统:")
    print("  python main.py")
    print("\n运行回测:")
    print("  python backtest_example.py")
    print("\n运行单元测试:")
    print("  python test_unit.py")


if __name__ == "__main__":
    main()
