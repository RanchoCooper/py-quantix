#!/usr/bin/env python3
"""
策略模块测试
验证所有策略是否可以正确导入和实例化
"""

import sys
from pathlib import Path

from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_strategy_imports():
    """测试策略导入和实例化"""
    print("正在测试策略导入...")

    # 测试趋势跟踪策略
    print("1. 测试趋势跟踪策略...")
    strategy1 = TrendFollowingStrategy(period=14, multiplier=2)
    print(f"   ✓ 趋势跟踪策略实例化成功: {type(strategy1).__name__}")

    # 测试均值回归策略
    print("2. 测试均值回归策略...")
    strategy2 = MeanReversionStrategy(period=20, std_dev_multiplier=2)
    print(f"   ✓ 均值回归策略实例化成功: {type(strategy2).__name__}")

    # 测试海龟交易策略
    print("3. 测试海龟交易策略...")
    strategy3 = TurtleTradingStrategy(entry_period=20, exit_period=10, atr_period=14)
    print(f"   ✓ 海龟交易策略实例化成功: {type(strategy3).__name__}")


if __name__ == "__main__":
    test_strategy_imports()
    print("\n所有策略测试通过!")
