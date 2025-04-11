"""
Symbol service implementation.

This module provides the implementation of the Symbol domain service.
"""
import logging
from typing import Dict, List

from domain.event.base_event import EventBus
from domain.model.errors import SymbolNotFoundError
from domain.model.symbol import Symbol
from domain.repository.symbol_repository import SymbolRepository
from domain.service.exchange_service import ExchangeService
from domain.service.symbol_service import SymbolService

logger = logging.getLogger(__name__)


class SymbolServiceImpl(SymbolService):
    """
    Implementation of the Symbol domain service.
    
    This service contains domain logic for managing trading symbols.
    """
    
    def __init__(self, repository: SymbolRepository, exchange_service: ExchangeService, event_bus: EventBus):
        """
        Initialize the Symbol service.
        
        Args:
            repository: Repository for Symbol entities
            exchange_service: Exchange service for interacting with the exchange
            event_bus: Event bus for publishing domain events
        """
        self._repository = repository
        self._exchange_service = exchange_service
        self._event_bus = event_bus
        logger.info("Initialized Symbol service")
    
    def sync_symbols(self) -> List[Symbol]:
        """
        Synchronize symbols from the exchange.
        
        This method fetches symbol information from the exchange and updates
        the local database.
        
        Returns:
            A list of synchronized Symbol entities
        """
        logger.info("Synchronizing symbols from exchange")
        exchange_symbols = self._exchange_service.get_symbols()
        
        # Get existing symbols from repository
        existing_symbols = {symbol.name: symbol for symbol in self._repository.get_all()}
        
        # Update or create symbols
        synced_symbols = []
        for exchange_symbol in exchange_symbols:
            existing_symbol = existing_symbols.get(exchange_symbol.name)
            
            if existing_symbol:
                # Update existing symbol
                updated_symbol = existing_symbol.update(
                    status=exchange_symbol.status,
                    min_quantity=exchange_symbol.min_quantity,
                    max_quantity=exchange_symbol.max_quantity,
                    step_size=exchange_symbol.step_size,
                    min_notional=exchange_symbol.min_notional
                )
                synced_symbols.append(self._repository.save(updated_symbol))
            else:
                # Create new symbol
                synced_symbols.append(self._repository.save(exchange_symbol))
        
        logger.info(f"Synchronized {len(synced_symbols)} symbols")
        return synced_symbols
    
    def get_symbol(self, symbol_id: str) -> Symbol:
        """
        Get a symbol by its ID.
        
        Args:
            symbol_id: The ID of the symbol to get
            
        Returns:
            The found Symbol
            
        Raises:
            SymbolNotFoundError: If the symbol with the given ID doesn't exist
        """
        symbol = self._repository.get_by_id(symbol_id)
        if not symbol:
            raise SymbolNotFoundError(symbol_id)
        return symbol
    
    def get_symbol_by_name(self, name: str) -> Symbol:
        """
        Get a symbol by its name.
        
        Args:
            name: The name of the symbol to get (e.g., "BTCUSDT")
            
        Returns:
            The found Symbol
            
        Raises:
            SymbolNotFoundError: If the symbol with the given name doesn't exist
        """
        symbol = self._repository.get_by_name(name)
        if not symbol:
            # Try to get it from the exchange
            exchange_symbol = self._exchange_service.get_symbol(name)
            if not exchange_symbol:
                raise SymbolNotFoundError(f"Symbol with name '{name}' not found")
            # Save and return the symbol
            return self._repository.save(exchange_symbol)
        return symbol
    
    def get_all_symbols(self) -> List[Symbol]:
        """
        Get all symbols.
        
        Returns:
            A list of all Symbol entities
        """
        return self._repository.get_all()
    
    def get_ticker(self, symbol_name: str) -> Dict:
        """
        Get current price ticker for a symbol.
        
        Args:
            symbol_name: The name of the symbol (e.g., "BTCUSDT")
            
        Returns:
            Dictionary with ticker information
        """
        return self._exchange_service.get_ticker(symbol_name)
    
    def get_klines(self, symbol_name: str, interval: str, 
                  limit: int = 500) -> List[Dict]:
        """
        Get candlestick data for a symbol.
        
        Args:
            symbol_name: The name of the symbol (e.g., "BTCUSDT")
            interval: Kline/candlestick interval (e.g., "1m", "5m", "1h", "1d")
            limit: Number of candles to return
            
        Returns:
            List of candlestick data
        """
        return self._exchange_service.get_klines(symbol_name, interval, limit) 