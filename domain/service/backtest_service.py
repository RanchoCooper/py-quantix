"""
Backtest service interface.

This module defines the interface for backtest services.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from domain.model.strategy import Strategy


class BacktestService(ABC):
    """
    Interface for backtest services.
    
    This abstract class defines the operations for backtesting trading strategies.
    """
    
    @abstractmethod
    def run_backtest(self, strategy: Strategy, start_date: datetime, end_date: datetime,
                   initial_balance: float, fee_rate: float = 0.001) -> Dict:
        """
        Run a backtest for a strategy.
        
        Args:
            strategy: The strategy to backtest
            start_date: Start date for the backtest
            end_date: End date for the backtest
            initial_balance: Initial balance for the backtest
            fee_rate: Fee rate to apply to trades
            
        Returns:
            Dictionary with backtest results
        """
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol_name: str, interval: str,
                          start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get historical candlestick data for backtesting.
        
        Args:
            symbol_name: Symbol name (e.g., "BTCUSDT")
            interval: Candlestick interval (e.g., "1m", "1h", "1d")
            start_date: Start date for the data
            end_date: End date for the data
            
        Returns:
            List of candlestick data
        """
        pass
    
    @abstractmethod
    def save_backtest_result(self, strategy_id: str, result: Dict) -> str:
        """
        Save a backtest result.
        
        Args:
            strategy_id: ID of the strategy that was backtested
            result: Backtest result data
            
        Returns:
            ID of the saved backtest result
        """
        pass
    
    @abstractmethod
    def get_backtest_result(self, backtest_id: str) -> Dict:
        """
        Get a backtest result by its ID.
        
        Args:
            backtest_id: ID of the backtest result
            
        Returns:
            Backtest result data
        """
        pass
    
    @abstractmethod
    def get_backtest_results_by_strategy(self, strategy_id: str) -> List[Dict]:
        """
        Get all backtest results for a strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            List of backtest result data
        """
        pass 