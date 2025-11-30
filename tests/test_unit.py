#!/usr/bin/env python3
"""
交易策略单元测试
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy


def create_test_data():
    """创建带有明确买卖信号的测试数据"""
    # 创建一个具有明显上升和下降趋势的DataFrame
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1D')

    # 创建具有明显上升趋势后下降趋势的价格数据
    prices = []
    # 上升趋势：价格逐渐上涨
    for i in range(50):
        prices.append(100 + i * 2 + np.random.normal(0, 1))
    # 下降趋势：价格逐渐下跌
    for i in range(50):
        prices.append(200 - i * 2 + np.random.normal(0, 1))

    df = pd.DataFrame({
        'timestamp': dates,
        'open': [p + np.random.normal(0, 0.5) for p in prices],
        'high': [p + abs(np.random.normal(0, 1)) for p in prices],
        'low': [p - abs(np.random.normal(0, 1)) for p in prices],
        'close': prices,
        'volume': [1000 + np.random.randint(-100, 100) for _ in range(100)]
    })

    return df


def test_trend_following_strategy():
    """测试趋势跟踪策略"""
    print("正在测试趋势跟踪策略...")

    # 创建策略
    strategy = TrendFollowingStrategy()

    # 创建测试数据
    data = create_test_data()

    # 计算技术指标
    data_with_indicators = strategy.calculate_indicators(data.copy())

    # 检查是否计算了技术指标
    assert 'ma_short' in data_with_indicators.columns, "未计算短期均线"
    assert 'ma_long' in data_with_indicators.columns, "未计算长期均线"
    assert 'momentum' in data_with_indicators.columns, "未计算动量指标"

    print("✓ 技术指标计算正确")

    # 测试评估方法
    # 测试几行数据确保没有异常
    for i in range(10, min(20, len(data_with_indicators))):
        result = strategy.evaluate(data_with_indicators.iloc[i])
        # 处理字符串和字典两种返回格式
        if isinstance(result, dict):
            signal = result.get('action', '').upper()
        else:
            signal = result.upper()
        assert signal in ["BUY", "SELL", "HOLD"], f"无效信号: {result}"

    print("✓ 评估方法正常工作")
    print("趋势跟踪策略测试通过!\n")


def test_mean_reversion_strategy():
    """测试均值回归策略"""
    print("正在测试均值回归策略...")

    # 创建策略
    strategy = MeanReversionStrategy()

    # 创建测试数据
    data = create_test_data()

    # 计算技术指标
    data_with_indicators = strategy.calculate_indicators(data.copy())

    # 检查是否计算了技术指标
    assert 'ma' in data_with_indicators.columns, "未计算均线"
    assert 'upper_band' in data_with_indicators.columns, "未计算上轨"
    assert 'lower_band' in data_with_indicators.columns, "未计算下轨"
    assert 'rsi' in data_with_indicators.columns, "未计算RSI"

    print("✓ 技术指标计算正确")

    # 测试评估方法
    # 测试几行数据确保没有异常
    for i in range(20, min(30, len(data_with_indicators))):
        result = strategy.evaluate(data_with_indicators.iloc[i])
        # 处理字符串和字典两种返回格式
        if isinstance(result, dict):
            signal = result.get('action', '').upper()
        else:
            signal = result.upper()
        assert signal in ["BUY", "SELL", "HOLD"], f"无效信号: {result}"

    print("✓ 评估方法正常工作")
    print("均值回归策略测试通过!\n")


def test_turtle_trading_strategy():
    """测试海龟交易策略"""
    print("正在测试海龟交易策略...")

    # 创建策略
    strategy = TurtleTradingStrategy()

    # 创建测试数据（海龟策略需要K线数据格式）
    # 模拟币安API的K线数据格式
    test_klines = []
    base_timestamp = 1617590400000  # 示例时间戳
    for i in range(100):
        # 构造K线数据 [timestamp, open, high, low, close, volume, ...]
        open_price = 50000 + i * 10
        close_price = 50000 + i * 12
        high_price = max(open_price, close_price) + 50
        low_price = min(open_price, close_price) - 50
        volume = 100 + i

        kline = [
            str(base_timestamp + i * 3600000),  # timestamp
            str(open_price),    # open
            str(high_price),    # high
            str(low_price),     # low
            str(close_price),   # close
            str(volume),        # volume
            str(base_timestamp + (i + 1) * 3600000 - 1),  # close_time
            "0",                # quote_asset_volume
            "0",                # number_of_trades
            "0",                # taker_buy_base_asset_volume
            "0",                # taker_buy_quote_asset_volume
            "0"                 # ignore
        ]
        test_klines.append(kline)

    # 测试评估方法
    # 测试几行数据确保没有异常
    result = strategy.evaluate(test_klines)
    # 处理字符串和字典两种返回格式
    if isinstance(result, dict):
        signal = result.get('action', '').upper()
    else:
        signal = result.upper()
    assert signal in ["BUY", "SELL", "HOLD"], f"无效信号: {result}"

    print("✓ 评估方法正常工作")
    print("海龟交易策略测试通过!\n")


def test_dingtalk_notifier():
    """测试钉钉通知器"""
    print("正在测试钉钉通知器...")

    # 导入测试函数
    import subprocess
    import sys
    import os

    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_script_path = os.path.join(current_dir, "test_dingtalk.py")

    # 运行钉钉通知器的独立测试
    result = subprocess.run([sys.executable, test_script_path],
                          capture_output=True, text=True, cwd=current_dir)

    # 检查测试是否成功运行
    if result.returncode == 0:
        print("✓ 钉钉通知器测试通过")
    else:
        print("✗ 钉钉通知器测试失败")
        print("错误输出:", result.stdout)
        print("错误详情:", result.stderr)
        raise AssertionError("钉钉通知器测试失败")


def main():
    """运行所有单元测试"""
    print("正在运行交易策略的单元测试...\n")

    try:
        test_trend_following_strategy()
        test_mean_reversion_strategy()
        test_turtle_trading_strategy()
        test_dingtalk_notifier()

        print("所有单元测试通过! ✓")

    except Exception as e:
        print(f"单元测试失败: {e}")
        raise


if __name__ == "__main__":
    main()
