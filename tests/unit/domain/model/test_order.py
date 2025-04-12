"""
Unit tests for order domain model.
"""
import unittest
from datetime import datetime

from domain.model.order import Order, OrderFill


class TestOrderFill(unittest.TestCase):
    """Test cases for OrderFill class."""

    def test_order_fill_creation(self):
        """Test creating order fill."""
        fill = OrderFill(
            price=100.0,
            quantity=1.5,
            commission=0.015,
            commission_asset="BNB",
            trade_id=12345,
        )

        self.assertEqual(fill.price, 100.0)
        self.assertEqual(fill.quantity, 1.5)
        self.assertEqual(fill.commission, 0.015)
        self.assertEqual(fill.commission_asset, "BNB")
        self.assertEqual(fill.trade_id, 12345)


class TestOrder(unittest.TestCase):
    """Test cases for Order class."""

    def setUp(self):
        """Setup before each test."""
        self.order_time = int(datetime(2023, 1, 1, 10, 0).timestamp() * 1000)
        self.update_time = int(datetime(2023, 1, 1, 10, 5).timestamp() * 1000)

        # Complete order data
        self.order_data = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "clientOrderId": "myOrder123",
            "price": "10000.0",
            "origQty": "1.0",
            "executedQty": "0.5",
            "status": "PARTIALLY_FILLED",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
            "stopPrice": "9800.0",
            "icebergQty": "0.1",
            "time": self.order_time,
            "updateTime": self.update_time,
            "isWorking": True,
            "origQuoteOrderQty": "10000.0",
            "fills": [
                {
                    "price": "10000.0",
                    "qty": "0.5",
                    "commission": "0.01",
                    "commissionAsset": "BNB",
                    "tradeId": 56789,
                }
            ],
        }

        # Minimal order data
        self.minimal_order_data = {
            "symbol": "BTCUSDT",
            "orderId": 12345,
            "clientOrderId": "myOrder123",
            "price": "10000.0",
            "origQty": "1.0",
            "status": "NEW",
            "timeInForce": "GTC",
            "type": "LIMIT",
            "side": "BUY",
        }

    def test_from_dict_complete(self):
        """Test creating order from complete dictionary."""
        order = Order.from_dict(self.order_data)

        self.assertEqual(order.symbol, "BTCUSDT")
        self.assertEqual(order.order_id, 12345)
        self.assertEqual(order.client_order_id, "myOrder123")
        self.assertEqual(order.price, 10000.0)
        self.assertEqual(order.orig_qty, 1.0)
        self.assertEqual(order.executed_qty, 0.5)
        self.assertEqual(order.status, "PARTIALLY_FILLED")
        self.assertEqual(order.time_in_force, "GTC")
        self.assertEqual(order.type, "LIMIT")
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.stop_price, 9800.0)
        self.assertEqual(order.iceberg_qty, 0.1)
        self.assertEqual(order.is_working, True)
        self.assertEqual(order.orig_quote_order_qty, 10000.0)

        # Verify time conversions
        expected_time = datetime.fromtimestamp(self.order_time / 1000)
        self.assertEqual(order.time, expected_time)

        expected_update_time = datetime.fromtimestamp(self.update_time / 1000)
        self.assertEqual(order.update_time, expected_update_time)

        # Verify fills
        self.assertEqual(len(order.fills), 1)
        self.assertEqual(order.fills[0].price, 10000.0)
        self.assertEqual(order.fills[0].quantity, 0.5)
        self.assertEqual(order.fills[0].commission, 0.01)
        self.assertEqual(order.fills[0].commission_asset, "BNB")
        self.assertEqual(order.fills[0].trade_id, 56789)

    def test_from_dict_minimal(self):
        """Test creating order from minimal dictionary."""
        order = Order.from_dict(self.minimal_order_data)

        self.assertEqual(order.symbol, "BTCUSDT")
        self.assertEqual(order.order_id, 12345)
        self.assertEqual(order.client_order_id, "myOrder123")
        self.assertEqual(order.price, 10000.0)
        self.assertEqual(order.orig_qty, 1.0)
        self.assertEqual(order.executed_qty, 0)  # Default value
        self.assertEqual(order.status, "NEW")
        self.assertEqual(order.time_in_force, "GTC")
        self.assertEqual(order.type, "LIMIT")
        self.assertEqual(order.side, "BUY")

        # Optional fields should be None or default values
        self.assertIsNone(order.stop_price)
        self.assertIsNone(order.iceberg_qty)
        self.assertIsNone(order.time)
        self.assertIsNone(order.update_time)
        self.assertTrue(order.is_working)  # Default is True
        self.assertEqual(order.orig_quote_order_qty, 0.0)  # Default value

        # fills default to empty list not None
        self.assertEqual(order.fills, [])


if __name__ == "__main__":
    unittest.main()
