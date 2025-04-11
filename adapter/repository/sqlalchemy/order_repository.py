"""
SQLAlchemy Order repository implementation.

This module provides the SQLAlchemy-based implementation of the Order repository.
"""
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_

from domain.model.order import Order
from domain.repository.order_repository import OrderRepository
from adapter.repository.sqlalchemy.base_repository import SQLAlchemyBaseRepository
from adapter.repository.sqlalchemy.models import OrderModel

logger = logging.getLogger(__name__)


class SQLAlchemyOrderRepository(SQLAlchemyBaseRepository, OrderRepository):
    """
    SQLAlchemy implementation of the Order repository.
    
    This class provides a SQLAlchemy-based implementation of the Order repository
    interface defined in the domain layer.
    """
    
    def __init__(self, db_name: str = None):
        """
        Initialize the Order repository.
        
        Args:
            db_name: Optional name of the database to use
        """
        super().__init__(db_name)
    
    def save(self, order: Order) -> Order:
        """
        Save an Order entity.
        
        This method creates a new Order if it doesn't exist, or updates an existing one.
        
        Args:
            order: The Order entity to save
            
        Returns:
            The saved Order entity
        """
        session = self._get_session()
        
        try:
            # Check if the Order already exists
            existing_model = session.query(OrderModel).filter_by(id=order.id).first()
            
            if existing_model:
                # Update existing model
                existing_model.exchange_order_id = order.exchange_order_id
                existing_model.strategy_id = order.strategy_id
                existing_model.symbol = order.symbol
                existing_model.order_type = order.order_type
                existing_model.side = order.side
                existing_model.status = order.status
                existing_model.price = order.price
                existing_model.quantity = order.quantity
                existing_model.executed_quantity = order.executed_quantity
                existing_model.updated_at = datetime.now()
            else:
                # Create new model
                model = OrderModel(
                    id=order.id,
                    exchange_order_id=order.exchange_order_id,
                    strategy_id=order.strategy_id,
                    symbol=order.symbol,
                    order_type=order.order_type,
                    side=order.side,
                    status=order.status,
                    price=order.price,
                    quantity=order.quantity,
                    executed_quantity=order.executed_quantity,
                    created_at=order.created_at,
                    updated_at=order.updated_at
                )
                session.add(model)
                
            session.commit()
            
            # Return the updated or created Order
            return order
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving Order {order.id}: {e}")
            raise
    
    def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Get an Order by its ID.
        
        Args:
            order_id: The ID of the Order to retrieve
            
        Returns:
            The Order if found, None otherwise
        """
        session = self._get_session()
        
        try:
            model = session.query(OrderModel).filter_by(id=order_id).first()
            
            if not model:
                return None
                
            return Order(
                id=model.id,
                exchange_order_id=model.exchange_order_id,
                strategy_id=model.strategy_id,
                symbol=model.symbol,
                order_type=model.order_type,
                side=model.side,
                status=model.status,
                price=model.price,
                quantity=model.quantity,
                executed_quantity=model.executed_quantity,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
        except Exception as e:
            logger.error(f"Error getting Order with ID {order_id}: {e}")
            raise
    
    def get_by_exchange_order_id(self, exchange_order_id: str) -> Optional[Order]:
        """
        Get an Order by its exchange order ID.
        
        Args:
            exchange_order_id: The exchange order ID
            
        Returns:
            The Order if found, None otherwise
        """
        session = self._get_session()
        
        try:
            model = session.query(OrderModel).filter_by(exchange_order_id=exchange_order_id).first()
            
            if not model:
                return None
                
            return Order(
                id=model.id,
                exchange_order_id=model.exchange_order_id,
                strategy_id=model.strategy_id,
                symbol=model.symbol,
                order_type=model.order_type,
                side=model.side,
                status=model.status,
                price=model.price,
                quantity=model.quantity,
                executed_quantity=model.executed_quantity,
                created_at=model.created_at,
                updated_at=model.updated_at
            )
        except Exception as e:
            logger.error(f"Error getting Order with exchange order ID {exchange_order_id}: {e}")
            raise
    
    def get_all(self) -> List[Order]:
        """
        Get all Orders.
        
        Returns:
            A list of all Order entities
        """
        session = self._get_session()
        
        try:
            models = session.query(OrderModel).all()
            
            return [
                Order(
                    id=model.id,
                    exchange_order_id=model.exchange_order_id,
                    strategy_id=model.strategy_id,
                    symbol=model.symbol,
                    order_type=model.order_type,
                    side=model.side,
                    status=model.status,
                    price=model.price,
                    quantity=model.quantity,
                    executed_quantity=model.executed_quantity,
                    created_at=model.created_at,
                    updated_at=model.updated_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting all Orders: {e}")
            raise
    
    def get_by_strategy_id(self, strategy_id: str) -> List[Order]:
        """
        Get all Orders for a specific Strategy.
        
        Args:
            strategy_id: The ID of the Strategy to get Orders for
            
        Returns:
            A list of Order entities for the specified Strategy
        """
        session = self._get_session()
        
        try:
            models = session.query(OrderModel).filter_by(strategy_id=strategy_id).all()
            
            return [
                Order(
                    id=model.id,
                    exchange_order_id=model.exchange_order_id,
                    strategy_id=model.strategy_id,
                    symbol=model.symbol,
                    order_type=model.order_type,
                    side=model.side,
                    status=model.status,
                    price=model.price,
                    quantity=model.quantity,
                    executed_quantity=model.executed_quantity,
                    created_at=model.created_at,
                    updated_at=model.updated_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting Orders for Strategy ID {strategy_id}: {e}")
            raise
    
    def get_by_symbol(self, symbol: str) -> List[Order]:
        """
        Get all Orders for a specific Symbol.
        
        Args:
            symbol: The Symbol name to get Orders for (e.g., "BTCUSDT")
            
        Returns:
            A list of Order entities for the specified Symbol
        """
        session = self._get_session()
        
        try:
            models = session.query(OrderModel).filter_by(symbol=symbol).all()
            
            return [
                Order(
                    id=model.id,
                    exchange_order_id=model.exchange_order_id,
                    strategy_id=model.strategy_id,
                    symbol=model.symbol,
                    order_type=model.order_type,
                    side=model.side,
                    status=model.status,
                    price=model.price,
                    quantity=model.quantity,
                    executed_quantity=model.executed_quantity,
                    created_at=model.created_at,
                    updated_at=model.updated_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting Orders for Symbol {symbol}: {e}")
            raise
    
    def get_active_orders(self, strategy_id: Optional[str] = None) -> List[Order]:
        """
        Get all active Orders.
        
        Args:
            strategy_id: Optional ID of a Strategy to filter by
            
        Returns:
            A list of active Order entities
        """
        session = self._get_session()
        
        try:
            query = session.query(OrderModel).filter(
                or_(
                    OrderModel.status == 'NEW',
                    OrderModel.status == 'PARTIALLY_FILLED'
                )
            )
            
            if strategy_id:
                query = query.filter_by(strategy_id=strategy_id)
                
            models = query.all()
            
            return [
                Order(
                    id=model.id,
                    exchange_order_id=model.exchange_order_id,
                    strategy_id=model.strategy_id,
                    symbol=model.symbol,
                    order_type=model.order_type,
                    side=model.side,
                    status=model.status,
                    price=model.price,
                    quantity=model.quantity,
                    executed_quantity=model.executed_quantity,
                    created_at=model.created_at,
                    updated_at=model.updated_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting active Orders: {e}")
            raise
    
    def delete(self, order_id: str) -> bool:
        """
        Delete an Order by its ID.
        
        Args:
            order_id: The ID of the Order to delete
            
        Returns:
            True if the Order was deleted, False if it didn't exist
        """
        session = self._get_session()
        
        try:
            model = session.query(OrderModel).filter_by(id=order_id).first()
            
            if not model:
                return False
                
            session.delete(model)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting Order with ID {order_id}: {e}")
            raise 