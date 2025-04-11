"""
Trading application service.

This module provides the application service for trading operations.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from domain.model.errors import (
    EntityNotFoundError, ExchangeError, InsufficientBalanceError,
    InvalidOrderError, OrderNotFoundError, StrategyNotFoundError,
    StrategyValidationError, SymbolNotFoundError
)
from domain.model.order import Order
from domain.model.strategy import Strategy
from domain.model.symbol import Symbol
from domain.model.trade import Trade
from domain.service.order_service import OrderService
from domain.service.strategy_service import StrategyService
from domain.service.symbol_service import SymbolService

logger = logging.getLogger(__name__)


class TradingAppService:
    """
    Application service for trading operations.
    
    This service provides a facade for trading-related operations, coordinating
    the domain services and mapping between DTOs and domain objects.
    """
    
    def __init__(self, symbol_service: SymbolService, strategy_service: StrategyService,
                order_service: OrderService):
        """
        Initialize the trading application service.
        
        Args:
            symbol_service: Symbol domain service
            strategy_service: Strategy domain service
            order_service: Order domain service
        """
        self._symbol_service = symbol_service
        self._strategy_service = strategy_service
        self._order_service = order_service
        logger.info("Initialized Trading application service")
    
    # Symbol operations
    
    def sync_symbols(self) -> List[Dict]:
        """
        Synchronize symbols from the exchange.
        
        Returns:
            List of synchronized symbols as dictionaries
        """
        try:
            symbols = self._symbol_service.sync_symbols()
            return [symbol.to_dict() for symbol in symbols]
        except ExchangeError as e:
            logger.error(f"Error synchronizing symbols: {e}")
            raise
    
    def get_symbol(self, symbol_id: str) -> Dict:
        """
        Get a symbol by its ID.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            Symbol as a dictionary
            
        Raises:
            SymbolNotFoundError: If the symbol is not found
        """
        try:
            symbol = self._symbol_service.get_symbol(symbol_id)
            return symbol.to_dict()
        except SymbolNotFoundError as e:
            logger.error(f"Symbol not found: {e}")
            raise
    
    def get_symbol_by_name(self, name: str) -> Dict:
        """
        Get a symbol by its name.
        
        Args:
            name: Symbol name (e.g., "BTCUSDT")
            
        Returns:
            Symbol as a dictionary
            
        Raises:
            SymbolNotFoundError: If the symbol is not found
        """
        try:
            symbol = self._symbol_service.get_symbol_by_name(name)
            return symbol.to_dict()
        except SymbolNotFoundError as e:
            logger.error(f"Symbol not found: {e}")
            raise
    
    def get_all_symbols(self) -> List[Dict]:
        """
        Get all symbols.
        
        Returns:
            List of symbols as dictionaries
        """
        symbols = self._symbol_service.get_all_symbols()
        return [symbol.to_dict() for symbol in symbols]
    
    def get_ticker(self, symbol_name: str) -> Dict:
        """
        Get ticker for a symbol.
        
        Args:
            symbol_name: Symbol name (e.g., "BTCUSDT")
            
        Returns:
            Ticker data as a dictionary
            
        Raises:
            ExchangeError: If there's an error with the exchange
        """
        try:
            return self._symbol_service.get_ticker(symbol_name)
        except ExchangeError as e:
            logger.error(f"Error getting ticker for {symbol_name}: {e}")
            raise
    
    def get_klines(self, symbol_name: str, interval: str, limit: int = 500) -> List[Dict]:
        """
        Get candlestick data for a symbol.
        
        Args:
            symbol_name: Symbol name (e.g., "BTCUSDT")
            interval: Kline interval (e.g., "1m", "1h", "1d")
            limit: Maximum number of candles to return
            
        Returns:
            List of candlestick data as dictionaries
            
        Raises:
            ExchangeError: If there's an error with the exchange
        """
        try:
            return self._symbol_service.get_klines(symbol_name, interval, limit)
        except ExchangeError as e:
            logger.error(f"Error getting klines for {symbol_name}: {e}")
            raise
    
    # Strategy operations
    
    def create_strategy(self, name: str, symbol_id: str, type: str, 
                       parameters: Dict, description: Optional[str] = None) -> Dict:
        """
        Create a new strategy.
        
        Args:
            name: Strategy name
            symbol_id: ID of the symbol to trade
            type: Strategy type (e.g., "MACD", "RSI", "GRID")
            parameters: Strategy parameters
            description: Optional description
            
        Returns:
            Created strategy as a dictionary
            
        Raises:
            SymbolNotFoundError: If the symbol is not found
            StrategyValidationError: If the strategy parameters are invalid
        """
        try:
            strategy = self._strategy_service.create_strategy(
                name=name,
                symbol_id=symbol_id,
                type=type,
                parameters=parameters,
                description=description
            )
            return strategy.to_dict()
        except (SymbolNotFoundError, StrategyValidationError) as e:
            logger.error(f"Error creating strategy: {e}")
            raise
    
    def update_strategy(self, strategy_id: str, name: Optional[str] = None,
                       type: Optional[str] = None, parameters: Optional[Dict] = None,
                       description: Optional[str] = None) -> Dict:
        """
        Update an existing strategy.
        
        Args:
            strategy_id: ID of the strategy to update
            name: New name
            type: New type
            parameters: New parameters
            description: New description
            
        Returns:
            Updated strategy as a dictionary
            
        Raises:
            StrategyNotFoundError: If the strategy is not found
            StrategyValidationError: If the strategy parameters are invalid
        """
        try:
            strategy = self._strategy_service.update_strategy(
                strategy_id=strategy_id,
                name=name,
                type=type,
                parameters=parameters,
                description=description
            )
            return strategy.to_dict()
        except (StrategyNotFoundError, StrategyValidationError) as e:
            logger.error(f"Error updating strategy: {e}")
            raise
    
    def activate_strategy(self, strategy_id: str) -> Dict:
        """
        Activate a strategy.
        
        Args:
            strategy_id: ID of the strategy to activate
            
        Returns:
            Activated strategy as a dictionary
            
        Raises:
            StrategyNotFoundError: If the strategy is not found
        """
        try:
            strategy = self._strategy_service.activate_strategy(strategy_id)
            return strategy.to_dict()
        except StrategyNotFoundError as e:
            logger.error(f"Error activating strategy: {e}")
            raise
    
    def deactivate_strategy(self, strategy_id: str) -> Dict:
        """
        Deactivate a strategy.
        
        Args:
            strategy_id: ID of the strategy to deactivate
            
        Returns:
            Deactivated strategy as a dictionary
            
        Raises:
            StrategyNotFoundError: If the strategy is not found
        """
        try:
            strategy = self._strategy_service.deactivate_strategy(strategy_id)
            return strategy.to_dict()
        except StrategyNotFoundError as e:
            logger.error(f"Error deactivating strategy: {e}")
            raise
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: ID of the strategy to delete
            
        Returns:
            True if deleted, False if not found
        """
        return self._strategy_service.delete_strategy(strategy_id)
    
    def get_strategy(self, strategy_id: str) -> Dict:
        """
        Get a strategy by its ID.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy as a dictionary
            
        Raises:
            StrategyNotFoundError: If the strategy is not found
        """
        try:
            strategy = self._strategy_service.get_strategy(strategy_id)
            return strategy.to_dict()
        except StrategyNotFoundError as e:
            logger.error(f"Strategy not found: {e}")
            raise
    
    def get_all_strategies(self) -> List[Dict]:
        """
        Get all strategies.
        
        Returns:
            List of strategies as dictionaries
        """
        strategies = self._strategy_service.get_all_strategies()
        return [strategy.to_dict() for strategy in strategies]
    
    def get_strategies_by_symbol(self, symbol_id: str) -> List[Dict]:
        """
        Get all strategies for a specific symbol.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            List of strategies as dictionaries
        """
        strategies = self._strategy_service.get_strategies_by_symbol(symbol_id)
        return [strategy.to_dict() for strategy in strategies]
    
    def get_active_strategies(self) -> List[Dict]:
        """
        Get all active strategies.
        
        Returns:
            List of active strategies as dictionaries
        """
        strategies = self._strategy_service.get_active_strategies()
        return [strategy.to_dict() for strategy in strategies]
    
    # Order operations
    
    def create_order(self, strategy_id: str, symbol: str, order_type: str,
                    side: str, quantity: float, price: Optional[float] = None) -> Dict:
        """
        Create a new order.
        
        Args:
            strategy_id: ID of the strategy
            symbol: Symbol name (e.g., "BTCUSDT")
            order_type: Order type (e.g., "LIMIT", "MARKET")
            side: Order side (e.g., "BUY", "SELL")
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            
        Returns:
            Created order as a dictionary
            
        Raises:
            StrategyNotFoundError: If the strategy is not found
            ExchangeError: If there's an error with the exchange
            InvalidOrderError: If the order parameters are invalid
            InsufficientBalanceError: If there's insufficient balance
        """
        try:
            order, trade = self._order_service.create_order(
                strategy_id=strategy_id,
                symbol=symbol,
                order_type=order_type,
                side=side,
                quantity=quantity,
                price=price
            )
            
            result = order.to_dict()
            if trade:
                result['trade'] = trade.to_dict()
                
            return result
        except (StrategyNotFoundError, ExchangeError, InvalidOrderError, InsufficientBalanceError) as e:
            logger.error(f"Error creating order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Dict:
        """
        Cancel an order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            Canceled order as a dictionary
            
        Raises:
            OrderNotFoundError: If the order is not found
            ExchangeError: If there's an error with the exchange
        """
        try:
            order = self._order_service.cancel_order(order_id)
            return order.to_dict()
        except (OrderNotFoundError, ExchangeError) as e:
            logger.error(f"Error canceling order: {e}")
            raise
    
    def get_order(self, order_id: str) -> Dict:
        """
        Get an order by its ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order as a dictionary
            
        Raises:
            OrderNotFoundError: If the order is not found
        """
        try:
            order = self._order_service.get_order(order_id)
            return order.to_dict()
        except OrderNotFoundError as e:
            logger.error(f"Order not found: {e}")
            raise
    
    def get_order_with_trades(self, order_id: str) -> Dict:
        """
        Get an order with its trades.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order with trades as a dictionary
            
        Raises:
            OrderNotFoundError: If the order is not found
        """
        try:
            order, trades = self._order_service.get_order_with_trades(order_id)
            result = order.to_dict()
            result['trades'] = [trade.to_dict() for trade in trades]
            return result
        except OrderNotFoundError as e:
            logger.error(f"Order not found: {e}")
            raise
    
    def update_order_status(self, order_id: str) -> Dict:
        """
        Update an order's status from the exchange.
        
        Args:
            order_id: Order ID
            
        Returns:
            Updated order with new trades as a dictionary
            
        Raises:
            OrderNotFoundError: If the order is not found
            ExchangeError: If there's an error with the exchange
        """
        try:
            order, trades = self._order_service.update_order_status(order_id)
            result = order.to_dict()
            result['new_trades'] = [trade.to_dict() for trade in trades]
            return result
        except (OrderNotFoundError, ExchangeError) as e:
            logger.error(f"Error updating order status: {e}")
            raise
    
    def get_orders_by_strategy(self, strategy_id: str) -> List[Dict]:
        """
        Get all orders for a specific strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            List of orders as dictionaries
        """
        orders = self._order_service.get_orders_by_strategy(strategy_id)
        return [order.to_dict() for order in orders]
    
    def get_active_orders(self, strategy_id: Optional[str] = None) -> List[Dict]:
        """
        Get all active orders.
        
        Args:
            strategy_id: Optional strategy ID to filter by
            
        Returns:
            List of active orders as dictionaries
        """
        orders = self._order_service.get_active_orders(strategy_id)
        return [order.to_dict() for order in orders]
    
    def get_all_orders(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all orders with pagination.
        
        Args:
            limit: Maximum number of orders to return
            offset: Offset for pagination
            
        Returns:
            List of orders as dictionaries
        """
        orders = self._order_service.get_all_orders(limit, offset)
        return [order.to_dict() for order in orders] 