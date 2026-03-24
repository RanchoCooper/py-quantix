"""
Binance 官方 API 客户端
使用 python-binance 库实现
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Optional, List, Dict

from binance.client import Client
from binance.exceptions import BinanceAPIException
from loguru import logger

from config.settings import get_settings


class BinanceClient:
    """
    Binance 官方 API 客户端

    使用 python-binance 库，支持：
    - 市场数据获取（K线、行情、订单簿等）
    - 账户操作（余额、持仓）
    - 交易操作（下单、杠杆设置）

    注意：使用延迟初始化，Client 对象在实际调用 API 时才创建
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        testnet: bool = True,
        config_path: Optional[str] = None,
        settings: Optional[Any] = None,
    ):
        """
        初始化 Binance 客户端

        Args:
            exchange_id: 交易所ID（目前仅支持 binance）
            testnet: 是否使用测试网络
            config_path: 配置文件路径
            settings: 已加载的 Settings 实例（可选）
        """
        # 使用传入的 settings 或重新加载
        self.settings = settings if settings is not None else get_settings(config_path)
        self.exchange_id = exchange_id
        self.testnet = testnet
        # 延迟初始化 Client 对象
        self._client: Optional[Client] = None
        self._proxy_config: Optional[Any] = None

        # 预先获取代理配置
        self._init_proxy_config()

        logger.info(f"Initialized Binance client (lazy), testnet: {self.testnet}")

    def _init_proxy_config(self) -> None:
        """预先获取代理配置"""
        proxy_config = self.settings.exchange.proxy if hasattr(self.settings.exchange, 'proxy') else None
        if not proxy_config:
            proxy_config = self.settings.llm.proxy if hasattr(self.settings.llm, 'proxy') else None
        self._proxy_config = proxy_config

    @property
    def client(self) -> Client:
        """延迟初始化 Client 对象"""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> Client:
        """创建 Binance Client 对象"""
        exchange_config = self.settings.exchange

        # 准备 requests_params（代理配置）
        requests_params = None
        if self._proxy_config and (self._proxy_config.http or self._proxy_config.https):
            proxy_url = self._proxy_config.https or self._proxy_config.http
            requests_params = {
                'proxies': {
                    'http': self._proxy_config.http,
                    'https': proxy_url,
                }
            }
            logger.info(f"使用代理: {proxy_url}")

        # 测试网络配置
        if self.testnet:
            if not exchange_config.api_key or not exchange_config.api_secret:
                raise ValueError(
                    "Binance API credentials are required. "
                    "Set EXCHANGE_API_KEY and EXCHANGE_API_SECRET environment variables."
                )
            client = Client(exchange_config.api_key, exchange_config.api_secret, testnet=True, requests_params=requests_params)
            logger.warning(
                "Binance Testnet 已迁移到新端点。"
                "如需使用测试环境，请配置 TESTNET=true 使用主网数据或自行搭建本地测试网。"
            )
        else:
            # 主网配置
            if not exchange_config.api_key or not exchange_config.api_secret:
                raise ValueError(
                    "Binance API credentials are required. "
                    "Set EXCHANGE_API_KEY and EXCHANGE_API_SECRET environment variables."
                )
            client = Client(
                exchange_config.api_key,
                exchange_config.api_secret,
                requests_params=requests_params,
            )

        return client

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
            symbol: 交易对，如 BTCUSDT 或 BTC/USDT:USDT
            timeframe: 时间周期 (1m, 5m, 15m, 1h, 4h, 1d 等)
            limit: 数量 (1-1000)
            since: 起始时间戳 (毫秒)

        Returns:
            K线数据列表 [[timestamp, open, high, low, close, volume], ...]
        """
        try:
            # 转换交易对格式 (BTC/USDT -> BTCUSDT)
            symbol = self._format_symbol(symbol)

            # 转换时间周期格式
            interval = self._convert_timeframe(timeframe)

            kwargs: Dict[str, Any] = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
            }

            if since:
                kwargs["startTime"] = since

            def _fetch():
                return self.client.get_klines(**kwargs)

            klines = await asyncio.to_thread(_fetch)

            # 转换为标准格式
            result = []
            for k in klines:
                result.append([
                    k[0],  # open time
                    float(k[1]),  # open
                    float(k[2]),  # high
                    float(k[3]),  # low
                    float(k[4]),  # close
                    float(k[5]),  # volume
                ])

            logger.debug(f"Fetched {len(result)} candles for {symbol}")
            return result

        except BinanceAPIException as e:
            logger.error(f"Binance API error fetching OHLCV for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {e}")
            raise

    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取当前行情"""
        try:
            symbol = self._format_symbol(symbol)

            def _fetch():
                return self.client.get_symbol_ticker(symbol=symbol)

            ticker = await asyncio.to_thread(_fetch)
            return {
                "symbol": ticker["symbol"],
                "lastPrice": float(ticker["price"]),
            }

        except BinanceAPIException as e:
            logger.error(f"Binance API error fetching ticker for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_tickers(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """批量获取行情"""
        try:
            def _fetch():
                return self.client.get_all_tickers()

            tickers = await asyncio.to_thread(_fetch)

            result = {}
            for t in tickers:
                if symbols:
                    # 过滤指定交易对
                    formatted_symbols = [self._format_symbol(s) for s in symbols]
                    if t["symbol"] in formatted_symbols:
                        result[t["symbol"]] = {"lastPrice": float(t["price"])}
                else:
                    result[t["symbol"]] = {"lastPrice": float(t["price"])}

            return result

        except BinanceAPIException as e:
            logger.error(f"Binance API error fetching tickers: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch tickers: {e}")
            raise

    async def get_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[List]]:
        """批量获取多个交易对的K线数据（异步版本）"""
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

    def fetch_klines(
        self,
        symbols: List[str],
        timeframe: str = "1h",
        limit: int = 100
    ) -> Dict[str, List[List]]:
        """批量获取多个交易对的K线数据（同步版本）"""
        return asyncio.run(self.get_multiple_symbols(symbols, timeframe, limit))

    async def fetch_order_book(
        self,
        symbol: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """获取订单簿"""
        try:
            symbol = self._format_symbol(symbol)

            def _fetch():
                return self.client.get_order_book(symbol=symbol, limit=limit)

            order_book = await asyncio.to_thread(_fetch)

            return {
                "bids": [[float(p), float(q)] for p, q in order_book["bids"]],
                "asks": [[float(p), float(q)] for p, q in order_book["asks"]],
            }

        except BinanceAPIException as e:
            logger.error(f"Binance API error fetching order book for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch order book for {symbol}: {e}")
            raise

    # ==================== 账户操作 ====================

    async def fetch_balance(self) -> Dict[str, Any]:
        """获取账户余额"""
        try:
            def _fetch():
                return self.client.get_account()

            account = await asyncio.to_thread(_fetch)

            balances = {}
            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                if free > 0 or locked > 0:
                    balances[balance["asset"]] = {
                        "free": free,
                        "locked": locked,
                        "total": free + locked,
                    }

            return {"info": account, "total": balances}

        except BinanceAPIException as e:
            logger.error(f"Binance API error fetching balance: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch balance: {e}")
            raise

    async def fetch_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取持仓信息 (合约)"""
        try:
            symbol = self._format_symbol(symbol)

            def _fetch():
                return self.client.futures_position_information(symbol=symbol)

            positions = await asyncio.to_thread(_fetch)

            if positions:
                pos = positions[0]
                return {
                    "symbol": pos["symbol"],
                    "positionAmt": float(pos["positionAmt"]),
                    "entryPrice": float(pos["entryPrice"]),
                    "unrealizedProfit": float(pos["unrealizedProfit"]),
                }
            return None

        except BinanceAPIException as e:
            logger.warning(f"Binance API error fetching position for {symbol}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch position for {symbol}: {e}")
            return None

    async def fetch_positions(self) -> List[Dict[str, Any]]:
        """获取所有持仓 (合约)"""
        try:
            def _fetch():
                return self.client.futures_position_information()

            positions = await asyncio.to_thread(_fetch)

            result = []
            for pos in positions:
                if float(pos["positionAmt"]) != 0:
                    result.append({
                        "symbol": pos["symbol"],
                        "positionAmt": float(pos["positionAmt"]),
                        "entryPrice": float(pos["entryPrice"]),
                        "unrealizedProfit": float(pos["unrealizedProfit"]),
                    })

            return result

        except BinanceAPIException as e:
            logger.warning(f"Binance API error fetching positions: {e}")
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch positions: {e}")
            return []

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
        """下订单"""
        try:
            symbol = self._format_symbol(symbol)

            order_params: Dict[str, Any] = {
                "symbol": symbol,
                "side": side.upper(),
                "quantity": quantity,
            }

            # 订单类型映射
            type_mapping = {
                "market": "MARKET",
                "limit": "LIMIT",
                "stop": "STOP",
                "take_profit": "TAKE_PROFIT",
            }
            order_params["type"] = type_mapping.get(order_type, order_type.upper())

            if price and order_type == "limit":
                order_params["price"] = price
                order_params["timeInForce"] = "GTC"

            if stop_price:
                order_params["stopPrice"] = stop_price

            if params:
                order_params.update(params)

            def _create():
                return self.client.create_order(**order_params)

            order = await asyncio.to_thread(_create)
            logger.info(f"Order created: {order['orderId']} - {side} {quantity} {symbol}")
            return order

        except BinanceAPIException as e:
            logger.error(f"Binance API error creating order: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create order: {e}")
            raise

    async def set_leverage(
        self,
        symbol: str,
        leverage: int,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """设置杠杆倍数"""
        try:
            symbol = self._format_symbol(symbol)

            def _set():
                return self.client.futures_change_leverage(
                    symbol=symbol,
                    leverage=leverage
                )

            result = await asyncio.to_thread(_set)
            logger.info(f"Leverage set for {symbol}: {leverage}x")
            return result

        except BinanceAPIException as e:
            logger.error(f"Binance API error setting leverage for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {e}")
            raise

    # ==================== 辅助方法 ====================

    def get_server_time(self) -> int:
        """获取服务器时间"""
        try:
            result = self.client.get_server_time()
            return result["serverTime"]
        except Exception as e:
            logger.warning(f"Failed to fetch server time: {e}")
            return int(datetime.now(timezone.utc).timestamp() * 1000)

    def get_markets(self) -> Dict[str, Any]:
        """获取市场信息"""
        try:
            return self.client.get_exchange_info()
        except Exception as e:
            logger.error(f"Failed to load markets: {e}")
            raise

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """获取交易对信息"""
        markets = self.get_markets()
        symbol = self._format_symbol(symbol)
        for s in markets.get("symbols", []):
            if s["symbol"] == symbol:
                return s
        return {}

    def format_symbol(
        self,
        base: str,
        quote: str,
        settle: Optional[str] = None
    ) -> str:
        """格式化交易对符号"""
        return f"{base}{quote}"

    def convert_symbol(self, symbol: str) -> str:
        """转换交易对格式"""
        if "/" in symbol:
            return self._format_symbol(symbol)
        return symbol

    def _format_symbol(self, symbol: str) -> str:
        """格式化交易对为 Binance 格式 (BTCUSDT)"""
        # 已经是正确格式
        if not "/" in symbol and ":" not in symbol:
            return symbol

        # 移除 :settle 部分 (BTC/USDT:USDT -> BTC/USDT)
        if ":" in symbol:
            symbol = symbol.split(":")[0]

        # 移除 / (BTC/USDT -> BTCUSDT)
        return symbol.replace("/", "")

    def _convert_timeframe(self, timeframe: str) -> str:
        """转换时间周期格式"""
        mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
            "6h": "6h",
            "8h": "8h",
            "12h": "12h",
            "1d": "1d",
            "3d": "3d",
            "1w": "1w",
            "1M": "1M",
        }
        return mapping.get(timeframe, timeframe)

    async def close(self) -> None:
        """关闭连接"""
        pass

    def __repr__(self) -> str:
        return f"BinanceClient(testnet={self.testnet})"
