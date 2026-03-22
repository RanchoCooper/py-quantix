"""
交易引擎模块
主交易引擎集成各组件，负责协调工作流程
"""
import asyncio
import importlib
import time
from typing import Any, Dict, Optional

from loguru import logger

from core.analyzer_runner import MarketAnalyzerRunner
from core.components import (
    SignalProcessor,
    TradeExecutor,
    PositionManager,
    NotificationManager,
)
from data.fetchers.market_fetcher import ExchangeClient
from notifications.dingtalk import DingTalkNotifier
from notifications.feishu import FeishuNotifier
from utils.config_manager import ConfigManager
from utils.symbol_parser import parse_symbol_config


def create_engine(
    config_path: str = "config/config.yaml",
    run_mode: Optional[str] = None
) -> Optional[object]:
    """
    工厂函数：根据配置创建合适的引擎实例

    Args:
        config_path: 配置文件路径
        run_mode: 运行模式，如果为 None 则从配置文件读取

    Returns:
        TradingEngine 或 MarketAnalyzerRunner 实例
    """
    try:
        config = ConfigManager.load_config(config_path)

        # 优先使用传入的 run_mode，否则从配置读取
        actual_mode = run_mode if run_mode else config.get('run_mode', 'monitor')
        logger.info(f"检测到运行模式: {actual_mode}")

        if actual_mode == 'analyzer':
            config['run_mode'] = actual_mode
            return MarketAnalyzerRunner(config)
        else:
            return TradingEngine(config=config, mode='monitor')

    except Exception as e:
        logger.error(f"创建引擎失败: {e}")
        return None


class TradingEngine:
    """
    主交易引擎，集成策略、API连接器和通知系统

    使用组件模式，将职责分解到：
    - SignalProcessor: 信号处理
    - TradeExecutor: 交易执行
    - PositionManager: 仓位管理
    - NotificationManager: 通知管理
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: str = "config/config.yaml",
        mode: str = "auto"
    ):
        """
        初始化交易引擎

        Args:
            config: 配置字典
            config_path: 配置文件路径
            mode: 运行模式
        """
        # 加载配置
        if config is None:
            config = ConfigManager.load_config(config_path)

        self.config = config
        self.mode = mode

        # 初始化组件
        self.client = self._init_client()
        self.strategies = self._init_strategies()
        self.notifiers = self._init_notifiers()

        # 初始化各功能组件
        self.signal_processor = SignalProcessor(self.strategies, self.client)
        self.trade_executor = TradeExecutor(self.client, config)
        self.trade_executor.set_mode(mode)
        self.position_manager = PositionManager()
        self.notification_manager = NotificationManager(self.notifiers, config)

        logger.info(f"交易引擎初始化完成，运行模式: {mode}")

    def _init_client(self) -> ExchangeClient:
        """初始化交易所客户端"""
        binance_config = self.config.get('binance', {})
        client = ExchangeClient(
            exchange_id="binance",
            testnet=binance_config.get('testnet', True)
        )

        # 设置杠杆
        trading_config = self.config.get('trading', {})
        symbols_config = trading_config.get('symbols', [])
        symbol_list = parse_symbol_config(symbols_config)

        for item in symbol_list:
            symbol = item.get('symbol')
            leverage = item.get('leverage', 10)
            try:
                asyncio.run(client.set_leverage(symbol=symbol, leverage=leverage))
                logger.info(f"已为 {symbol} 设置杠杆 {leverage}")
            except Exception as e:
                logger.warning(f"为 {symbol} 设置杠杆失败: {e}")

        return client

    def _init_strategies(self) -> Dict[str, Any]:
        """初始化策略"""
        strategies = {}
        trading_config = self.config.get('trading', {})
        symbols_config = trading_config.get('symbols', [])
        symbol_list = parse_symbol_config(symbols_config)

        for item in symbol_list:
            symbol = item.get('symbol')
            strategy_name = item.get('strategy')

            # 获取策略参数
            if 'strategy_params' in item:
                strategy_config = item['strategy_params']
            else:
                strategy_config = self.config.get('strategies', {}).get(strategy_name, {})

            # 动态导入策略
            try:
                module = importlib.import_module(f"strategies.{strategy_name}")
                class_name_map = {
                    'trend_following': 'TrendFollowingStrategy',
                    'mean_reversion': 'MeanReversionStrategy',
                    'turtle_trading': 'TurtleTradingStrategy'
                }
                class_name = class_name_map.get(
                    strategy_name,
                    f"{strategy_name.title().replace('_', '')}Strategy"
                )
                strategy_class = getattr(module, class_name)
                strategy = strategy_class(**strategy_config)
                strategies[symbol] = strategy
                logger.info(f"交易对 {symbol} 的策略 {strategy_name} 初始化完成")
            except Exception as e:
                logger.error(f"初始化交易对 {symbol} 的策略 {strategy_name} 失败: {e}")
                raise

        return strategies

    def _init_notifiers(self) -> Dict[str, Any]:
        """初始化通知器"""
        notifiers = {}
        notifications_config = self.config.get('notifications', {})

        # 钉钉通知器
        if 'dingtalk' in notifications_config:
            config = notifications_config['dingtalk']
            if config.get('webhook_url'):
                notifiers['dingtalk'] = DingTalkNotifier(
                    webhook_url=config['webhook_url'],
                    secret=config.get('secret')
                )
                logger.info("钉钉通知器已初始化")

        # 飞书通知器
        if 'feishu' in notifications_config:
            config = notifications_config['feishu']
            if config.get('webhook_url'):
                notifiers['feishu'] = FeishuNotifier(
                    webhook_url=config['webhook_url'],
                    template_id=config.get('template_id'),
                    template_version=config.get('template_version')
                )
                logger.info("飞书通知器已初始化")

        return notifiers

    def evaluate_strategy(self, symbol: str) -> Dict[str, Any]:
        """评估指定交易对的策略"""
        return self.signal_processor.evaluate_strategy(symbol)

    def evaluate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """评估所有交易对的策略"""
        return self.signal_processor.evaluate_all_strategies()

    def run_once(self) -> bool:
        """运行一次交易循环"""
        if len(self.strategies) == 1:
            symbol = next(iter(self.strategies.keys()))
            return self._run_once_for_symbol(symbol)
        return self._run_once_for_all_symbols()

    def _run_once_for_symbol(self, symbol: str) -> bool:
        """为单个交易对运行交易循环"""
        try:
            signal = self.signal_processor.evaluate_strategy(symbol)

            if self.signal_processor.has_new_signal(symbol, signal):
                logger.info(f"交易对 {symbol} 检测到新信号: {signal}")

                # 发送通知
                position_size = self.trade_executor.get_position_size(symbol)
                self.notification_manager.send_signal_notification(
                    symbol, signal, position_size
                )

                # 执行交易
                success = self.trade_executor.execute(symbol, signal)

                # 更新信号状态
                self.signal_processor.update_signal(symbol, signal)

                return success
            else:
                logger.debug(f"交易对 {symbol} 无新信号")
                return True

        except Exception as e:
            logger.error(f"运行交易对 {symbol} 的交易循环失败: {e}")
            self.notification_manager.send_system_alert(
                "交易循环错误",
                f"交易对 {symbol} 错误: {str(e)}"
            )
            return False

    def _run_once_for_all_symbols(self) -> bool:
        """为所有交易对运行交易循环"""
        success = True
        signals = self.signal_processor.evaluate_all_strategies()

        for symbol, signal in signals.items():
            try:
                if self.signal_processor.has_new_signal(symbol, signal):
                    logger.info(f"交易对 {symbol} 检测到新信号: {signal}")

                    # 发送通知
                    position_size = self.trade_executor.get_position_size(symbol)
                    self.notification_manager.send_signal_notification(
                        symbol, signal, position_size
                    )

                    # 执行交易
                    trade_success = self.trade_executor.execute(symbol, signal)
                    success = success and trade_success

                    # 更新信号状态
                    self.signal_processor.update_signal(symbol, signal)
                else:
                    logger.debug(f"交易对 {symbol} 无新信号")

            except Exception as e:
                logger.error(f"运行交易对 {symbol} 的交易循环失败: {e}")
                self.notification_manager.send_system_alert(
                    "交易循环错误",
                    f"交易对 {symbol} 错误: {str(e)}"
                )
                success = False

        return success

    def run_continuously(self, interval: int = 3600):
        """持续运行交易引擎"""
        logger.info(f"开始持续运行交易引擎，间隔 {interval} 秒")

        while True:
            try:
                success = self.run_once()
                if not success:
                    logger.warning("交易循环执行失败")

                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("收到键盘中断，停止交易引擎")
                break
            except Exception as e:
                logger.error(f"持续运行期间出错: {e}")
                self.notification_manager.send_system_alert(
                    "持续运行错误",
                    f"错误: {str(e)}"
                )
                time.sleep(interval)
