from typing import Any, Dict

import pandas as pd
from loguru import logger

from core.binance_client import BinanceFuturesClient


class Backtester:
    """
    回测器类，支持从币安获取指定时间范围的历史数据进行策略回测
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化回测器

        Args:
            config_path (str): 配置文件路径
        """
        # 加载配置
        try:
            import yaml
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise

        # 初始化币安客户端
        binance_config = self.config['binance']
        self.client = BinanceFuturesClient(
            api_key=binance_config['api_key'],
            api_secret=binance_config['api_secret'],
            testnet=binance_config['testnet']
        )

        logger.info("回测器初始化完成")

    def get_historical_data(self, symbol: str, interval: str, lookback_period: str) -> pd.DataFrame:
        """
        从币安获取指定时间范围的历史K线数据

        Args:
            symbol (str): 交易对符号 (例如: 'BTCUSDT')
            interval (str): K线间隔 ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')
            lookback_period (str): 回看周期 ('1h', '1d', '1w', '1mo')

        Returns:
            pd.DataFrame: 包含历史K线数据的DataFrame
        """
        # 根据回看周期确定limit参数，增加数据量以满足策略计算需求
        limit_map = {
            '1h': 240,   # 4小时 = 240根1分钟K线 (用于1小时回测)
            '1d': 168,   # 7天 = 168根1小时K线 (用于1天回测)
            '1w': 28,    # 4周 = 28根1天K线 (用于1周回测)
            '1mo': 365   # 1年 = 365根1天K线 (用于1月回测)
        }

        # 根据回看周期确定interval参数
        interval_map = {
            '1h': '1m',   # 1小时回测使用1分钟K线
            '1d': '1h',   # 1天回测使用1小时K线
            '1w': '1d',   # 1周回测使用1天K线
            '1mo': '1d'   # 1月回测使用1天K线
        }

        # 如果用户指定了interval，则使用用户指定的
        if interval is None:
            interval = interval_map.get(lookback_period, '1h')

        limit = limit_map.get(lookback_period, 100)

        try:
            # 获取K线数据
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            # 转换为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

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

    def backtest_strategy(self, strategy, data: pd.DataFrame, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        对策略进行回测

        Args:
            strategy: 策略实例
            data (pd.DataFrame): 历史K线数据
            initial_capital (float): 初始资金

        Returns:
            Dict[str, Any]: 回测结果
        """
        capital = initial_capital
        position = 0
        trades = []

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
                    # 卖出信号 - 做空（如果支持）
                    # 为简单起见，我们只平掉多头仓位
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

            result = {
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

    def run_backtest(self, symbol: str, strategy, lookback_period: str = '1d',
                     interval: str = None, initial_capital: float = 10000.0) -> Dict[str, Any]:
        """
        运行完整的回测流程

        Args:
            symbol (str): 交易对符号
            strategy: 策略实例
            lookback_period (str): 回看周期 ('1h', '1d', '1w', '1mo')
            interval (str): K线间隔，如果为None则自动选择
            initial_capital (float): 初始资金

        Returns:
            Dict[str, Any]: 回测结果
        """
        logger.info(f"开始对 {symbol} 进行 {lookback_period} 回测")

        # 获取历史数据
        data = self.get_historical_data(symbol, interval, lookback_period)

        # 运行回测
        result = self.backtest_strategy(strategy, data, initial_capital)

        return result
