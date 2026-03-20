"""
市场数据获取与交易模块
基于 ccxt 统一实现，支持多交易所
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional, List, Dict

import ccxt

from loguru import logger
from config.settings import get_settings


class ExchangeClient:
    """
    统一的交易所客户端，封装市场数据获取和交易功能

    基于 ccxt 实现，支持：
    - 市场数据获取（K线、行情、订单簿等）
    - 账户操作（余额、持仓）
    - 交易操作（下单、杠杆设置）
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        testnet: bool = True,
        config_path: Optional[str] = None,
    ):
        """
        初始化交易所客户端

        Args:
            exchange_id: 交易所ID
            testnet: 是否使用测试网络
            config_path: 配置文件路径
        """
        self.settings = get_settings(config_path)
        self.exchange_id = exchange_id
        self.testnet = testnet
        self.exchange: Optional[ccxt.Exchange] = None

        # 初始化交易所实例
        self._init_exchange()

    def _init_exchange(self) -> None:
        """初始化交易所实例"""
        exchange_config = self.settings.exchange

        # 创建交易所实例
        exchange_class: type[ccxt.Exchange] = getattr(ccxt, self.exchange_id)

        config: Dict[str, Any] = {
            "enableRateLimit": True,
            "options": {
                "defaultType": exchange_config.mode,
            }
        }

        # 测试网络配置 - Binance Testnet
        if self.testnet:
            config["urls"] = {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api",
                }
            }
            # 使用现货市场
            config["options"] = {"defaultType": "spot"}

        # API密钥配置
        if exchange_config.api_key:
            config["apiKey"] = exchange_config.api_key
            config["secret"] = exchange_config.api_secret

            if exchange_config.passphrase:
                config["password"] = exchange_config.passphrase

        # 代理配置 - 从 exchange 或 llm 配置中获取
        proxy_config = self.settings.exchange.proxy if hasattr(self.settings.exchange, 'proxy') else None
        if not proxy_config:
            proxy_config = self.settings.llm.proxy if hasattr(self.settings.llm, 'proxy') else None

        if proxy_config:
            proxy_http = proxy_config.http
            proxy_https = proxy_config.https
            if proxy_http or proxy_https:
                config["proxy"] = {
                    "http": proxy_http,
                    "https": proxy_https,
                }
                logger.info(f"使用代理: HTTP={proxy_http}, HTTPS={proxy_https}")

        self.exchange = exchange_class(config)

        # 设置合约模式
        if exchange_config.contract_type == "linear":
            self.exchange.options["defaultSettleCode"] = "USDT"

        logger.info(f"Initialized exchange: {self.exchange_id}, testnet: {self.testnet}")

    # ==================== 市场数据获取 ====================

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
        """获取当前行情"""
        try:
            ticker = await asyncio.to_thread(
                self.exchange.fetch_ticker,
                symbol
            )
            return ticker
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_tickers(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """批量获取行情"""
        try:
            tickers = await asyncio.to_thread(
                self.exchange.fetch_tickers,
                symbols
            )
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
        """
        批量获取多个交易对的K线数据

        Args:
            symbols: 交易对列表
            timeframe: K线周期
            limit: 获取数量

        Returns:
            {symbol: klines} 字典
        """
        import time

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

            time.sleep(0.2)  # 避免请求过快

        logger.info(f"成功获取 {len(results)}/{len(symbols)} 个交易对的数据")
        return results

    def fetch_klines(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[List]]:
        """
        同步版本：批量获取多个交易对的K线数据

        Args:
            symbols: 交易对列表
            timeframe: K线周期
            limit: 获取数量

        Returns:
            {symbol: klines} 字典
        """
        import time

        results: Dict[str, List[List]] = {}
        for symbol in symbols:
            try:
                klines = asyncio.run(self.fetch_ohlcv(symbol, timeframe, limit))
                if klines:
                    results[symbol] = klines
                else:
                    logger.warning(f"获取 {symbol} 数据失败")
            except Exception as e:
                logger.warning(f"获取 {symbol} 数据失败: {e}")

            time.sleep(0.2)  # 避免请求过快

        logger.info(f"成功获取 {len(results)}/{len(symbols)} 个交易对的数据")
        return results

    async def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取订单簿"""
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
        """获取标记价格 (合约)"""
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

    # ==================== 账户操作 ====================

    async def fetch_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        try:
            balance = await asyncio.to_thread(
                self.exchange.fetch_balance
            )
            return balance
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    async def fetch_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓信息 (合约)"""
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
        """获取所有持仓 (合约)"""
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
        """获取资金费率 (合约)"""
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

    # ==================== 交易操作 ====================

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
        """
        下订单

        Args:
            symbol: 交易对
            side: 订单方向 ('buy' 或 'sell')
            order_type: 订单类型 ('market', 'limit', 'stop', 'take_profit')
            quantity: 订单数量
            price: 订单价格 (限价单需要)
            stop_price: 止损价格
            params: 其他参数

        Returns:
            订单信息
        """
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
        """
        设置杠杆倍数

        Args:
            symbol: 交易对
            leverage: 杠杆倍数 (1-125)
            params: 其他参数

        Returns:
            设置结果
        """
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

    # ==================== 辅助方法 ====================

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

    def format_symbol(
        self,
        base: str,
        quote: str,
        settle: Optional[str] = None
    ) -> str:
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

    async def close(self) -> None:
        """关闭连接"""
        pass

    def __repr__(self) -> str:
        return f"ExchangeClient({self.exchange_id}, testnet={self.testnet})"


# 保留别名以兼容旧代码
MarketFetcher = ExchangeClient
