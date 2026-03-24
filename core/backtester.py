"""
回测器模块
支持从交易所获取指定时间范围的历史数据进行策略回测
"""
import asyncio
from typing import Any, Dict, Optional

import pandas as pd
from loguru import logger

from data.fetchers.market_fetcher import ExchangeClient
from utils.config_manager import ConfigManager


class Backtester:
    """
    回测器类，支持从交易所获取指定时间范围的历史数据进行策略回测
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化回测器

        Args:
            config_path: 配置文件路径
        """
        # 使用 ConfigManager 加载配置
        self.config = ConfigManager.load_config(config_path, use_env=True)

        # 初始化交易所客户端
        binance_config = self.config.get('binance', {})
        self.client = ExchangeClient(
            exchange_id="binance",
            testnet=binance_config.get('testnet', True)
        )

        logger.info("回测器初始化完成")

    def get_historical_data(
        self,
        symbol: str,
        timeframe: Optional[str] = None,
        lookback_period: str = "1d"
    ) -> pd.DataFrame:
        """
        从交易所获取指定时间范围的历史K线数据

        Args:
            symbol: 交易对符号 (例如: 'BTCUSDT')
            timeframe: K线间隔 ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')
            lookback_period: 回看周期 ('1h', '1d', '1w', '1mo')

        Returns:
            包含历史K线数据的DataFrame
        """
        # 根据回看周期确定 limit 参数
        limit_map: Dict[str, int] = {
            '1h': 240,
            '1d': 168,
            '1w': 28,
            '1mo': 365
        }

        # 根据回看周期确定 timeframe 参数
        interval_map: Dict[str, str] = {
            '1h': '1m',
            '1d': '1h',
            '1w': '1d',
            '1mo': '1d'
        }

        # 如果用户指定了 timeframe，则使用用户指定的
        if timeframe is None:
            timeframe = interval_map.get(lookback_period, '1h')

        limit = limit_map.get(lookback_period, 100)

        try:
            # 异步获取K线数据
            klines: list = asyncio.run(
                self.client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit
                )
            )

            # 转换为DataFrame
            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ]
            )

            # 转换时间戳为datetime格式
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

            # 转换数值类型
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            logger.info(f"成功获取 {symbol} 的 {lookback_period} 历史数据，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            raise

    def backtest_strategy(
        self,
        strategy: Any,
        data: pd.DataFrame,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        对策略进行回测

        Args:
            strategy: 策略实例
            data: 历史K线数据
            initial_capital: 初始资金

        Returns:
            回测结果字典
        """
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be positive, got {initial_capital}")
        if data.empty:
            raise ValueError("data cannot be empty")

        capital = initial_capital
        position = 0.0
        trades: list = []

        try:
            # 计算技术指标
            data_with_indicators = strategy.calculate_indicators(data.copy())

            # 模拟交易
            for i in range(len(data_with_indicators)):
                # 传递累积数据给策略，而不是单行数据
                cumulative_data = data_with_indicators.iloc[:i+1]
                signal = strategy.generate_signals(cumulative_data)

                # 根据信号执行交易
                if signal['action'] == "buy" and position <= 0:
                    # 买入信号 - 做多
                    row = data_with_indicators.iloc[i]
                    position = capital / row['close']
                    capital = 0
                    trades.append({
                        'timestamp': row['timestamp'],
                        'action': 'BUY',
                        'price': row['close'],
                        'position': position
                    })
                elif signal['action'] == "sell" and position >= 0:
                    # 卖出信号 - 平掉多头仓位
                    if position > 0:
                        row = data_with_indicators.iloc[i]
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

            result: Dict[str, Any] = {
                'initial_capital': initial_capital,
                'final_value': final_value,
                'return_pct': ((final_value - initial_capital) / initial_capital) * 100,
                'num_trades': len(trades),
                'trades': trades
            }

            logger.info(f"回测完成，收益率: {result['return_pct']:.2f}%")
            return result

        except Exception as e:
            logger.error(f"回测过程中出错: {e}")
            raise

    def run_backtest(
        self,
        symbol: str,
        strategy: Any,
        lookback_period: str = '1d',
        timeframe: Optional[str] = None,
        initial_capital: float = 10000.0
    ) -> Dict[str, Any]:
        """
        运行完整的回测流程

        Args:
            symbol: 交易对符号
            strategy: 策略实例
            lookback_period: 回看周期 ('1h', '1d', '1w', '1mo')
            timeframe: K线间隔，如果为None则自动选择
            initial_capital: 初始资金

        Returns:
            回测结果字典
        """
        logger.info(f"开始对 {symbol} 进行 {lookback_period} 回测")

        # 获取历史数据
        data = self.get_historical_data(symbol, timeframe, lookback_period)

        # 运行回测
        result = self.backtest_strategy(strategy, data, initial_capital)

        return result
