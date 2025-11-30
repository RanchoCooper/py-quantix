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
    
    该类封装了与币安期货API交互所需的所有功能，包括账户信息查询、
    K线数据获取、订单下单等操作。支持实盘和测试网环境切换。
    """

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        初始化币安期货客户端

        Args:
            api_key (str): 币安API密钥，用于身份验证
            api_secret (str): 币安API密钥，用于请求签名
            testnet (bool, optional): 是否使用测试网环境. 默认为 True.
            
        Attributes:
            api_key (str): API密钥
            api_secret (str): API密钥
            testnet (bool): 是否使用测试网
            base_url (str): API基础URL
            session (requests.Session): HTTP会话对象
            
        Example:
            >>> client = BinanceFuturesClient("your_api_key", "your_api_secret", testnet=True)
            >>> logger.info("客户端初始化成功")
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
        为API请求生成HMAC SHA256签名

        Args:
            params (Dict[str, Any]): 需要签名的请求参数字典

        Returns:
            str: 生成的十六进制签名字符串
            
        Note:
            该方法是内部方法，用于为需要签名的API请求生成必要的认证签名。
            参数字典会被编码为URL查询字符串，然后使用HMAC SHA256算法签名。
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
            method (str): HTTP方法 ('GET', 'POST', 'DELETE', 等)
            endpoint (str): API端点路径 (例如: '/fapi/v2/account')
            params (Optional[Dict[str, Any]], optional): 请求参数. 默认为 None.
            signed (bool, optional): 请求是否需要签名. 默认为 False.

        Returns:
            Dict[str, Any]: API响应的JSON数据
            
        Raises:
            requests.exceptions.RequestException: 当HTTP请求失败时抛出
            
        Example:
            >>> response = self._send_request("GET", "/fapi/v2/ping")
            >>> print(response)
            {'code': 200, 'msg': 'success'}
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
        获取账户信息，包括余额、持仓、交易权限等

        Returns:
            Dict[str, Any]: 包含账户详细信息的字典
            
        Example:
            >>> account_info = client.get_account_info()
            >>> print(account_info['assets'][0])
            {'asset': 'USDT', 'walletBalance': '1000.00000000', ...}
        """
        return self._send_request("GET", "/fapi/v2/account", signed=True)

    def get_balance(self) -> Dict[str, Any]:
        """
        获取账户资产余额信息

        Returns:
            Dict[str, Any]: 包含各资产余额信息的列表
            
        Example:
            >>> balance = client.get_balance()
            >>> print(balance[0])
            {'accountAlias': 'SgsR', 'asset': 'USDT', 'balance': '1000.00000000', ...}
        """
        return self._send_request("GET", "/fapi/v2/balance", signed=True)

    def get_positions(self) -> Dict[str, Any]:
        """
        获取当前持仓风险信息

        Returns:
            Dict[str, Any]: 包含当前持仓信息的列表
            
        Example:
            >>> positions = client.get_positions()
            >>> print(positions[0])
            {'symbol': 'BTCUSDT', 'positionAmt': '0.000', 'entryPrice': '0.00000000', ...}
        """
        return self._send_request("GET", "/fapi/v2/positionRisk", signed=True)

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> Dict[str, Any]:
        """
        获取指定交易对的K线/烛台数据

        Args:
            symbol (str): 交易对符号 (例如: 'BTCUSDT')
            interval (str): K线间隔 ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M')
            limit (int, optional): 返回的K线数量. 默认为 500. 最大值为1500.

        Returns:
            Dict[str, Any]: K线数据列表，每个元素包含开盘价、最高价、最低价、收盘价等信息
            
        Example:
            >>> klines = client.get_klines("BTCUSDT", "1h", limit=100)
            >>> print(len(klines))
            100
            >>> print(klines[0])
            [1617590400000, '57648.57', '57715.00', '57560.00', '57663.21', '305.94734000', 1617590699999, '17644864.26770240', 1234, '153.23582000', '8827865.18270240', '0']
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
            symbol (str): 交易对符号 (例如: 'BTCUSDT')
            side (str): 订单方向 ('BUY' 或 'SELL')
            order_type (str): 订单类型 ('LIMIT', 'MARKET', 'STOP', 'TAKE_PROFIT', 等)
            quantity (float): 订单数量
            price (Optional[float], optional): 订单价格 (限价单需要). 默认为 None.
            stop_price (Optional[float], optional): 止损价格 (止损单需要). 默认为 None.
            time_in_force (str, optional): 有效时间 ('GTC', 'IOC', 'FOK'). 默认为 'GTC'.

        Returns:
            Dict[str, Any]: 订单信息
            
        Example:
            >>> order = client.place_order(
            ...     symbol="BTCUSDT",
            ...     side="BUY",
            ...     order_type="MARKET",
            ...     quantity=0.001
            ... )
            >>> print(order['orderId'])
            123456789
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
        为指定交易对设置杠杆倍数

        Args:
            symbol (str): 交易对符号 (例如: 'BTCUSDT')
            leverage (int): 杠杆倍数 (范围: 1-125)

        Returns:
            Dict[str, Any]: 响应信息
            
        Example:
            >>> response = client.set_leverage("BTCUSDT", 10)
            >>> print(response['leverage'])
            10
        """
        params = {
            "symbol": symbol,
            "leverage": leverage
        }
        return self._send_request("POST", "/fapi/v1/leverage", params, signed=True)

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取指定交易对的交易所信息

        Args:
            symbol (str): 交易对符号 (例如: 'BTCUSDT')

        Returns:
            Dict[str, Any]: 交易对信息，包括价格精度、数量精度、交易限制等
            
        Example:
            >>> symbol_info = client.get_symbol_info("BTCUSDT")
            >>> print(symbol_info['symbols'][0]['symbol'])
            BTCUSDT
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
