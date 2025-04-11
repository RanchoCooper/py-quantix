"""
Backtest service implementation.

This module provides the implementation of the Backtest service.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from binance.client import Client

from domain.model.errors import StrategyValidationError
from domain.model.strategy import Strategy
from domain.service.backtest_service import BacktestService
from domain.service.strategy_service import StrategyService

logger = logging.getLogger(__name__)


class BacktestServiceImpl(BacktestService):
    """
    Implementation of the Backtest service.
    
    This service provides backtest functionality for trading strategies.
    """
    
    def __init__(self, client: Client, strategy_service: StrategyService):
        """
        Initialize the Backtest service.
        
        Args:
            client: Binance API client
            strategy_service: Strategy service for validating strategies
        """
        self._client = client
        self._strategy_service = strategy_service
        self._backtest_results = {}  # In-memory storage for backtest results
        logger.info("Initialized Backtest service")
    
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
        # Get the symbol name from the strategy
        symbol_name = self._get_symbol_name_for_strategy(strategy.symbol_id)
        
        # Get parameters
        params = strategy.get_parameters()
        
        # Get historical data
        interval = params.get('timeframe', '1h')
        historical_data = self.get_historical_data(
            symbol_name=symbol_name,
            interval=interval,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        
        # Run the appropriate backtest based on strategy type
        if strategy.type == "MACD":
            result = self._backtest_macd(
                strategy_id=strategy.id,
                df=df,
                params=params,
                initial_balance=initial_balance,
                fee_rate=fee_rate
            )
        elif strategy.type == "RSI":
            result = self._backtest_rsi(
                strategy_id=strategy.id,
                df=df,
                params=params,
                initial_balance=initial_balance,
                fee_rate=fee_rate
            )
        elif strategy.type == "GRID":
            result = self._backtest_grid(
                strategy_id=strategy.id,
                df=df,
                params=params,
                initial_balance=initial_balance,
                fee_rate=fee_rate
            )
        else:
            raise StrategyValidationError(f"Unsupported strategy type for backtesting: {strategy.type}")
        
        # Save the result
        result_id = self.save_backtest_result(strategy.id, result)
        result['backtest_id'] = result_id
        
        return result
    
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
        # Convert datetime to millisecond timestamp
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        # Fetch data from Binance
        klines = self._client.get_historical_klines(
            symbol=symbol_name,
            interval=interval,
            start_str=start_ms,
            end_str=end_ms
        )
        
        # Format data
        formatted_data = []
        for k in klines:
            formatted_data.append({
                'open_time': datetime.fromtimestamp(k[0] / 1000),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'close_time': datetime.fromtimestamp(k[6] / 1000),
                'quote_asset_volume': float(k[7]),
                'number_of_trades': k[8],
                'taker_buy_base_asset_volume': float(k[9]),
                'taker_buy_quote_asset_volume': float(k[10])
            })
        
        return formatted_data
    
    def save_backtest_result(self, strategy_id: str, result: Dict) -> str:
        """
        Save a backtest result.
        
        Args:
            strategy_id: ID of the strategy that was backtested
            result: Backtest result data
            
        Returns:
            ID of the saved backtest result
        """
        backtest_id = str(uuid.uuid4())
        
        # Save timestamp
        result['timestamp'] = datetime.now().isoformat()
        result['strategy_id'] = strategy_id
        
        # Store in memory
        self._backtest_results[backtest_id] = result
        
        return backtest_id
    
    def get_backtest_result(self, backtest_id: str) -> Dict:
        """
        Get a backtest result by its ID.
        
        Args:
            backtest_id: ID of the backtest result
            
        Returns:
            Backtest result data
        """
        if backtest_id not in self._backtest_results:
            raise ValueError(f"Backtest result with ID {backtest_id} not found")
            
        return self._backtest_results[backtest_id]
    
    def get_backtest_results_by_strategy(self, strategy_id: str) -> List[Dict]:
        """
        Get all backtest results for a strategy.
        
        Args:
            strategy_id: ID of the strategy
            
        Returns:
            List of backtest result data
        """
        results = []
        
        for backtest_id, result in self._backtest_results.items():
            if result.get('strategy_id') == strategy_id:
                result_copy = result.copy()
                result_copy['backtest_id'] = backtest_id
                results.append(result_copy)
        
        return results
    
    def _get_symbol_name_for_strategy(self, symbol_id: str) -> str:
        """
        Get the symbol name for a strategy.
        
        This is a placeholder method. In a real implementation, you would
        look up the symbol name from the symbol repository.
        
        Args:
            symbol_id: ID of the symbol
            
        Returns:
            Symbol name
        """
        # For simplicity, we'll just return BTCUSDT
        # In a real implementation, you would query the symbol repository
        return "BTCUSDT"
    
    def _backtest_macd(self, strategy_id: str, df: pd.DataFrame, params: Dict,
                     initial_balance: float, fee_rate: float) -> Dict:
        """
        Run a MACD strategy backtest.
        
        Args:
            strategy_id: ID of the strategy
            df: DataFrame with historical data
            params: Strategy parameters
            initial_balance: Initial balance
            fee_rate: Fee rate
            
        Returns:
            Dictionary with backtest results
        """
        # Extract parameters
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        
        # Calculate MACD
        # Fast EMA
        df['fast_ema'] = df['close'].ewm(span=fast_period, adjust=False).mean()
        
        # Slow EMA
        df['slow_ema'] = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        # MACD Line
        df['macd'] = df['fast_ema'] - df['slow_ema']
        
        # Signal Line
        df['signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
        
        # MACD Histogram
        df['histogram'] = df['macd'] - df['signal']
        
        # Generate signals
        df['signal_buy'] = False
        df['signal_sell'] = False
        
        # Buy when MACD crosses above Signal
        df.loc[(df['macd'] > df['signal']) & (df['macd'].shift(1) <= df['signal'].shift(1)), 'signal_buy'] = True
        
        # Sell when MACD crosses below Signal
        df.loc[(df['macd'] < df['signal']) & (df['macd'].shift(1) >= df['signal'].shift(1)), 'signal_sell'] = True
        
        # Run backtest
        return self._run_backtest_simulation(df, initial_balance, fee_rate)
    
    def _backtest_rsi(self, strategy_id: str, df: pd.DataFrame, params: Dict,
                    initial_balance: float, fee_rate: float) -> Dict:
        """
        Run an RSI strategy backtest.
        
        Args:
            strategy_id: ID of the strategy
            df: DataFrame with historical data
            params: Strategy parameters
            initial_balance: Initial balance
            fee_rate: Fee rate
            
        Returns:
            Dictionary with backtest results
        """
        # Extract parameters
        period = params.get('period', 14)
        overbought = params.get('overbought', 70)
        oversold = params.get('oversold', 30)
        
        # Calculate RSI
        # First, calculate price changes
        df['price_change'] = df['close'].diff()
        
        # Separate gains and losses
        df['gain'] = df['price_change'].apply(lambda x: x if x > 0 else 0)
        df['loss'] = df['price_change'].apply(lambda x: -x if x < 0 else 0)
        
        # Calculate average gain and loss
        df['avg_gain'] = df['gain'].rolling(window=period).mean()
        df['avg_loss'] = df['loss'].rolling(window=period).mean()
        
        # Calculate RS and RSI
        df['rs'] = df['avg_gain'] / df['avg_loss']
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # Generate signals
        df['signal_buy'] = False
        df['signal_sell'] = False
        
        # Buy when RSI crosses above oversold
        df.loc[(df['rsi'] > oversold) & (df['rsi'].shift(1) <= oversold), 'signal_buy'] = True
        
        # Sell when RSI crosses below overbought
        df.loc[(df['rsi'] < overbought) & (df['rsi'].shift(1) >= overbought), 'signal_sell'] = True
        
        # Run backtest
        return self._run_backtest_simulation(df, initial_balance, fee_rate)
    
    def _backtest_grid(self, strategy_id: str, df: pd.DataFrame, params: Dict,
                     initial_balance: float, fee_rate: float) -> Dict:
        """
        Run a Grid trading strategy backtest.
        
        Args:
            strategy_id: ID of the strategy
            df: DataFrame with historical data
            params: Strategy parameters
            initial_balance: Initial balance
            fee_rate: Fee rate
            
        Returns:
            Dictionary with backtest results
        """
        # Extract parameters
        upper_price = params.get('upper_price')
        lower_price = params.get('lower_price')
        grid_num = params.get('grid_num')
        quantity = params.get('quantity')
        
        # Calculate grid levels
        grid_size = (upper_price - lower_price) / grid_num
        grid_levels = [lower_price + i * grid_size for i in range(grid_num + 1)]
        
        # Initialize signals
        df['signal_buy'] = False
        df['signal_sell'] = False
        
        # For each candle, check if price crosses any grid level
        for i in range(1, len(df)):
            prev_close = df.iloc[i-1]['close']
            curr_close = df.iloc[i]['close']
            
            # Check for grid level crossings
            for level in grid_levels:
                # Buy if price crosses a level upward
                if prev_close < level and curr_close >= level:
                    df.iloc[i, df.columns.get_loc('signal_buy')] = True
                
                # Sell if price crosses a level downward
                if prev_close > level and curr_close <= level:
                    df.iloc[i, df.columns.get_loc('signal_sell')] = True
        
        # Run backtest
        return self._run_backtest_simulation(df, initial_balance, fee_rate)
    
    def _run_backtest_simulation(self, df: pd.DataFrame, initial_balance: float, fee_rate: float) -> Dict:
        """
        Run a backtest simulation based on buy/sell signals.
        
        Args:
            df: DataFrame with historical data and signals
            initial_balance: Initial balance
            fee_rate: Fee rate
            
        Returns:
            Dictionary with backtest results
        """
        # Initialize variables
        balance = initial_balance
        position = 0
        entry_price = 0
        trades = []
        
        # Loop through each candle
        for i in range(len(df)):
            date = df.iloc[i]['open_time']
            close_price = df.iloc[i]['close']
            
            # Buy signal
            if df.iloc[i]['signal_buy'] and balance > 0:
                # Calculate quantity to buy
                buy_amount = balance * 0.99  # Keep some for fees
                quantity = buy_amount / close_price
                fee = buy_amount * fee_rate
                
                # Update state
                position = quantity
                entry_price = close_price
                balance = 0
                
                # Record trade
                trades.append({
                    'date': date.isoformat(),
                    'type': 'BUY',
                    'price': close_price,
                    'quantity': quantity,
                    'fee': fee,
                    'balance': balance,
                    'position_value': position * close_price
                })
            
            # Sell signal
            elif df.iloc[i]['signal_sell'] and position > 0:
                # Calculate amount to receive
                sell_amount = position * close_price
                fee = sell_amount * fee_rate
                
                # Update state
                balance = sell_amount - fee
                
                # Calculate profit/loss
                profit_loss = (close_price - entry_price) * position - fee
                profit_loss_pct = (close_price / entry_price - 1) * 100
                
                # Record trade
                trades.append({
                    'date': date.isoformat(),
                    'type': 'SELL',
                    'price': close_price,
                    'quantity': position,
                    'fee': fee,
                    'balance': balance,
                    'position_value': 0,
                    'profit_loss': profit_loss,
                    'profit_loss_pct': profit_loss_pct
                })
                
                # Reset position
                position = 0
                entry_price = 0
        
        # Calculate final value
        final_balance = balance
        if position > 0:
            final_balance += position * df.iloc[-1]['close']
        
        # Calculate performance metrics
        total_return = final_balance - initial_balance
        total_return_pct = (final_balance / initial_balance - 1) * 100
        
        # Calculate drawdown
        portfolio_values = []
        for i in range(len(df)):
            value = 0
            if i > 0:
                # Get the value from the previous day
                value = portfolio_values[-1]['value']
                
                # If there was a trade on this day, update the value
                for trade in trades:
                    trade_date = datetime.fromisoformat(trade['date'])
                    if trade_date.date() == df.iloc[i]['open_time'].date():
                        if trade['type'] == 'BUY':
                            value = trade['position_value']
                        elif trade['type'] == 'SELL':
                            value = trade['balance']
            else:
                value = initial_balance
                
            # Adjust for current price if holding a position
            if position > 0:
                value = balance + position * df.iloc[i]['close']
                
            portfolio_values.append({
                'date': df.iloc[i]['open_time'].isoformat(),
                'value': value
            })
        
        # Calculate maximum drawdown
        max_value = portfolio_values[0]['value']
        max_drawdown = 0
        
        for pv in portfolio_values:
            max_value = max(max_value, pv['value'])
            drawdown = (max_value - pv['value']) / max_value * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # Prepare result
        result = {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'max_drawdown': max_drawdown,
            'trades': trades,
            'portfolio_values': portfolio_values
        }
        
        return result 