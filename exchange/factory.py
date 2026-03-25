"""
交易所客户端工厂
根据配置创建合适的交易所客户端
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ccxt
from loguru import logger

from config.settings import get_settings

# 延迟导入以避免循环依赖
_binance_client = None


def _get_binance_client():
    """延迟导入 Binance 官方客户端"""
    global _binance_client
    if _binance_client is None:
        from exchange.binance_client import BinanceClient
        _binance_client = BinanceClient
    return _binance_client


def create_exchange_client(
    exchange_id: str = "binance",
    testnet: bool = True,
    config_path: Optional[str] = "config/config.yaml",
) -> "ExchangeClientImpl":
    """
    根据配置创建合适的交易所客户端

    Args:
        exchange_id: 交易所ID
        testnet: 是否使用测试网络
        config_path: 配置文件路径

    Returns:
        ExchangeClientImpl 实例
    """
    return ExchangeClientImpl(
        exchange_id=exchange_id,
        testnet=testnet,
        config_path=config_path,
    )


class ExchangeClientImpl:
    """
    统一的交易所客户端，封装市场数据获取和交易功能

    支持两种实现方式：
    - ccxt: 统一交易所 API，支持多交易所
    - binance: Binance 官方 API (python-binance)

    特性：
    - 市场数据获取（K线、行情、订单簿等）
    - 账户操作（余额、持仓）
    - 交易操作（下单、杠杆设置）
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        testnet: bool = True,
        config_path: Optional[str] = "config/config.yaml",
    ):
        self.settings = get_settings(config_path)
        self.exchange_id = exchange_id
        self.testnet = testnet
        self.api_client_type = self.settings.exchange.api_client
        self.exchange: Optional[ccxt.Exchange] = None
        self._binance_client: Any = None
        self._init_exchange()

    def _init_exchange(self) -> None:
        """初始化交易所实例"""
        exchange_config = self.settings.exchange

        if exchange_config.api_client == "binance" and self.exchange_id == "binance":
            BinanceClientClass = _get_binance_client()
            self._binance_client = BinanceClientClass(
                exchange_id=self.exchange_id,
                testnet=self.testnet,
                settings=self.settings,
            )
            logger.info(f"使用 Binance 官方 API 客户端 (testnet: {self.testnet})")
            return

        exchange_class: type[ccxt.Exchange] = getattr(ccxt, self.exchange_id)
        config: Dict[str, Any] = {
            "enableRateLimit": True,
            "options": {
                "defaultType": exchange_config.mode,
            }
        }

        if self.testnet:
            config["urls"] = {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api",
                }
            }
            config["options"] = {"defaultType": "spot"}

        if exchange_config.api_key:
            config["apiKey"] = exchange_config.api_key
            config["secret"] = exchange_config.api_secret
            if exchange_config.passphrase:
                config["password"] = exchange_config.passphrase

        proxy_config = self.settings.exchange.proxy if hasattr(self.settings.exchange, 'proxy') else None
        if not proxy_config:
            proxy_config = self.settings.llm.proxy if hasattr(self.settings.llm, 'proxy') else None

        if proxy_config:
            proxy_url = proxy_config.https or proxy_config.http
            if proxy_url:
                config["proxy"] = proxy_url.rstrip('/') + '/'
                logger.info(f"使用代理: {config['proxy']}")

        self.exchange = exchange_class(config)

        if exchange_config.contract_type == "linear":
            self.exchange.options["defaultSettleCode"] = "USDT"

        logger.info(f"Initialized exchange: {self.exchange_id}, testnet: {self.testnet}, client: ccxt")

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        since: Optional[int] = None,
    ) -> List[List]:
        if self._binance_client:
            return await self._binance_client.fetch_ohlcv(symbol, timeframe, limit, since)

        try:
            ohlcv = await asyncio.to_thread(
                self.exchange.fetch_ohlcv,
                symbol,
                timeframe,
                since,
                limit
            )
            logger.debug(f"Fetched {len(ohlcv)} candles for {symbol}")
            return ohlcv
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        if self._binance_client:
            return await self._binance_client.fetch_ticker(symbol)

        try:
            ticker = await asyncio.to_thread(self.exchange.fetch_ticker, symbol)
            return ticker
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_tickers(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if self._binance_client:
            return await self._binance_client.fetch_tickers(symbols)

        try:
            tickers = await asyncio.to_thread(self.exchange.fetch_tickers, symbols)
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            raise

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[List]]:
        if self._binance_client:
            return await self._binance_client.get_multiple_symbols(symbols, timeframe, limit)
        return await self._fetch_symbols_impl(symbols, timeframe, limit, async_mode=True)

    def fetch_klines(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[List]]:
        if self._binance_client:
            return self._binance_client.fetch_klines(symbols, timeframe, limit)
        return asyncio.run(self._fetch_symbols_impl(symbols, timeframe, limit))

    async def _fetch_symbols_impl(
        self,
        symbols: List[str],
        timeframe: str,
        limit: int,
    ) -> Dict[str, List[List]]:
        results: Dict[str, List[List]] = {}
        for symbol in symbols:
            try:
                klines = await self.fetch_ohlcv(symbol, timeframe, limit)
                if klines:
                    results[symbol] = klines
                else:
                    logger.warning(f"获取 {symbol} 数据失败")
            except Exception as e:
                logger.warning(f"获取 {symbol} 数据失败: {e}")
            time.sleep(0.2)
        logger.info(f"成功获取 {len(results)}/{len(symbols)} 个交易对的数据")
        return results

    async def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        if self._binance_client:
            return await self._binance_client.fetch_order_book(symbol, limit)

        try:
            order_book = await asyncio.to_thread(
                self.exchange.fetch_order_book,
                symbol,
                limit
            )
            return order_book
        except Exception as e:
            logger.error(f"Failed to fetch order book for {symbol}: {e}")
            raise

    async def fetch_mark_price(self, symbol: str) -> Optional[float]:
        if self._binance_client:
            return None

        try:
            if hasattr(self.exchange, "fetch_mark_price"):
                mark_price = await asyncio.to_thread(
                    self.exchange.fetch_mark_price,
                    symbol
                )
                return mark_price.get("markPrice")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch mark price for {symbol}: {e}")
            return None

    async def fetch_balance(self) -> Dict[str, Any]:
        if self._binance_client:
            return await self._binance_client.fetch_balance()

        try:
            balance = await asyncio.to_thread(self.exchange.fetch_balance)
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    async def fetch_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        if self._binance_client:
            return await self._binance_client.fetch_position(symbol)

        try:
            if hasattr(self.exchange, "fetch_position"):
                position = await asyncio.to_thread(
                    self.exchange.fetch_position,
                    symbol
                )
                return position
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch position for {symbol}: {e}")
            return None

    async def fetch_positions(self) -> List[Dict[str, Any]]:
        if self._binance_client:
            return await self._binance_client.fetch_positions()

        try:
            if hasattr(self.exchange, "fetch_positions"):
                positions = await asyncio.to_thread(
                    self.exchange.fetch_positions
                )
                return positions
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch positions: {e}")
            return []

    async def fetch_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        if self._binance_client:
            return None

        try:
            if hasattr(self.exchange, "fetch_funding_rate"):
                funding_rate = await asyncio.to_thread(
                    self.exchange.fetch_funding_rate,
                    symbol
                )
                return funding_rate
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch funding rate for {symbol}: {e}")
            return None

    async def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if side not in ("buy", "sell"):
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'.")
        if order_type not in ("market", "limit", "stop", "take_profit"):
            raise ValueError(f"Invalid order_type: {order_type}.")

        if self._binance_client:
            return await self._binance_client.create_order(
                symbol, side, order_type, quantity, price, stop_price, params
            )

        try:
            order_params = params or {}
            if stop_price:
                order_params["stopPrice"] = stop_price

            order = await asyncio.to_thread(
                self.exchange.create_order,
                symbol,
                order_type,
                side,
                quantity,
                price,
                order_params
            )
            logger.info(f"Order created: {order['id']} - {side} {quantity} {symbol}")
            return order
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise

    async def set_leverage(
        self,
        symbol: str,
        leverage: int,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if self._binance_client:
            return await self._binance_client.set_leverage(symbol, leverage, params)

        try:
            result = await asyncio.to_thread(
                self.exchange.set_leverage,
                leverage,
                symbol,
                params
            )
            logger.info(f"Leverage set for {symbol}: {leverage}x")
            return result
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {e}")
            raise

    def get_server_time(self) -> int:
        if self._binance_client:
            return self._binance_client.get_server_time()

        try:
            return self.exchange.fetch_time()
        except Exception as e:
            logger.warning(f"Failed to fetch server time: {e}")
            return int(datetime.now(timezone.utc).timestamp() * 1000)

    def get_markets(self) -> Dict[str, Any]:
        if self._binance_client:
            return self._binance_client.get_markets()

        try:
            return self.exchange.load_markets()
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        markets = self.get_markets()
        return markets.get(symbol, {})

    def format_symbol(
        self,
        base: str,
        quote: str,
        settle: Optional[str] = None
    ) -> str:
        if settle and settle != quote:
            return f"{base}/{quote}:{settle}"
        return f"{base}/{quote}"

    def convert_symbol(self, symbol: str) -> str:
        if "/" in symbol:
            return symbol

        common_quotes = ["USDT", "BUSD", "USD", "BTC", "ETH"]
        for quote in common_quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        return symbol

    async def close(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"ExchangeClientImpl({self.exchange_id}, testnet={self.testnet})"


# 模块级缓存
_client_cache: Dict[str, Any] = {}
