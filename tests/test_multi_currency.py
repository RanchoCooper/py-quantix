#!/usr/bin/env python3
"""
多币种功能测试
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import TradingEngine
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy
from utils.config_manager import ConfigManager


class TestMultiCurrencySupport(unittest.TestCase):
    """多币种支持测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建多币种配置
        self.multi_currency_config = {
            "binance": {
                "api_key": "test_api_key",
                "api_secret": "test_api_secret",
                "testnet": True
            },
            "trading": {
                "symbols": {
                    "BNBUSDT": {
                        "leverage": 10,
                        "position_size": 0.1,
                        "strategy": "trend_following",
                        "strategy_params": {
                            "period": 14,
                            "multiplier": 2.0
                        }
                    },
                    "BTCUSDT": {
                        "leverage": 5,
                        "position_size": 0.001,
                        "strategy": "mean_reversion",
                        "strategy_params": {
                            "period": 20,
                            "std_dev_multiplier": 2.0
                        }
                    }
                }
            },
            "strategies": {
                "trend_following": {
                    "class": "TrendFollowingStrategy",
                    "module": "strategies.trend_following"
                },
                "mean_reversion": {
                    "class": "MeanReversionStrategy",
                    "module": "strategies.mean_reversion"
                },
                "turtle_trading": {
                    "class": "TurtleTradingStrategy",
                    "module": "strategies.turtle_trading"
                }
            },
            "notifications": {
                "dingtalk": {
                    "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=test_access_token",
                    "secret": "test_secret"
                }
            },
            "logging": {
                "level": "DEBUG",
                "file": "logs/trading.log"
            }
        }

        # 保存配置到临时文件
        self.config_file = "/tmp/test_multi_currency_config.json"
        with open(self.config_file, 'w') as f:
            json.dump(self.multi_currency_config, f)

    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_engine_initialization_with_multi_currency(self, mock_notifier, mock_client):
        """测试多币种交易引擎初始化"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 验证基本属性
        self.assertEqual(engine.mode, "auto")
        self.assertIsNotNone(engine.client)
        self.assertIsNotNone(engine.notifier)
        self.assertEqual(len(engine.strategies), 2)
        # 注意：last_signals在初始化时是空字典，只有在运行交易循环后才会填充
        self.assertEqual(len(engine.last_signals), 0)
        self.assertEqual(len(engine.positions), 0)

        # 验证策略类型
        self.assertIsInstance(engine.strategies['BNBUSDT'], TrendFollowingStrategy)
        self.assertIsInstance(engine.strategies['BTCUSDT'], MeanReversionStrategy)

        # 验证last_signals和positions在初始化时为空
        self.assertEqual(engine.last_signals, {})
        self.assertEqual(engine.positions, {})

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_single_currency_evaluation(self, mock_notifier, mock_client):
        """测试单个交易对策略评估"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 模拟市场数据
        mock_klines = [
            [1640995200000, "40000", "41000", "39000", "40500", "1000", 1640995259999, "40000000", 100, "500", "2000000", "0"],
            [1640995260000, "40500", "41500", "40000", "41000", "1100", 1640995319999, "41000000", 110, "550", "2100000", "0"]
        ]
        engine._get_market_data = Mock(return_value=mock_klines)

        # 模拟策略评估结果
        mock_signal = {"action": "buy", "price": 41000, "reason": "测试信号"}
        for strategy in engine.strategies.values():
            strategy.evaluate = Mock(return_value=mock_signal)

        # 测试单个交易对策略评估
        signal_bnb = engine.evaluate_strategy("BNBUSDT")
        signal_btc = engine.evaluate_strategy("BTCUSDT")

        # 验证返回结果
        self.assertEqual(signal_bnb, mock_signal)
        self.assertEqual(signal_btc, mock_signal)

        # 验证策略的evaluate方法被调用
        engine.strategies["BNBUSDT"].evaluate.assert_called_once_with(mock_klines)
        engine.strategies["BTCUSDT"].evaluate.assert_called_once_with(mock_klines)

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_all_currencies_evaluation(self, mock_notifier, mock_client):
        """测试所有交易对策略评估"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 模拟市场数据
        mock_klines = [
            [1640995200000, "40000", "41000", "39000", "40500", "1000", 1640995259999, "40000000", 100, "500", "2000000", "0"],
            [1640995260000, "40500", "41500", "40000", "41000", "1100", 1640995319999, "41000000", 110, "550", "2100000", "0"]
        ]
        engine._get_market_data = Mock(return_value=mock_klines)

        # 模拟策略评估结果
        mock_signal_bnb = {"action": "buy", "price": 41000, "reason": "BNB买入信号"}
        mock_signal_btc = {"action": "sell", "price": 41000, "reason": "BTC卖出信号"}
        engine.strategies["BNBUSDT"].evaluate = Mock(return_value=mock_signal_bnb)
        engine.strategies["BTCUSDT"].evaluate = Mock(return_value=mock_signal_btc)

        # 测试所有交易对策略评估
        signals = engine.evaluate_all_strategies()

        # 验证返回结果
        self.assertIsInstance(signals, dict)
        self.assertEqual(len(signals), 2)
        self.assertEqual(signals["BNBUSDT"], mock_signal_bnb)
        self.assertEqual(signals["BTCUSDT"], mock_signal_btc)

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_single_currency_execution(self, mock_notifier, mock_client):
        """测试单个交易对交易执行"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 模拟交易信号
        signal = {"action": "buy", "price": 41000, "reason": "买入信号"}

        # 模拟客户端下单
        mock_order = {
            "orderId": 123456,
            "symbol": "BNBUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.1"
        }
        mock_client_instance = mock_client.return_value
        mock_client_instance.place_order.return_value = mock_order

        # 执行交易
        success = engine._execute_trade("BNBUSDT", signal)

        # 验证交易执行结果
        self.assertTrue(success)
        mock_client_instance.place_order.assert_called_once_with(
            symbol="BNBUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.1
        )

        # 验证持仓更新
        self.assertIn("BNBUSDT", engine.positions)
        self.assertEqual(engine.positions["BNBUSDT"]["side"], "BUY")
        self.assertEqual(engine.positions["BNBUSDT"]["size"], 0.1)

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_run_once_for_single_currency(self, mock_notifier, mock_client):
        """测试单个交易对运行一次交易循环"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 修改引擎只包含一个交易对，以便测试run_once_for_symbol
        engine.strategies = {"BNBUSDT": engine.strategies["BNBUSDT"]}
        engine.last_signals = {"BNBUSDT": None}
        engine.positions = {"BNBUSDT": {}}

        # 模拟市场数据和策略信号
        mock_klines = [
            [1640995200000, "40000", "41000", "39000", "40500", "1000", 1640995259999, "40000000", 100, "500", "2000000", "0"]
        ]
        engine._get_market_data = Mock(return_value=mock_klines)

        mock_signal = {"action": "buy", "price": 41000, "reason": "买入信号"}
        engine.strategies["BNBUSDT"].evaluate = Mock(return_value=mock_signal)

        # 模拟客户端下单
        mock_order = {
            "orderId": 123456,
            "symbol": "BNBUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.1"
        }
        mock_client_instance = mock_client.return_value
        mock_client_instance.place_order.return_value = mock_order

        # 运行一次交易循环
        success = engine.run_once()

        # 验证执行结果
        self.assertTrue(success)
        engine.strategies["BNBUSDT"].evaluate.assert_called_once_with(mock_klines)
        mock_client_instance.place_order.assert_called_once_with(
            symbol="BNBUSDT",
            side="BUY",
            order_type="MARKET",
            quantity=0.1
        )

    @patch('core.engine.BinanceFuturesClient')
    @patch('notifications.dingtalk.DingTalkNotifier')
    def test_run_once_for_multiple_currencies(self, mock_notifier, mock_client):
        """测试多个交易对运行一次交易循环"""
        # 创建交易引擎实例
        engine = TradingEngine(self.config_file, mode="auto")

        # 模拟市场数据和策略信号
        mock_klines = [
            [1640995200000, "40000", "41000", "39000", "40500", "1000", 1640995259999, "40000000", 100, "500", "2000000", "0"]
        ]
        engine._get_market_data = Mock(return_value=mock_klines)

        mock_signal_bnb = {"action": "buy", "price": 41000, "reason": "BNB买入信号"}
        mock_signal_btc = {"action": "sell", "price": 41000, "reason": "BTC卖出信号"}
        engine.strategies["BNBUSDT"].evaluate = Mock(return_value=mock_signal_bnb)
        engine.strategies["BTCUSDT"].evaluate = Mock(return_value=mock_signal_btc)

        # 模拟客户端下单
        mock_order = {
            "orderId": 123456,
            "symbol": "TESTUSDT",
            "side": "BUY",
            "type": "MARKET",
            "quantity": "0.1"
        }
        mock_client_instance = mock_client.return_value
        mock_client_instance.place_order.return_value = mock_order

        # 运行一次交易循环
        success = engine.run_once()

        # 验证执行结果
        self.assertTrue(success)
        engine.strategies["BNBUSDT"].evaluate.assert_called_once_with(mock_klines)
        engine.strategies["BTCUSDT"].evaluate.assert_called_once_with(mock_klines)


if __name__ == '__main__':
    unittest.main()
