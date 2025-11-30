import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from loguru import logger


class BinanceFuturesClient:
    """
    币安期货API客户端，用于量化交易
    """

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        初始化币安期货客户端

        Args:
            api_key: 币安API密钥
            api_secret: 币安API密钥
            testnet: 是否使用测试网 (默认: True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"

        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key
        })

        logger.info(f"币安期货客户端初始化完成. 测试网: {testnet}")

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        为API请求生成签名

        Args:
            params: 请求参数

        Returns:
            签名字符串
        """
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _send_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Dict[str, Any]:
        """
        发送HTTP请求到币安API

        Args:
            method: HTTP方法 (GET, POST, DELETE, 等)
            endpoint: API端点
            params: 请求参数
            signed: 请求是否需要签名

        Returns:
            JSON响应
        """
        if params is None:
            params = {}

        # 为签名请求添加时间戳
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息

        Returns:
            账户信息
        """
        return self._send_request("GET", "/fapi/v2/account", signed=True)

    def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额

        Returns:
            账户余额信息
        """
        return self._send_request("GET", "/fapi/v2/balance", signed=True)

    def get_positions(self) -> Dict[str, Any]:
        """
        获取当前持仓

        Returns:
            当前持仓信息
        """
        return self._send_request("GET", "/fapi/v2/positionRisk", signed=True)

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> Dict[str, Any]:
        """
        获取K线/烛台数据

        Args:
            symbol: 交易对 (例如: BTCUSDT)
            interval: K线间隔 (1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: 返回的K线数量 (默认: 500)

        Returns:
            K线数据
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        return self._send_request("GET", "/fapi/v1/klines", params)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                   price: Optional[float] = None, stop_price: Optional[float] = None,
                   time_in_force: str = "GTC") -> Dict[str, Any]:
        """
        下订单

        Args:
            symbol: 交易对
            side: 订单方向 (BUY 或 SELL)
            order_type: 订单类型 (LIMIT, MARKET, STOP, TAKE_PROFIT, 等)
            quantity: 订单数量
            price: 订单价格 (限价单需要)
            stop_price: 止损价格 (止损单需要)
            time_in_force: 有效时间 (GTC, IOC, FOK)

        Returns:
            订单信息
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "timeInForce": time_in_force
        }

        if price is not None:
            params["price"] = price

        if stop_price is not None:
            params["stopPrice"] = stop_price

        return self._send_request("POST", "/fapi/v1/order", params, signed=True)

    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        为交易对设置杠杆

        Args:
            symbol: 交易对
            leverage: 杠杆倍数

        Returns:
            响应信息
        """
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        return self._send_request("POST", "/fapi/v1/leverage", params, signed=True)

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取交易对信息

        Args:
            symbol: 交易对

        Returns:
            交易对信息
        """
        params = {"symbol": symbol}
        return self._send_request("GET", "/fapi/v1/exchangeInfo", params)


# 示例用法
if __name__ == "__main__":
    # 加载配置 (实际使用中从配置文件加载)
    config = {
        "api_key": "your_api_key",
        "api_secret": "your_api_secret",
        "testnet": True
    }

    client = BinanceFuturesClient(
        config["api_key"],
        config["api_secret"],
        config["testnet"]
    )

    # 示例: 获取账户信息
    try:
        account_info = client.get_account_info()
        print("账户信息:", account_info)
    except Exception as e:
        print(f"获取账户信息错误: {e}")
