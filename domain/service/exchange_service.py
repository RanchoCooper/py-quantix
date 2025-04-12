from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from domain.model.order import Order
from domain.model.symbol import Symbol


class ExchangeService(ABC):
    """Exchange service interface for interacting with cryptocurrency exchanges."""

    @abstractmethod
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information."""
        pass

    @abstractmethod
    def get_symbols(self) -> List[Symbol]:
        """Get all available trading symbols/pairs."""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get ticker information for a specific symbol."""
        pass

    @abstractmethod
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book for a specific symbol."""
        pass

    @abstractmethod
    def get_recent_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get recent trades for a specific symbol."""
        pass

    @abstractmethod
    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[List[Any]]:
        """Get historical klines/candlesticks for a specific symbol and interval."""
        pass

    @abstractmethod
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: Optional[str] = None,
        **kwargs
    ) -> Order:
        """Create a new order."""
        pass

    @abstractmethod
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass

    @abstractmethod
    def get_order(self, symbol: str, order_id: int) -> Order:
        """Get information about a specific order."""
        pass

    @abstractmethod
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders for a symbol or all symbols."""
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balances."""
        pass

    @abstractmethod
    def get_account_balance(self, asset: Optional[str] = None) -> Dict[str, float]:
        """Get account balance for specific asset or all assets."""
        pass
