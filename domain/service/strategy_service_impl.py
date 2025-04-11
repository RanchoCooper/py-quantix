"""
Strategy service implementation.

This module provides the implementation of the Strategy domain service.
"""
import logging
from typing import Dict, List, Optional

from domain.event.base_event import EventBus
from domain.event.strategy_events import (
    StrategyActivatedEvent, StrategyCreatedEvent, StrategyDeactivatedEvent,
    StrategyDeletedEvent, StrategyUpdatedEvent
)
from domain.model.errors import (
    StrategyNotFoundError, StrategyValidationError, SymbolNotFoundError
)
from domain.model.strategy import Strategy
from domain.repository.strategy_repository import StrategyRepository
from domain.service.strategy_service import StrategyService
from domain.service.symbol_service import SymbolService

logger = logging.getLogger(__name__)


class StrategyServiceImpl(StrategyService):
    """
    Implementation of the Strategy domain service.
    
    This service contains domain logic for managing trading strategies.
    """
    
    def __init__(self, repository: StrategyRepository, symbol_service: SymbolService, 
                event_bus: EventBus):
        """
        Initialize the Strategy service.
        
        Args:
            repository: Repository for Strategy entities
            symbol_service: Symbol service for checking symbol existence
            event_bus: Event bus for publishing domain events
        """
        self._repository = repository
        self._symbol_service = symbol_service
        self._event_bus = event_bus
        logger.info("Initialized Strategy service")
    
    def create_strategy(self, name: str, symbol_id: str, type: str, 
                       parameters: Dict, description: Optional[str] = None) -> Strategy:
        """
        Create a new trading strategy.
        
        Args:
            name: Strategy name
            symbol_id: ID of the symbol this strategy trades on
            type: Strategy type (e.g., "MACD", "RSI", "GRID")
            parameters: Dictionary of strategy parameters
            description: Optional description
            
        Returns:
            The created Strategy
            
        Raises:
            SymbolNotFoundError: If the symbol with the given ID doesn't exist
            StrategyValidationError: If the strategy parameters are invalid
        """
        # Check if the symbol exists
        try:
            self._symbol_service.get_symbol(symbol_id)
        except SymbolNotFoundError as e:
            logger.error(f"Symbol not found when creating strategy: {e}")
            raise
        
        # Validate strategy parameters
        if not self.validate_strategy_parameters(type, parameters):
            raise StrategyValidationError(f"Invalid parameters for strategy type {type}")
        
        # Create the strategy
        strategy = Strategy.create(
            name=name,
            symbol_id=symbol_id,
            type=type,
            parameters=parameters,
            description=description,
            is_active=False  # Strategies are created inactive by default
        )
        
        # Save the strategy
        saved_strategy = self._repository.save(strategy)
        
        # Publish strategy created event
        self._event_bus.publish(
            StrategyCreatedEvent(
                strategy_id=saved_strategy.id,
                name=saved_strategy.name,
                symbol_id=saved_strategy.symbol_id,
                type=saved_strategy.type
            )
        )
        
        logger.info(f"Created strategy: {saved_strategy.id} - {saved_strategy.name}")
        return saved_strategy
    
    def update_strategy(self, strategy_id: str, name: Optional[str] = None,
                       type: Optional[str] = None, parameters: Optional[Dict] = None,
                       description: Optional[str] = None) -> Strategy:
        """
        Update an existing strategy.
        
        Args:
            strategy_id: The ID of the strategy to update
            name: The new name of the strategy (if provided)
            type: The new type of the strategy (if provided)
            parameters: The new parameters of the strategy (if provided)
            description: The new description of the strategy (if provided)
            
        Returns:
            The updated Strategy
            
        Raises:
            StrategyNotFoundError: If the strategy with the given ID doesn't exist
            StrategyValidationError: If the updated strategy parameters are invalid
        """
        # Get the strategy
        strategy = self.get_strategy(strategy_id)
        
        # If type is changing, verify new parameters
        if type is not None and type != strategy.type and parameters is None:
            raise StrategyValidationError(f"Parameters must be provided when changing strategy type to {type}")
        
        # If parameters are changing, validate them
        if parameters is not None:
            validate_type = type if type is not None else strategy.type
            if not self.validate_strategy_parameters(validate_type, parameters):
                raise StrategyValidationError(f"Invalid parameters for strategy type {validate_type}")
        
        # Update the strategy
        updated_strategy = strategy.update(
            name=name,
            type=type,
            parameters=parameters,
            description=description
        )
        
        # Save the updated strategy
        saved_strategy = self._repository.save(updated_strategy)
        
        # Publish strategy updated event
        self._event_bus.publish(
            StrategyUpdatedEvent(
                strategy_id=saved_strategy.id,
                name=name,
                type=type,
                parameters_updated=(parameters is not None)
            )
        )
        
        logger.info(f"Updated strategy: {saved_strategy.id}")
        return saved_strategy
    
    def activate_strategy(self, strategy_id: str) -> Strategy:
        """
        Activate a strategy.
        
        Args:
            strategy_id: The ID of the strategy to activate
            
        Returns:
            The activated Strategy
            
        Raises:
            StrategyNotFoundError: If the strategy with the given ID doesn't exist
        """
        # Get the strategy
        strategy = self.get_strategy(strategy_id)
        
        # If already active, return as is
        if strategy.is_active:
            return strategy
        
        # Activate the strategy
        activated_strategy = strategy.activate()
        
        # Save the activated strategy
        saved_strategy = self._repository.save(activated_strategy)
        
        # Publish strategy activated event
        self._event_bus.publish(
            StrategyActivatedEvent(
                strategy_id=saved_strategy.id
            )
        )
        
        logger.info(f"Activated strategy: {saved_strategy.id}")
        return saved_strategy
    
    def deactivate_strategy(self, strategy_id: str) -> Strategy:
        """
        Deactivate a strategy.
        
        Args:
            strategy_id: The ID of the strategy to deactivate
            
        Returns:
            The deactivated Strategy
            
        Raises:
            StrategyNotFoundError: If the strategy with the given ID doesn't exist
        """
        # Get the strategy
        strategy = self.get_strategy(strategy_id)
        
        # If already inactive, return as is
        if not strategy.is_active:
            return strategy
        
        # Deactivate the strategy
        deactivated_strategy = strategy.deactivate()
        
        # Save the deactivated strategy
        saved_strategy = self._repository.save(deactivated_strategy)
        
        # Publish strategy deactivated event
        self._event_bus.publish(
            StrategyDeactivatedEvent(
                strategy_id=saved_strategy.id
            )
        )
        
        logger.info(f"Deactivated strategy: {saved_strategy.id}")
        return saved_strategy
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: The ID of the strategy to delete
            
        Returns:
            True if the strategy was deleted, False if it didn't exist
        """
        # Check if the strategy exists
        try:
            self.get_strategy(strategy_id)
        except StrategyNotFoundError:
            return False
        
        # Delete the strategy
        result = self._repository.delete(strategy_id)
        
        if result:
            # Publish strategy deleted event
            self._event_bus.publish(
                StrategyDeletedEvent(
                    strategy_id=strategy_id
                )
            )
            
            logger.info(f"Deleted strategy: {strategy_id}")
        
        return result
    
    def get_strategy(self, strategy_id: str) -> Strategy:
        """
        Get a strategy by its ID.
        
        Args:
            strategy_id: The ID of the strategy to get
            
        Returns:
            The found Strategy
            
        Raises:
            StrategyNotFoundError: If the strategy with the given ID doesn't exist
        """
        strategy = self._repository.get_by_id(strategy_id)
        if not strategy:
            raise StrategyNotFoundError(strategy_id)
        return strategy
    
    def get_all_strategies(self) -> List[Strategy]:
        """
        Get all strategies.
        
        Returns:
            A list of all strategies
        """
        return self._repository.get_all()
    
    def get_strategies_by_symbol(self, symbol_id: str) -> List[Strategy]:
        """
        Get all strategies for a specific symbol.
        
        Args:
            symbol_id: The ID of the symbol to get strategies for
            
        Returns:
            A list of strategies for the specified symbol
        """
        return self._repository.get_by_symbol_id(symbol_id)
    
    def get_active_strategies(self) -> List[Strategy]:
        """
        Get all active strategies.
        
        Returns:
            A list of all active strategies
        """
        return self._repository.get_active_strategies()
    
    def validate_strategy_parameters(self, type: str, parameters: Dict) -> bool:
        """
        Validate strategy parameters for a given strategy type.
        
        Args:
            type: Strategy type (e.g., "MACD", "RSI", "GRID")
            parameters: Dictionary of strategy parameters
            
        Returns:
            True if the parameters are valid, False otherwise
            
        Raises:
            StrategyValidationError: If the parameters are invalid
        """
        # Different validation logic for each strategy type
        if type == "MACD":
            return self._validate_macd_parameters(parameters)
        elif type == "RSI":
            return self._validate_rsi_parameters(parameters)
        elif type == "GRID":
            return self._validate_grid_parameters(parameters)
        else:
            raise StrategyValidationError(f"Unsupported strategy type: {type}")
    
    def _validate_macd_parameters(self, parameters: Dict) -> bool:
        """
        Validate MACD strategy parameters.
        
        Args:
            parameters: Dictionary of MACD parameters
            
        Returns:
            True if the parameters are valid, False otherwise
            
        Raises:
            StrategyValidationError: If the parameters are invalid
        """
        required_params = ['fast_period', 'slow_period', 'signal_period', 'timeframe']
        
        # Check if all required parameters are present
        for param in required_params:
            if param not in parameters:
                raise StrategyValidationError(f"Missing required parameter: {param}")
        
        # Validate parameter values
        if not isinstance(parameters['fast_period'], int) or parameters['fast_period'] <= 0:
            raise StrategyValidationError("fast_period must be a positive integer")
            
        if not isinstance(parameters['slow_period'], int) or parameters['slow_period'] <= 0:
            raise StrategyValidationError("slow_period must be a positive integer")
            
        if not isinstance(parameters['signal_period'], int) or parameters['signal_period'] <= 0:
            raise StrategyValidationError("signal_period must be a positive integer")
            
        if parameters['fast_period'] >= parameters['slow_period']:
            raise StrategyValidationError("fast_period must be less than slow_period")
            
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if parameters['timeframe'] not in valid_timeframes:
            raise StrategyValidationError(f"Invalid timeframe: {parameters['timeframe']}")
        
        return True
    
    def _validate_rsi_parameters(self, parameters: Dict) -> bool:
        """
        Validate RSI strategy parameters.
        
        Args:
            parameters: Dictionary of RSI parameters
            
        Returns:
            True if the parameters are valid, False otherwise
            
        Raises:
            StrategyValidationError: If the parameters are invalid
        """
        required_params = ['period', 'overbought', 'oversold', 'timeframe']
        
        # Check if all required parameters are present
        for param in required_params:
            if param not in parameters:
                raise StrategyValidationError(f"Missing required parameter: {param}")
        
        # Validate parameter values
        if not isinstance(parameters['period'], int) or parameters['period'] <= 0:
            raise StrategyValidationError("period must be a positive integer")
            
        if not isinstance(parameters['overbought'], (int, float)) or parameters['overbought'] <= 0 or parameters['overbought'] > 100:
            raise StrategyValidationError("overbought must be a number between 0 and 100")
            
        if not isinstance(parameters['oversold'], (int, float)) or parameters['oversold'] <= 0 or parameters['oversold'] >= parameters['overbought']:
            raise StrategyValidationError("oversold must be a number between 0 and overbought")
            
        valid_timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if parameters['timeframe'] not in valid_timeframes:
            raise StrategyValidationError(f"Invalid timeframe: {parameters['timeframe']}")
        
        return True
    
    def _validate_grid_parameters(self, parameters: Dict) -> bool:
        """
        Validate Grid trading strategy parameters.
        
        Args:
            parameters: Dictionary of Grid parameters
            
        Returns:
            True if the parameters are valid, False otherwise
            
        Raises:
            StrategyValidationError: If the parameters are invalid
        """
        required_params = ['upper_price', 'lower_price', 'grid_num', 'quantity']
        
        # Check if all required parameters are present
        for param in required_params:
            if param not in parameters:
                raise StrategyValidationError(f"Missing required parameter: {param}")
        
        # Validate parameter values
        if not isinstance(parameters['upper_price'], (int, float)) or parameters['upper_price'] <= 0:
            raise StrategyValidationError("upper_price must be a positive number")
            
        if not isinstance(parameters['lower_price'], (int, float)) or parameters['lower_price'] <= 0:
            raise StrategyValidationError("lower_price must be a positive number")
            
        if parameters['upper_price'] <= parameters['lower_price']:
            raise StrategyValidationError("upper_price must be greater than lower_price")
            
        if not isinstance(parameters['grid_num'], int) or parameters['grid_num'] <= 0:
            raise StrategyValidationError("grid_num must be a positive integer")
            
        if not isinstance(parameters['quantity'], (int, float)) or parameters['quantity'] <= 0:
            raise StrategyValidationError("quantity must be a positive number")
        
        return True 