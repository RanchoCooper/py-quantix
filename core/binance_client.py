"""
向后兼容模块 - 已弃用
请使用 data.fetchers.market_fetcher.ExchangeClient
"""
import warnings

from data.fetchers.market_fetcher import ExchangeClient

# 向后兼容别名
BinanceFuturesClient = ExchangeClient
BinanceMarketData = ExchangeClient

warnings.warn(
    "core.binance_client 已弃用，请使用 data.fetchers.market_fetcher.ExchangeClient",
    DeprecationWarning,
    stacklevel=2
)
