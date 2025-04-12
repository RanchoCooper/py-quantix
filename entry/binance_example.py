#!/usr/bin/env python
"""
Binance API example script.

This script demonstrates using the Binance exchange adapter to interact with Binance API.
"""
import logging
import sys
from pprint import pprint

from adapter.di.container import AppContainer
from config.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """
    Main function to demonstrate Binance API usage.
    """
    # Load configuration
    config = load_config()

    # Initialize container
    container = AppContainer()
    container.config.from_dict(config)

    # Get exchange service
    exchange_service = container.exchange_service()

    try:
        # Get exchange info
        print("Getting exchange info...")
        exchange_info = exchange_service.get_exchange_info()
        print(f"Exchange timezone: {exchange_info['timezone']}")
        print(f"Exchange server time: {exchange_info['serverTime']}")

        # Get symbols
        print("\nGetting symbols...")
        symbols = exchange_service.get_symbols()
        print(f"Found {len(symbols)} symbols")

        # Get first 5 symbols as examples
        print("\nFirst 5 symbols:")
        for i, symbol in enumerate(symbols[:5]):
            print(f"{i+1}. {symbol.symbol}: {symbol.base_asset}/{symbol.quote_asset}")

        # Select a symbol to work with
        test_symbol = "BTCUSDT"
        print(f"\nUsing {test_symbol} for further operations")

        # Get ticker
        print("\nGetting ticker...")
        ticker = exchange_service.get_ticker(symbol=test_symbol)
        print(f"Price: {ticker['lastPrice']}")

        # Get order book
        print("\nGetting order book...")
        order_book = exchange_service.get_order_book(symbol=test_symbol, limit=5)
        print("Top 5 bids:")
        for bid in order_book["bids"][:5]:
            print(f"Price: {bid[0]}, Quantity: {bid[1]}")

        print("\nTop 5 asks:")
        for ask in order_book["asks"][:5]:
            print(f"Price: {ask[0]}, Quantity: {ask[1]}")

        # Get recent trades
        print("\nGetting recent trades...")
        trades = exchange_service.get_recent_trades(symbol=test_symbol, limit=5)
        print("Recent trades:")
        for trade in trades[:5]:
            print(
                f"Price: {trade['price']}, Quantity: {trade['qty']}, Time: {trade['time']}"
            )

        # Get historical klines
        print("\nGetting historical klines...")
        klines = exchange_service.get_historical_klines(
            symbol=test_symbol, interval="1h", limit=5
        )
        print("Recent klines:")
        for kline in klines[:5]:
            print(
                f"Open time: {kline[0]}, Open: {kline[1]}, High: {kline[2]}, Low: {kline[3]}, Close: {kline[4]}"
            )

        # If API key and secret are provided, get account info
        if (
            config["exchange"]["binance"]["api_key"]
            and config["exchange"]["binance"]["api_secret"]
        ):
            print("\nGetting account info...")
            account = exchange_service.get_account_info()
            balances = exchange_service.get_account_balance()

            print("Account status:", account["status"])
            print("Account balances:")
            for asset, balance in balances.items():
                print(
                    f"{asset}: Free: {balance['free']}, Locked: {balance['locked']}, Total: {balance['total']}"
                )
        else:
            print("\nAPI key and secret not provided. Skipping account operations.")

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
