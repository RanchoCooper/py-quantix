"""
市场数据获取模块
支持从交易所获取K线数据、实时行情、账户信息等
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from datetime import timezone

import ccxt

from loguru import logger
from config.settings import get_settings


class MarketFetcher:
    """市场数据获取器"""

    def __init__(
        self,
        exchange_id: str = "binance",
        testnet: bool = True,
        config_path: Optional[str] = None,
    ):
        """
        初始化市场数据获取器

        Args:
            exchange_id: 交易所ID
            testnet: 是否使用测试网络
            config_path: 配置文件路径
        """
        self.settings = get_settings(config_path)
        self.exchange_id = exchange_id
        self.testnet = testnet

        # 初始化交易所
        self._init_exchange()

    def _init_exchange(self):
        """初始化交易所实例"""
        exchange_config = self.settings.exchange

        # 创建交易所实例
        exchange_class = getattr(ccxt, self.exchange_id)

        config = {
            "enableRateLimit": True,
            "options": {
                "defaultType": exchange_config.mode,
            }
        }

        # 测试网络配置
        if self.testnet:
            config["urls"] = {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api",
                }
            }

        # API密钥配置
        if exchange_config.api_key:
            config["apiKey"] = exchange_config.api_key
            config["secret"] = exchange_config.api_secret

            if exchange_config.passphrase:
                config["password"] = exchange_config.passphrase

        # 代理配置
        proxy_http = exchange_config.proxy.http
        proxy_https = exchange_config.proxy.https
        if proxy_http or proxy_https:
            config["proxy"] = {
                "http": proxy_http,
                "https": proxy_https,
            }

        self.exchange = exchange_class(config)

        # 设置合约模式
        if exchange_config.contract_type == "linear":
            self.exchange.options["defaultSettleCode"] = "USDT"

        logger.info(f"Initialized exchange: {self.exchange_id}, testnet: {self.testnet}")

    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
        since: Optional[int] = None,
    ) -> List[List]:
        """
        获取K线数据 (OHLCV)

        Args:
            symbol: 交易对，如 BTC/USDT:USDT 或 BTCUSDT
            timeframe: 时间周期
            limit: 数量
            since: 起始时间戳 (毫秒)

        Returns:
            K线数据列表 [[timestamp, open, high, low, close, volume], ...]
        """
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
        """
        获取当前行情

        Args:
            symbol: 交易对

        Returns:
            行情数据字典
        """
        try:
            ticker = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                symbol
            )
            return ticker

        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_tickers(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        批量获取行情

        Args:
            symbols: 交易对列表，None表示全部

        Returns:
            行情字典
        """
        try:
            tickers = await asyncio.to_thread(
                self.exchange.fetch_tickers,
                symbols
            )
            return tickers

        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            raise

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取订单簿

        Args:
            symbol: 交易对
            limit: 深度数量

        Returns:
            订单簿数据
        """
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

    async def fetch_funding_rate(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取资金费率 (合约)

        Args:
            symbol: 合约交易对

        Returns:
            资金费率数据
        """
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

    async def fetch_mark_price(self, symbol: str) -> Optional[float]:
        """
        获取标记价格 (合约)

        Args:
            symbol: 合约交易对

        Returns:
            标记价格
        """
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

    async def fetch_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取持仓信息 (合约)

        Args:
            symbol: 交易对

        Returns:
            持仓数据
        """
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
        """
        获取所有持仓 (合约)

        Returns:
            持仓列表
        """
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

    async def fetch_balance(self) -> Dict[str, Any]:
        """
        获取账户余额

        Returns:
            余额数据
        """
        try:
            balance = await asyncio.to_thread(
                self.exchange.fetch_balance
            )
            return balance

        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    def get_server_time(self) -> int:
        """获取服务器时间"""
        try:
            return self.exchange.fetch_time()
        except Exception as e:
            logger.warning(f"Failed to fetch server time: {e}")
            return int(datetime.now(timezone.utc).timestamp() * 1000)

    def get_markets(self) -> Dict[str, Any]:
        """获取市场信息"""
        try:
            return self.exchange.load_markets()
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """获取交易对信息"""
        markets = self.get_markets()
        return markets.get(symbol, {})

    def format_symbol(self, base: str, quote: str, settle: Optional[str] = None) -> str:
        """格式化交易对符号"""
        if settle and settle != quote:
            return f"{base}/{quote}:{settle}"
        return f"{base}/{quote}"

    def convert_symbol(self, symbol: str) -> str:
        """
        转换交易对格式

        Args:
            symbol: 交易对，如 BTCUSDT 或 BTC/USDT:USDT

        Returns:
            转换后的交易对
        """
        # 如果已经包含分隔符，直接返回
        if "/" in symbol:
            return symbol

        # 尝试匹配常见币种
        common_quotes = ["USDT", "BUSD", "USD", "BTC", "ETH"]
        for quote in common_quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"

        # 无法识别，返回原值
        return symbol

    async def close(self):
        """关闭连接"""
        pass
