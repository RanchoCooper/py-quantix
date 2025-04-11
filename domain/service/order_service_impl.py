"""
Order service implementation.

This module provides the implementation of the Order domain service.
"""
import logging
from typing import List, Optional, Tuple

from domain.event.base_event import EventBus
from domain.event.order_events import (
    OrderCanceledEvent, OrderCreatedEvent, OrderFilledEvent,
    OrderStatusUpdatedEvent, TradeCreatedEvent
)
from domain.model.errors import (
    ExchangeError, OrderNotFoundError, StrategyNotFoundError
)
from domain.model.order import Order
from domain.model.trade import Trade
from domain.repository.order_repository import OrderRepository
from domain.repository.trade_repository import TradeRepository
from domain.service.exchange_service import ExchangeService
from domain.service.order_service import OrderService
from domain.service.strategy_service import StrategyService

logger = logging.getLogger(__name__)


class OrderServiceImpl(OrderService):
    """
    Implementation of the Order domain service.
    
    This service contains domain logic for managing trading orders.
    """
    
    def __init__(self, order_repository: OrderRepository, trade_repository: TradeRepository,
                strategy_service: StrategyService, exchange_service: ExchangeService,
                event_bus: EventBus):
        """
        Initialize the Order service.
        
        Args:
            order_repository: Repository for Order entities
            trade_repository: Repository for Trade entities
            strategy_service: Strategy service for checking strategy existence
            exchange_service: Exchange service for interacting with the exchange
            event_bus: Event bus for publishing domain events
        """
        self._order_repository = order_repository
        self._trade_repository = trade_repository
        self._strategy_service = strategy_service
        self._exchange_service = exchange_service
        self._event_bus = event_bus
        logger.info("Initialized Order service")
    
    def create_order(self, strategy_id: str, symbol: str, order_type: str, 
                    side: str, quantity: float, price: Optional[float] = None) -> Tuple[Order, Optional[Trade]]:
        """
        Create and place a new order.
        
        Args:
            strategy_id: ID of the strategy creating the order
            symbol: Trading symbol (e.g., "BTCUSDT")
            order_type: Order type (e.g., "LIMIT", "MARKET")
            side: Order side (e.g., "BUY", "SELL")
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            
        Returns:
            Tuple of created Order and Trade if filled immediately (Market orders)
            
        Raises:
            StrategyNotFoundError: If the strategy with the given ID doesn't exist
            ExchangeError: If there's an error with the exchange
            InvalidOrderError: If the order parameters are invalid
            InsufficientBalanceError: If there's insufficient balance to place the order
        """
        # Check if the strategy exists
        try:
            self._strategy_service.get_strategy(strategy_id)
        except StrategyNotFoundError as e:
            logger.error(f"Strategy not found when creating order: {e}")
            raise
        
        # Create the order
        order = Order.create(
            strategy_id=strategy_id,
            symbol=symbol,
            order_type=order_type,
            side=side,
            quantity=quantity,
            price=price
        )
        
        # Save the order
        saved_order = self._order_repository.save(order)
        
        # Place the order on the exchange
        try:
            updated_order, trade = self._exchange_service.place_order(saved_order)
            
            # Save the updated order
            saved_order = self._order_repository.save(updated_order)
            
            # Publish order created event
            self._event_bus.publish(
                OrderCreatedEvent(
                    order_id=saved_order.id,
                    strategy_id=saved_order.strategy_id,
                    symbol=saved_order.symbol,
                    order_type=saved_order.order_type,
                    side=saved_order.side,
                    quantity=saved_order.quantity,
                    price=saved_order.price
                )
            )
            
            # If the order was filled immediately, save the trade and publish event
            if trade:
                saved_trade = self._trade_repository.save(trade)
                
                # Publish order filled event
                self._event_bus.publish(
                    OrderFilledEvent(
                        order_id=saved_order.id,
                        strategy_id=saved_order.strategy_id,
                        symbol=saved_order.symbol,
                        side=saved_order.side
                    )
                )
                
                # Publish trade created event
                self._event_bus.publish(
                    TradeCreatedEvent(
                        trade_id=saved_trade.id,
                        order_id=saved_trade.order_id,
                        price=saved_trade.price,
                        quantity=saved_trade.quantity
                    )
                )
                
                logger.info(f"Created order and trade: {saved_order.id}, {saved_trade.id}")
                return saved_order, saved_trade
            
            logger.info(f"Created order: {saved_order.id}")
            return saved_order, None
            
        except ExchangeError as e:
            # If there was an error placing the order, update the status and re-save
            failed_order = order.update_status("FAILED")
            self._order_repository.save(failed_order)
            logger.error(f"Error placing order: {e}")
            raise
    
    def cancel_order(self, order_id: str) -> Order:
        """
        Cancel an existing order.
        
        Args:
            order_id: The ID of the order to cancel
            
        Returns:
            The updated Order with canceled status
            
        Raises:
            OrderNotFoundError: If the order with the given ID doesn't exist
            ExchangeError: If there's an error with the exchange
        """
        # Get the order
        order = self.get_order(order_id)
        
        # Check if the order can be canceled
        if not order.is_active():
            logger.info(f"Order {order_id} is not active, cannot cancel")
            return order
        
        # Cancel the order on the exchange
        try:
            updated_order = self._exchange_service.cancel_order(order)
            
            # Save the updated order
            saved_order = self._order_repository.save(updated_order)
            
            # Publish order canceled event
            self._event_bus.publish(
                OrderCanceledEvent(
                    order_id=saved_order.id,
                    strategy_id=saved_order.strategy_id
                )
            )
            
            logger.info(f"Canceled order: {saved_order.id}")
            return saved_order
            
        except ExchangeError as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            raise
    
    def get_order(self, order_id: str) -> Order:
        """
        Get an order by its ID.
        
        Args:
            order_id: The ID of the order to get
            
        Returns:
            The found Order
            
        Raises:
            OrderNotFoundError: If the order with the given ID doesn't exist
        """
        order = self._order_repository.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order
    
    def get_order_with_trades(self, order_id: str) -> Tuple[Order, List[Trade]]:
        """
        Get an order with its trades by ID.
        
        Args:
            order_id: The ID of the order to get
            
        Returns:
            Tuple of Order and its Trades
            
        Raises:
            OrderNotFoundError: If the order with the given ID doesn't exist
        """
        # Get the order
        order = self.get_order(order_id)
        
        # Get the trades
        trades = self._trade_repository.get_by_order_id(order_id)
        
        return order, trades
    
    def update_order_status(self, order_id: str) -> Tuple[Order, List[Trade]]:
        """
        Update an order's status from the exchange.
        
        Args:
            order_id: The ID of the order to update
            
        Returns:
            Tuple of updated Order and new Trades if any
            
        Raises:
            OrderNotFoundError: If the order with the given ID doesn't exist
            ExchangeError: If there's an error with the exchange
        """
        # Get the order
        order = self.get_order(order_id)
        
        # If the order doesn't have an exchange ID, it can't be updated
        if not order.exchange_order_id:
            logger.warning(f"Order {order_id} has no exchange ID, cannot update status")
            return order, []
        
        # If the order is already in a final state, no need to update
        if not order.is_active():
            return order, []
        
        try:
            # Get the latest status from the exchange
            updated_order, new_trades = self._exchange_service.get_order_status(order)
            
            # Save the updated order
            old_status = order.status
            saved_order = self._order_repository.save(updated_order)
            
            # If the status changed, publish an event
            if saved_order.status != old_status:
                self._event_bus.publish(
                    OrderStatusUpdatedEvent(
                        order_id=saved_order.id,
                        strategy_id=saved_order.strategy_id,
                        old_status=old_status,
                        new_status=saved_order.status
                    )
                )
                
                # If the order was filled, publish an order filled event
                if saved_order.is_filled():
                    self._event_bus.publish(
                        OrderFilledEvent(
                            order_id=saved_order.id,
                            strategy_id=saved_order.strategy_id,
                            symbol=saved_order.symbol,
                            side=saved_order.side
                        )
                    )
            
            # Save any new trades
            saved_trades = []
            for trade in new_trades:
                # Check if we already have this trade
                existing_trade = self._trade_repository.get_by_exchange_trade_id(trade.exchange_trade_id) if trade.exchange_trade_id else None
                
                if not existing_trade:
                    saved_trade = self._trade_repository.save(trade)
                    saved_trades.append(saved_trade)
                    
                    # Publish trade created event
                    self._event_bus.publish(
                        TradeCreatedEvent(
                            trade_id=saved_trade.id,
                            order_id=saved_trade.order_id,
                            price=saved_trade.price,
                            quantity=saved_trade.quantity
                        )
                    )
            
            if saved_trades:
                logger.info(f"Updated order {saved_order.id} status and saved {len(saved_trades)} new trades")
            
            return saved_order, saved_trades
            
        except ExchangeError as e:
            logger.error(f"Error updating order {order_id} status: {e}")
            raise
    
    def get_orders_by_strategy(self, strategy_id: str) -> List[Order]:
        """
        Get all orders for a specific strategy.
        
        Args:
            strategy_id: The ID of the strategy to get orders for
            
        Returns:
            A list of orders for the specified strategy
        """
        return self._order_repository.get_by_strategy_id(strategy_id)
    
    def get_active_orders(self, strategy_id: Optional[str] = None) -> List[Order]:
        """
        Get all active orders.
        
        Args:
            strategy_id: Optional ID of a strategy to filter by
            
        Returns:
            A list of active orders
        """
        return self._order_repository.get_active_orders(strategy_id)
    
    def get_all_orders(self, limit: int = 100, offset: int = 0) -> List[Order]:
        """
        Get all orders with pagination.
        
        Args:
            limit: Maximum number of orders to return
            offset: Offset for pagination
            
        Returns:
            A list of orders
        """
        # Simple implementation without real pagination
        # In a real-world scenario, this would be implemented in the repository
        all_orders = self._order_repository.get_all()
        return all_orders[offset:offset+limit] 