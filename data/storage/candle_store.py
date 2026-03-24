"""
K线数据存储模块
提供内存缓存和文件存储功能
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
from threading import Lock

from loguru import logger


class CandleStore:
    """K线数据存储器"""

    def __init__(self, data_path: str = "./data/storage", max_candles: int = 1000):
        """
        初始化存储器

        Args:
            data_path: 数据存储路径
            max_candles: 内存中最大K线数量
        """
        self.data_path = Path(data_path)
        self.max_candles = max_candles

        # 内存缓存: {symbol: {timeframe: deque([candles...])}}
        self._cache: Dict[str, Dict[str, deque]] = {}
        self._lock = Lock()

        # 确保目录存在
        self.data_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"CandleStore initialized with path: {data_path}, max_candles: {max_candles}")

    def _ensure_cache(self, symbol: str, timeframe: str) -> deque:
        """确保缓存结构存在并返回对应 deque"""
        if symbol not in self._cache:
            self._cache[symbol] = {}
        if timeframe not in self._cache[symbol]:
            self._cache[symbol][timeframe] = deque(maxlen=self.max_candles)
        return self._cache[symbol][timeframe]

    def add_candle(self, symbol: str, timeframe: str, candle: List):
        """
        添加一根K线

        Args:
            symbol: 交易对
            timeframe: 时间周期
            candle: K线数据 [timestamp, open, high, low, close, volume]
        """
        with self._lock:
            candles = self._ensure_cache(symbol, timeframe)

            # 避免重复添加
            if candles and candles[-1][0] == candle[0]:
                candles[-1] = candle
            else:
                candles.append(candle)

    def add_candles(self, symbol: str, timeframe: str, candles: List[List]):
        """
        批量添加K线

        Args:
            symbol: 交易对
            timeframe: 时间周期
            candles: K线数据列表
        """
        with self._lock:
            candles_deque = self._ensure_cache(symbol, timeframe)

            for candle in candles:
                if candles_deque and candles_deque[-1][0] == candle[0]:
                    candles_deque[-1] = candle
                elif not candles_deque or candles_deque[-1][0] < candle[0]:
                    candles_deque.append(candle)

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: Optional[int] = None,
        since: Optional[int] = None,
        until: Optional[int] = None,
    ) -> List[List]:
        """
        获取K线数据

        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: 返回数量限制
            since: 起始时间戳
            until: 结束时间戳

        Returns:
            K线数据列表
        """
        with self._lock:
            if symbol not in self._cache or timeframe not in self._cache[symbol]:
                return []

            candles = list(self._cache[symbol][timeframe])

        # 时间过滤
        if since is not None:
            candles = [c for c in candles if c[0] >= since]
        if until is not None:
            candles = [c for c in candles if c[0] <= until]

        # 数量限制
        if limit is not None:
            candles = candles[-limit:]

        return candles

    def get_candles_dataframe(
        self,
        symbol: str,
        timeframe: str,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        获取K线数据 (DataFrame格式)

        Args:
            symbol: 交易对
            timeframe: 时间周期
            limit: 返回数量限制

        Returns:
            DataFrame
        """
        candles = self.get_candles(symbol, timeframe, limit)

        if not candles:
            return pd.DataFrame(
                columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

        df = pd.DataFrame(
            candles,
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.set_index("datetime")

        return df

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[List]:
        """
        获取最新一根K线

        Args:
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            K线数据 或 None
        """
        candles = self.get_candles(symbol, timeframe, limit=1)
        return candles[0] if candles else None

    def get_oldest_candle(self, symbol: str, timeframe: str) -> Optional[List]:
        """
        获取最旧一根K线

        Args:
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            K线数据 或 None
        """
        candles = self.get_candles(symbol, timeframe)
        return candles[0] if candles else None

    def get_count(self, symbol: str, timeframe: str) -> int:
        """获取缓存的K线数量"""
        with self._lock:
            if symbol not in self._cache or timeframe not in self._cache[symbol]:
                return 0
            return len(self._cache[symbol][timeframe])

    def has_data(self, symbol: str, timeframe: str) -> bool:
        """检查是否有数据"""
        return self.get_count(symbol, timeframe) > 0

    def clear(self, symbol: Optional[str] = None, timeframe: Optional[str] = None):
        """
        清空缓存

        Args:
            symbol: 交易对，None表示所有
            timeframe: 时间周期，None表示所有
        """
        with self._lock:
            if symbol is None:
                self._cache.clear()
            elif symbol in self._cache:
                if timeframe is None:
                    del self._cache[symbol]
                elif timeframe in self._cache[symbol]:
                    self._cache[symbol][timeframe].clear()

        logger.info(f"Cleared cache for {symbol or 'all'}/{timeframe or 'all'}")

    def save_to_file(self, symbol: str, timeframe: str):
        """
        保存到文件

        Args:
            symbol: 交易对
            timeframe: 时间周期
        """
        candles = self.get_candles(symbol, timeframe)

        if not candles:
            logger.warning(f"No candles to save for {symbol} {timeframe}")
            return

        # 生成文件名
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        filename = f"{safe_symbol}_{timeframe}.json"
        filepath = self.data_path / filename

        # 转换为可JSON序列化的格式
        data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(candles),
            "candles": [[int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])] for c in candles]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(candles)} candles to {filepath}")

    def load_from_file(self, symbol: str, timeframe: str) -> int:
        """
        从文件加载

        Args:
            symbol: 交易对
            timeframe: 时间周期

        Returns:
            加载的K线数量
        """
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        filename = f"{safe_symbol}_{timeframe}.json"
        filepath = self.data_path / filename

        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return 0

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            candles = data.get("candles", [])
            self.add_candles(symbol, timeframe, candles)

            logger.info(f"Loaded {len(candles)} candles from {filepath}")
            return len(candles)

        except Exception as e:
            logger.error(f"Failed to load from {filepath}: {e}")
            return 0

    def save_all(self):
        """保存所有数据到文件"""
        with self._lock:
            items = [
                (symbol, timeframe, list(self._cache[symbol][timeframe]))
                for symbol in self._cache
                for timeframe in self._cache[symbol]
            ]

        for symbol, timeframe, _ in items:
            self.save_to_file(symbol, timeframe)

    def __repr__(self):
        return f"CandleStore(path={self.data_path}, cached_symbols={len(self._cache)})"
