#!/usr/bin/env python3
"""
命令行回测工具，支持指定时间范围的历史数据回测
"""

import argparse
import json
import sys
from datetime import datetime

from core.backtester import Backtester
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.turtle_trading import TurtleTradingStrategy


def get_strategy_instance(strategy_name: str):
    """根据策略名称获取策略实例"""
    strategy_map = {
        'trend_following': TrendFollowingStrategy,
        'mean_reversion': MeanReversionStrategy,
        'turtle_trading': TurtleTradingStrategy,
    }

    if strategy_name not in strategy_map:
        raise ValueError(f"不支持的策略: {strategy_name}")

    # 对于改进版海龟交易策略，使用优化的参数
    if strategy_name == 'improved_turtle_trading':
        return strategy_map[strategy_name](entry_period=15, exit_period=7, atr_period=14)

    return strategy_map[strategy_name]()


def main():
    parser = argparse.ArgumentParser(description='量化交易策略回测工具')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='交易对符号 (默认: BTCUSDT)')
    parser.add_argument('--strategy', type=str, required=True,
                       choices=['trend_following', 'mean_reversion', 'turtle_trading'],
                       help='策略名称')
    parser.add_argument('--period', type=str, default='1d',
                       choices=['1h', '1d', '1w', '1mo'],
                       help='回测时间范围 (默认: 1d)')
    parser.add_argument('--interval', type=str,
                       choices=['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
                       help='K线间隔 (默认根据回测周期自动选择)')
    parser.add_argument('--capital', type=float, default=10000.0, help='初始资金 (默认: 10000.0)')
    parser.add_argument('--output', type=str, help='结果输出文件路径')

    args = parser.parse_args()

    try:
        # 初始化回测器
        backtester = Backtester()

        # 获取策略实例
        strategy = get_strategy_instance(args.strategy)

        # 运行回测
        print(f"开始对 {args.symbol} 使用 {args.strategy} 策略进行 {args.period} 回测...")
        result = backtester.run_backtest(
            symbol=args.symbol,
            strategy=strategy,
            lookback_period=args.period,
            interval=args.interval,
            initial_capital=args.capital
        )

        # 显示结果
        print(f"\n回测结果:")
        print(f"  交易对: {args.symbol}")
        print(f"  策略: {args.strategy}")
        print(f"  时间范围: {args.period}")
        print(f"  初始资金: ${result['initial_capital']:.2f}")
        print(f"  最终价值: ${result['final_value']:.2f}")
        print(f"  收益率: {result['return_pct']:.2f}%")
        print(f"  交易次数: {result['num_trades']}")

        # 保存结果
        if args.output:
            output_data = {
                'metadata': {
                    'symbol': args.symbol,
                    'strategy': args.strategy,
                    'period': args.period,
                    'interval': args.interval,
                    'initial_capital': args.capital,
                    'timestamp': datetime.now().isoformat()
                },
                'results': result
            }

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"\n结果已保存到 {args.output}")

        return 0

    except Exception as e:
        print(f"回测过程中发生错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
