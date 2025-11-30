#!/usr/bin/env python3
"""
回测示例脚本，演示如何使用策略与历史数据
"""

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy


def generate_sample_data(days=30):
    """
    生成用于测试的示例价格数据

    Args:
        days: 要生成的数据天数

    Returns:
        包含OHLCV数据的DataFrame
    """
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1h')

    # 生成随机游走价格
    np.random.seed(42)  # 为了结果可重现
    n_points = len(dates)
    returns = np.random.normal(0, 0.02, n_points)  # 2%的标准差
    prices = 100 * np.exp(np.cumsum(returns))  # 从$100开始

    # 创建OHLC数据
    open_prices = prices[:-1]  # 移位1以模拟真实数据
    close_prices = prices[1:]   # 下一期间的价格

    # 确保所有数组长度相同
    n_valid_points = min(len(open_prices), len(close_prices), len(dates[:-1]))

    df = pd.DataFrame({
        'timestamp': dates[:n_valid_points],
        'open': open_prices[:n_valid_points],
        'high': open_prices[:n_valid_points] * (1 + np.abs(np.random.normal(0, 0.01, n_valid_points))),
        'low': open_prices[:n_valid_points] * (1 - np.abs(np.random.normal(0, 0.01, n_valid_points))),
        'close': close_prices[:n_valid_points],
        'volume': np.random.randint(1000, 10000, n_valid_points)
    })

    return df


def backtest_strategy(strategy, data, initial_capital=10000):
    """
    简单的回测函数

    Args:
        strategy: 策略实例
        data: 包含OHLCV数据的DataFrame
        initial_capital: 初始资金

    Returns:
        包含回测结果的字典
    """
    capital = initial_capital
    position = 0
    trades = []

    # 计算技术指标
    data_with_indicators = strategy.calculate_indicators(data.copy())

    # 模拟交易
    for i in range(len(data_with_indicators)):
        row = data_with_indicators.iloc[i]
        signal = strategy.evaluate(row)

        # 根据信号执行交易
        if signal == "BUY" and position <= 0:
            # 买入信号 - 做多
            position = capital / row['close']
            capital = 0
            trades.append({
                'timestamp': row['timestamp'],
                'action': 'BUY',
                'price': row['close'],
                'position': position
            })
        elif signal == "SELL" and position >= 0:
            # 卖出信号 - 做空（如果支持）
            # 为简单起见，我们只平掉多头仓位
            if position > 0:
                capital = position * row['close']
                position = 0
                trades.append({
                    'timestamp': row['timestamp'],
                    'action': 'SELL',
                    'price': row['close'],
                    'capital': capital
                })

    # 计算最终投资组合价值
    if position > 0:
        final_value = position * data_with_indicators.iloc[-1]['close']
    else:
        final_value = capital

    return {
        'initial_capital': initial_capital,
        'final_value': final_value,
        'return_pct': ((final_value - initial_capital) / initial_capital) * 100,
        'num_trades': len(trades),
        'trades': trades
    }


def main():
    """运行回测的主函数"""
    print("正在生成示例数据...")
    data = generate_sample_data(days=30)
    print(f"已生成{len(data)}小时的示例数据")

    # 测试所有策略
    strategies = [
        ("趋势跟踪", TrendFollowingStrategy()),
        ("均值回归", MeanReversionStrategy()),
        ("海龟交易", TurtleTradingStrategy())
    ]

    results = {}

    for name, strategy in strategies:
        print(f"\n正在回测{name}策略...")
        result = backtest_strategy(strategy, data)
        results[name] = result
        print(f"{name}回测结果:")
        print(f"  初始资金: ${result['initial_capital']:.2f}")
        print(f"  最终价值: ${result['final_value']:.2f}")
        print(f"  收益率: {result['return_pct']:.2f}%")
        print(f"  交易次数: {result['num_trades']}")

    # 将结果保存到文件
    with open('backtest_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\n回测结果已保存到backtest_results.json")


if __name__ == "__main__":
    main()
