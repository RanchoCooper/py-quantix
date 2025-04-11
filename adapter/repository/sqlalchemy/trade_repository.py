"""
SQLAlchemy Trade repository implementation.

This module provides the SQLAlchemy-based implementation of the Trade repository.
"""
import logging
from typing import List, Optional

from domain.model.trade import Trade
from domain.repository.trade_repository import TradeRepository
from adapter.repository.sqlalchemy.base_repository import BaseSQLAlchemyRepository
from adapter.repository.sqlalchemy.models import TradeModel

logger = logging.getLogger(__name__)


class SQLAlchemyTradeRepository(BaseSQLAlchemyRepository, TradeRepository):
    """
    SQLAlchemy implementation of the Trade repository.
    
    This class provides a SQLAlchemy-based implementation of the Trade repository
    interface defined in the domain layer.
    """
    
    def __init__(self, db_name: str = None):
        """
        Initialize the Trade repository.
        
        Args:
            db_name: Optional name of the database to use
        """
        super().__init__(db_name)
    
    def save(self, trade: Trade) -> Trade:
        """
        Save a Trade entity.
        
        This method creates a new Trade if it doesn't exist.
        
        Args:
            trade: The Trade entity to save
            
        Returns:
            The saved Trade entity
        """
        session = self._session
        
        try:
            # Check if the Trade already exists
            existing_model = session.query(TradeModel).filter_by(id=trade.id).first()
            
            if existing_model:
                # Trade entities are immutable, so we should not update existing ones
                # Just return the existing trade
                return trade
            else:
                # Create new model
                model = TradeModel(
                    id=trade.id,
                    order_id=trade.order_id,
                    exchange_trade_id=trade.exchange_trade_id,
                    price=trade.price,
                    quantity=trade.quantity,
                    commission=trade.commission,
                    commission_asset=trade.commission_asset,
                    created_at=trade.created_at
                )
                session.add(model)
                
            session.commit()
            
            # Return the created Trade
            return trade
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving Trade {trade.id}: {e}")
            raise
    
    def get_by_id(self, trade_id: str) -> Optional[Trade]:
        """
        Get a Trade by its ID.
        
        Args:
            trade_id: The ID of the Trade to retrieve
            
        Returns:
            The Trade if found, None otherwise
        """
        session = self._session
        
        try:
            model = session.query(TradeModel).filter_by(id=trade_id).first()
            
            if not model:
                return None
                
            return Trade(
                id=model.id,
                order_id=model.order_id,
                exchange_trade_id=model.exchange_trade_id,
                price=model.price,
                quantity=model.quantity,
                commission=model.commission,
                commission_asset=model.commission_asset,
                created_at=model.created_at
            )
        except Exception as e:
            logger.error(f"Error getting Trade with ID {trade_id}: {e}")
            raise
    
    def get_by_exchange_trade_id(self, exchange_trade_id: str) -> Optional[Trade]:
        """
        Get a Trade by its exchange trade ID.
        
        Args:
            exchange_trade_id: The exchange trade ID
            
        Returns:
            The Trade if found, None otherwise
        """
        session = self._session
        
        try:
            model = session.query(TradeModel).filter_by(exchange_trade_id=exchange_trade_id).first()
            
            if not model:
                return None
                
            return Trade(
                id=model.id,
                order_id=model.order_id,
                exchange_trade_id=model.exchange_trade_id,
                price=model.price,
                quantity=model.quantity,
                commission=model.commission,
                commission_asset=model.commission_asset,
                created_at=model.created_at
            )
        except Exception as e:
            logger.error(f"Error getting Trade with exchange trade ID {exchange_trade_id}: {e}")
            raise
    
    def get_by_order_id(self, order_id: str) -> List[Trade]:
        """
        Get all Trades for a specific Order.
        
        Args:
            order_id: The ID of the Order to get Trades for
            
        Returns:
            A list of Trade entities for the specified Order
        """
        session = self._session
        
        try:
            models = session.query(TradeModel).filter_by(order_id=order_id).all()
            
            return [
                Trade(
                    id=model.id,
                    order_id=model.order_id,
                    exchange_trade_id=model.exchange_trade_id,
                    price=model.price,
                    quantity=model.quantity,
                    commission=model.commission,
                    commission_asset=model.commission_asset,
                    created_at=model.created_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting Trades for Order ID {order_id}: {e}")
            raise
    
    def get_all(self) -> List[Trade]:
        """
        Get all Trades.
        
        Returns:
            A list of all Trade entities
        """
        session = self._session
        
        try:
            models = session.query(TradeModel).all()
            
            return [
                Trade(
                    id=model.id,
                    order_id=model.order_id,
                    exchange_trade_id=model.exchange_trade_id,
                    price=model.price,
                    quantity=model.quantity,
                    commission=model.commission,
                    commission_asset=model.commission_asset,
                    created_at=model.created_at
                )
                for model in models
            ]
        except Exception as e:
            logger.error(f"Error getting all Trades: {e}")
            raise 