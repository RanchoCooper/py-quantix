import logging
from typing import Any, Dict, List, Optional, Tuple

from binance.client import Client
from binance.exceptions import BinanceAPIException

from domain.model.order import Order
from domain.model.symbol import Symbol
from domain.service.exchange_service import ExchangeService


class BinanceExchangeAdapter(ExchangeService):
    """Binance exchange adapter implementation."""

    def __init__(
        self, api_key: str = None, api_secret: str = None, testnet: bool = False
    ):
        """
        Initialize Binance client.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Whether to use testnet
        """
        self.logger = logging.getLogger(__name__)
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.logger.info("Binance exchange adapter initialized")

    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information."""
        try:
            return self.client.get_exchange_info()
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get exchange info: {e}")
            raise

    def get_symbols(self) -> List[Symbol]:
        """Get all available trading symbols/pairs."""
        try:
            exchange_info = self.client.get_exchange_info()
            symbols = []

            for symbol_data in exchange_info["symbols"]:
                symbols.append(Symbol.from_dict(symbol_data))

            return symbols
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get symbols: {e}")
            raise

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for a specific symbol."""
        try:
            return self.client.get_ticker(symbol=symbol)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get ticker for {symbol}: {e}")
            raise

    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a specific symbol."""
        try:
            return self.client.get_order_book(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get order book for {symbol}: {e}")
            raise

    def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent trades for a specific symbol."""
        try:
            return self.client.get_recent_trades(symbol=symbol, limit=limit)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get recent trades for {symbol}: {e}")
            raise

    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[List[Any]]:
        """Get historical klines/candlesticks for a specific symbol and interval."""
        try:
            return self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_time,
                end_str=end_time,
                limit=limit,
            )
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get historical klines for {symbol}: {e}")
            raise

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: Optional[str] = None,
        **kwargs,
    ) -> Order:
        """Create a new order."""
        try:
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }

            # Add optional parameters
            if price is not None:
                params["price"] = price

            if time_in_force is not None:
                params["timeInForce"] = time_in_force

            # Add any additional parameters
            params.update(kwargs)

            result = self.client.create_order(**params)
            return Order.from_dict(result)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to create order for {symbol}: {e}")
            raise

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an existing order."""
        try:
            return self.client.cancel_order(symbol=symbol, orderId=order_id)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to cancel order {order_id} for {symbol}: {e}")
            raise

    def get_order(self, symbol: str, order_id: int) -> Order:
        """Get information about a specific order."""
        try:
            result = self.client.get_order(symbol=symbol, orderId=order_id)
            return Order.from_dict(result)
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get order {order_id} for {symbol}: {e}")
            raise

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders for a symbol or all symbols."""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol

            results = self.client.get_open_orders(**params)
            return [Order.from_dict(order_data) for order_data in results]
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get open orders: {e}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balances."""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get account info: {e}")
            raise

    def get_account_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """Get account balance for specific asset or all assets."""
        try:
            account = self.client.get_account()
            balances = {}

            for balance in account["balances"]:
                if float(balance["free"]) > 0 or float(balance["locked"]) > 0:
                    asset_name = balance["asset"]
                    balances[asset_name] = {
                        "free": float(balance["free"]),
                        "locked": float(balance["locked"]),
                        "total": float(balance["free"]) + float(balance["locked"]),
                    }

            if asset:
                return balances.get(asset, {"free": 0.0, "locked": 0.0, "total": 0.0})

            return balances
        except BinanceAPIException as e:
            self.logger.error(f"Failed to get account balance: {e}")
            raise
