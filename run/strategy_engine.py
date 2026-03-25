"""
策略引擎
负责策略的运行、信号处理和执行
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable

from loguru import logger
from config.settings import get_settings
from exchange.factory import create_exchange_client
from market.candle_store import CandleStore
from strategies.base_strategy import BaseStrategy


class StrategyEngine:
    """策略引擎"""

    def __init__(
        self,
        exchange_id: str = "binance",
        testnet: bool = True,
        data_path: str = "./data/storage",
        config_path: Optional[str] = None,
    ):
        self.settings = get_settings(config_path)
        self.exchange_id = exchange_id
        self.testnet = testnet

        self.fetcher = create_exchange_client(exchange_id, testnet, config_path)
        self.candle_store = CandleStore(data_path, self.settings.data.max_candles_in_memory)

        self.strategies: Dict[str, BaseStrategy] = {}
        self.symbols: List[str] = self._get_symbols()
        self.timeframes: List[str] = self.settings.data.timeframes

        self.is_running = False
        self.tasks: List[asyncio.Task] = []

        self.on_signal: Optional[Callable] = None
        self.on_error: Optional[Callable] = None

        logger.info(f"StrategyEngine initialized for {exchange_id}, testnet: {testnet}")

    def _get_symbols(self) -> List[str]:
        """获取交易对列表"""
        trading_config = self.settings.trading
        symbols = trading_config.symbols
        if isinstance(symbols, dict):
            return list(symbols.keys())
        return symbols

    def add_strategy(self, strategy: BaseStrategy):
        key = f"{strategy.symbol}:{strategy.timeframe}:{strategy.name}"
        self.strategies[key] = strategy
        logger.info(f"Added strategy: {key}")

    def remove_strategy(self, key: str):
        if key in self.strategies:
            del self.strategies[key]
            logger.info(f"Removed strategy: {key}")

    def get_strategy(self, key: str) -> Optional[BaseStrategy]:
        return self.strategies.get(key)

    async def initialize(self):
        """初始化 - 预加载数据"""
        logger.info("Initializing strategies...")

        self.fetcher.get_markets()

        for symbol in self.symbols:
            for timeframe in self.timeframes:
                count = self.candle_store.load_from_file(symbol, timeframe)

                if count == 0:
                    try:
                        candles = await self.fetcher.fetch_ohlcv(
                            symbol, timeframe, limit=self.settings.data.limit
                        )
                        self.candle_store.add_candles(symbol, timeframe, candles)
                        logger.info(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
                    except Exception as e:
                        logger.error(f"Failed to fetch candles for {symbol} {timeframe}: {e}")

        for key, strategy in self.strategies.items():
            symbol = strategy.symbol
            timeframe = strategy.timeframe

            df = self.candle_store.get_candles_dataframe(symbol, timeframe)
            strategy.update_data(df)

            logger.info(f"Initialized strategy {strategy.name} with {len(df)} candles")

    async def start(self):
        """启动引擎"""
        if self.is_running:
            logger.warning("Engine is already running")
            return

        self.is_running = True
        logger.info("StrategyEngine started")

        for key, strategy in self.strategies.items():
            task = asyncio.create_task(self._run_strategy(strategy))
            self.tasks.append(task)

    async def stop(self):
        """停止引擎"""
        if not self.is_running:
            return

        self.is_running = False

        for task in self.tasks:
            task.cancel()

        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        self.candle_store.save_all()
        logger.info("StrategyEngine stopped")

    async def _run_strategy(self, strategy: BaseStrategy):
        symbol = strategy.symbol
        timeframe = strategy.timeframe
        interval = self._get_interval_seconds(timeframe)

        while self.is_running:
            try:
                candles = await self.fetcher.fetch_ohlcv(symbol, timeframe, limit=1)

                if candles:
                    self.candle_store.add_candles(symbol, timeframe, candles[-1:])

                    df = self.candle_store.get_candles_dataframe(symbol, timeframe)
                    strategy.update_data(df)

                    signal = strategy.get_signals()

                    if signal and self.on_signal:
                        await self.on_signal(signal)

            except Exception as e:
                logger.error(f"Error in strategy {strategy.name}: {e}")
                if self.on_error:
                    await self.on_error(e)

            await asyncio.sleep(interval)

    def _get_interval_seconds(self, timeframe: str) -> int:
        mapping = {
            "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
            "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600,
            "12h": 43200, "1d": 86400, "1w": 604800,
        }
        return mapping.get(timeframe, 3600)

    async def fetch_and_update(self, symbol: str, timeframe: str):
        try:
            candles = await self.fetcher.fetch_ohlcv(symbol, timeframe, limit=100)
            self.candle_store.add_candles(symbol, timeframe, candles)

            for key, strategy in self.strategies.items():
                if strategy.symbol == symbol and strategy.timeframe == timeframe:
                    df = self.candle_store.get_candles_dataframe(symbol, timeframe)
                    strategy.update_data(df)

            return candles

        except Exception as e:
            logger.error(f"Failed to fetch and update {symbol} {timeframe}: {e}")
            raise

    async def get_balance(self) -> Dict[str, Any]:
        return await self.fetcher.fetch_balance()

    async def get_positions(self) -> List[Dict[str, Any]]:
        return await self.fetcher.fetch_positions()

    def get_candles(self, symbol: str, timeframe: str, limit: int = 100):
        return self.candle_store.get_candles_dataframe(symbol, timeframe, limit)

    def get_candle_store(self) -> CandleStore:
        return self.candle_store

    def __repr__(self):
        return f"StrategyEngine(strategies={len(self.strategies)}, symbols={len(self.symbols)})"
