#!/usr/bin/env python3
"""
测试脚本，验证所有策略都可以被导入和实例化
"""

from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy


def test_strategy_imports():
    """测试所有策略是否可以被导入和实例化"""
    print("正在测试策略导入...")

    # 测试趋势跟踪策略
    try:
        trend_params = {
            "short_ma": 10,
            "long_ma": 50,
            "momentum_period": 14,
            "momentum_threshold": 0.0
        }
        trend_strategy = TrendFollowingStrategy(trend_params)
        print("✓ 趋势跟踪策略成功导入和实例化")
    except Exception as e:
        print(f"✗ 趋势跟踪策略错误: {e}")
        return False

    # 测试均值回归策略
    try:
        mr_params = {
            "bb_period": 20,
            "bb_multiplier": 2.0,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30
        }
        mr_strategy = MeanReversionStrategy(mr_params)
        print("✓ 均值回归策略成功导入和实例化")
    except Exception as e:
        print(f"✗ 均值回归策略错误: {e}")
        return False

    # 测试海龟交易策略
    try:
        turtle_params = {
            "entry_window": 20,
            "exit_window": 10,
            "atr_period": 14
        }
        turtle_strategy = TurtleTradingStrategy(turtle_params)
        print("✓ 海龟交易策略成功导入和实例化")
    except Exception as e:
        print(f"✗ 海龟交易策略错误: {e}")
        return False

    print("所有策略都成功导入和实例化!")
    return True


if __name__ == "__main__":
    success = test_strategy_imports()
    if not success:
        exit(1)
