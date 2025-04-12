"""
Unit tests for symbol domain model.
"""
import unittest

from domain.model.symbol import Symbol, SymbolFilter


class TestSymbolFilter(unittest.TestCase):
    """Test cases for SymbolFilter class."""

    def test_from_dict_price_filter(self):
        """Test creating price filter from dictionary."""
        filter_data = {
            "filterType": "PRICE_FILTER",
            "minPrice": "0.00000100",
            "maxPrice": "100000.00000000",
            "tickSize": "0.00000100",
        }

        filter_obj = SymbolFilter.from_dict(filter_data)

        self.assertEqual(filter_obj.filter_type, "PRICE_FILTER")
        self.assertEqual(filter_obj.min_price, 0.000001)
        self.assertEqual(filter_obj.max_price, 100000.0)
        self.assertEqual(filter_obj.tick_size, 0.000001)
        self.assertIsNone(filter_obj.min_qty)
        self.assertIsNone(filter_obj.max_qty)
        self.assertIsNone(filter_obj.step_size)

    def test_from_dict_lot_size(self):
        """Test creating lot size filter from dictionary."""
        filter_data = {
            "filterType": "LOT_SIZE",
            "minQty": "0.00100000",
            "maxQty": "100000.00000000",
            "stepSize": "0.00100000",
        }

        filter_obj = SymbolFilter.from_dict(filter_data)

        self.assertEqual(filter_obj.filter_type, "LOT_SIZE")
        self.assertEqual(filter_obj.min_qty, 0.001)
        self.assertEqual(filter_obj.max_qty, 100000.0)
        self.assertEqual(filter_obj.step_size, 0.001)
        self.assertIsNone(filter_obj.min_price)
        self.assertIsNone(filter_obj.max_price)
        self.assertIsNone(filter_obj.tick_size)

    def test_from_dict_min_notional(self):
        """Test creating minimum notional filter from dictionary."""
        filter_data = {"filterType": "MIN_NOTIONAL", "minNotional": "0.00100000"}

        filter_obj = SymbolFilter.from_dict(filter_data)

        self.assertEqual(filter_obj.filter_type, "MIN_NOTIONAL")
        self.assertEqual(filter_obj.min_notional, 0.001)
        self.assertIsNone(filter_obj.min_price)
        self.assertIsNone(filter_obj.max_price)
        self.assertIsNone(filter_obj.tick_size)
        self.assertIsNone(filter_obj.min_qty)
        self.assertIsNone(filter_obj.max_qty)
        self.assertIsNone(filter_obj.step_size)


class TestSymbol(unittest.TestCase):
    """Test cases for Symbol class."""

    def setUp(self):
        """Setup before each test."""
        self.symbol_data = {
            "symbol": "BTCUSDT",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "status": "TRADING",
            "filters": [
                {
                    "filterType": "PRICE_FILTER",
                    "minPrice": "0.01000000",
                    "maxPrice": "100000.00000000",
                    "tickSize": "0.01000000",
                },
                {
                    "filterType": "LOT_SIZE",
                    "minQty": "0.00100000",
                    "maxQty": "100000.00000000",
                    "stepSize": "0.00100000",
                },
                {"filterType": "MIN_NOTIONAL", "minNotional": "10.00000000"},
            ],
        }
        self.symbol = Symbol.from_dict(self.symbol_data)

    def test_from_dict(self):
        """Test creating symbol from dictionary."""
        self.assertEqual(self.symbol.symbol, "BTCUSDT")
        self.assertEqual(self.symbol.base_asset, "BTC")
        self.assertEqual(self.symbol.quote_asset, "USDT")
        self.assertEqual(self.symbol.status, "TRADING")
        self.assertEqual(len(self.symbol.filters), 3)

    def test_get_filter(self):
        """Test getting filter by specific type."""
        price_filter = self.symbol.get_filter("PRICE_FILTER")
        lot_size = self.symbol.get_filter("LOT_SIZE")
        min_notional = self.symbol.get_filter("MIN_NOTIONAL")

        self.assertIsNotNone(price_filter)
        self.assertEqual(price_filter.filter_type, "PRICE_FILTER")

        self.assertIsNotNone(lot_size)
        self.assertEqual(lot_size.filter_type, "LOT_SIZE")

        self.assertIsNotNone(min_notional)
        self.assertEqual(min_notional.filter_type, "MIN_NOTIONAL")

        # Test non-existent filter type
        non_existent = self.symbol.get_filter("NON_EXISTENT")
        self.assertIsNone(non_existent)

    def test_get_price_precision(self):
        """Test getting price precision."""
        # When tick_size is 0.01, precision should be 2
        price_filter = self.symbol.get_filter("PRICE_FILTER")
        self.assertEqual(price_filter.tick_size, 0.01)
        self.assertEqual(self.symbol.get_price_precision(), 2)

        # Test default value when no filter exists
        original_filters = self.symbol.filters.copy()
        self.symbol.filters = [
            f for f in self.symbol.filters if f.filter_type != "PRICE_FILTER"
        ]
        self.assertEqual(self.symbol.get_price_precision(), 8)

        # Restore filters
        self.symbol.filters = original_filters

    def test_get_quantity_precision(self):
        """Test getting quantity precision."""
        # When step_size is 0.001, precision should be 3
        lot_size = self.symbol.get_filter("LOT_SIZE")
        self.assertEqual(lot_size.step_size, 0.001)
        self.assertEqual(self.symbol.get_quantity_precision(), 3)

        # Test default value when no filter exists
        original_filters = self.symbol.filters.copy()
        self.symbol.filters = [
            f for f in self.symbol.filters if f.filter_type != "LOT_SIZE"
        ]
        self.assertEqual(self.symbol.get_quantity_precision(), 8)

        # Restore filters
        self.symbol.filters = original_filters


if __name__ == "__main__":
    unittest.main()
