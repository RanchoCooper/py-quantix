"""
回测器模块
支持从交易所获取指定时间范围的历史数据进行策略回测
"""
import asyncio
from typing import Any, Dict, Optional

import pandas as pd
from loguru import logger

from exchange.factory import create_exchange_client
from config.settings import get_settings


class Backtester:
    """
    回测器类，支持从交易所获取指定时间范围的历史数据进行策略回测
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.settings = get_settings(config_path)
        exchange_config = self.settings.exchange
        self.client = create_exchange_client(
            exchange_id="binance",
            testnet=exchange_config.testnet
        )
        logger.info("回测器初始化完成")

    def get_historical_data(
        self,
        symbol: str,
        timeframe: Optional[str] = None,
        lookback_period: str = "1d"
    ) -> pd.DataFrame:
        limit_map: Dict[str, int] = {
            '1h': 240, '1d': 168, '1w': 28, '1mo': 365
        }
        interval_map: Dict[str, str] = {
            '1h': '1m', '1d': '1h', '1w': '1d', '1mo': '1d'
        }

        if timeframe is None:
            timeframe = interval_map.get(lookback_period, '1h')

        limit = limit_map.get(lookback_period, 100)

        try:
            klines: list = asyncio.run(
                self.client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit
                )
            )

            df = pd.DataFrame(
                klines,
                columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ]
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

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
        if initial_capital <= 0:
            raise ValueError(f"initial_capital must be positive, got {initial_capital}")
        if data.empty:
            raise ValueError("data cannot be empty")

        capital = initial_capital
        position = 0.0
        trades: list = []

        try:
            data_with_indicators = strategy.calculate_indicators(data.copy())

            for i in range(len(data_with_indicators)):
                cumulative_data = data_with_indicators.iloc[:i+1]
                signal = strategy.generate_signals(cumulative_data)

                if signal['action'] == "buy" and position <= 0:
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
        logger.info(f"开始对 {symbol} 进行 {lookback_period} 回测")
        data = self.get_historical_data(symbol, timeframe, lookback_period)
        result = self.backtest_strategy(strategy, data, initial_capital)
        return result
