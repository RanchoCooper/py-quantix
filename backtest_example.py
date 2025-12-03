#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用新的回测模块从币安获取真实的历史数据
"""

import json

from core.backtester import Backtester
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy


def main():
    """主函数"""
    # 初始化回测器
    backtester = Backtester()

    # 定义要测试的策略和时间范围
    strategies = {
        'trend_following': TrendFollowingStrategy(period=14, multiplier=2.0),
        'mean_reversion': MeanReversionStrategy(period=20, std_dev_multiplier=2.0),
        'turtle_trading': TurtleTradingStrategy(entry_period=20, exit_period=10, atr_period=20)
    }

    test_periods = ['1h', '1d', '1w', '1mo']

    # 存储所有结果
    all_results = {}

    # 对每种策略和时间范围进行回测
    for strategy_name, strategy in strategies.items():
        print(f"\n{'='*50}")
        print(f"测试策略: {strategy_name}")
        print('='*50)

        strategy_results = {}
        for period in test_periods:
            try:
                print(f"\n测试时间范围: {period}")

                # 运行回测
                result = backtester.run_backtest(
                    symbol='BTCUSDT',
                    strategy=strategy,
                    lookback_period=period,
                    interval=None,  # 显式传递None，让系统自动选择
                    initial_capital=10000.0
                )

                # 存储结果
                strategy_results[period] = {
                    'return_pct': result['return_pct'],
                    'num_trades': result['num_trades'],
                    'initial_capital': result['initial_capital'],
                    'final_value': result['final_value']
                }

                print(f"  收益率: {result['return_pct']:.2f}%")
                print(f"  交易次数: {result['num_trades']}")
                print(f"  初始资金: ${result['initial_capital']:.2f}")
                print(f"  最终价值: ${result['final_value']:.2f}")

            except Exception as e:
                print(f"  错误: {e}")
                strategy_results[period] = {'error': str(e)}

        all_results[strategy_name] = strategy_results

    # 保存结果到JSON文件
    output_file = 'backtest_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*50}")
    print(f"所有回测完成，结果已保存到 {output_file}")
    print('='*50)

if __name__ == '__main__':
    main()
