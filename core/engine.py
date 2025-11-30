import importlib
import json
import time
from typing import Any, Dict, List

from loguru import logger

from core.binance_client import BinanceFuturesClient
from notifications.dingtalk import DingTalkNotifier


class TradingEngine:
    """
    主交易引擎，集成策略、API连接器和通知系统
    支持多币种交易，每个币种可以使用不同的策略
    """

    def __init__(self, config_path: str = "config/config.json", mode: str = "auto"):
        """
        初始化交易引擎

        Args:
            config_path: 配置文件路径
            mode: 运行模式 ("auto" 或 "monitor")
        """
        self.config = self._load_config(config_path)
        self.mode = mode  # 运行模式
        self.client = self._init_binance_client()
        self.notifier = self._init_notifier()
        # 为每个交易对初始化策略
        self.strategies = self._init_strategies()
        self.last_signals = {}  # 存储每个交易对的最后信号
        self.positions = {}     # 存储每个交易对的持仓信息

        logger.info(f"交易引擎初始化完成，运行模式: {mode}")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        从JSON文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"配置已从 {config_path} 加载")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise

    def _init_binance_client(self) -> BinanceFuturesClient:
        """
        初始化币安期货客户端，并为所有交易对设置杠杆

        Returns:
            BinanceFuturesClient实例
        """
        binance_config = self.config['binance']
        client = BinanceFuturesClient(
            api_key=binance_config['api_key'],
            api_secret=binance_config['api_secret'],
            testnet=binance_config['testnet']
        )

        # 为所有交易对设置杠杆
        trading_symbols = self.config['trading']['symbols']
        for symbol, symbol_config in trading_symbols.items():
            try:
                client.set_leverage(
                    symbol=symbol,
                    leverage=symbol_config['leverage']
                )
                logger.info(f"已为 {symbol} 设置杠杆 {symbol_config['leverage']}")
            except Exception as e:
                logger.warning(f"为 {symbol} 设置杠杆失败: {e}")

        return client

    def _init_notifier(self) -> DingTalkNotifier:
        """
        初始化钉钉通知器

        Returns:
            DingTalkNotifier实例
        """
        notify_config = self.config['notifications']['dingtalk']
        return DingTalkNotifier(
            webhook_url=notify_config['webhook_url'],
            secret=notify_config.get('secret')
        )

    def _init_strategies(self) -> Dict[str, Any]:
        """
        为每个交易对初始化对应的交易策略

        Returns:
            包含交易对和策略实例映射的字典
        """
        strategies = {}
        trading_symbols = self.config['trading']['symbols']

        for symbol, symbol_config in trading_symbols.items():
            strategy_name = symbol_config['strategy']
            # 优先使用交易对特定的策略参数，否则使用全局策略配置
            if 'strategy_params' in symbol_config:
                strategy_config = symbol_config['strategy_params']
            else:
                strategy_config = self.config['strategies'].get(strategy_name, {})

            # 动态导入并实例化策略
            try:
                module = importlib.import_module(f"strategies.{strategy_name}")
                strategy_class = getattr(module, f"{strategy_name.title().replace('_', '')}Strategy")
                strategy = strategy_class(**strategy_config)
                strategies[symbol] = strategy
                logger.info(f"交易对 {symbol} 的策略 {strategy_name} 初始化完成")
            except Exception as e:
                logger.error(f"初始化交易对 {symbol} 的策略 {strategy_name} 失败: {e}")
                raise

        return strategies

    def _get_market_data(self, symbol: str, interval: str = "1h", limit: int = 100) -> list:
        """
        从币安获取市场数据(K线)

        Args:
            symbol: 交易对符号
            interval: K线间隔
            limit: 获取K线数量

        Returns:
            K线列表
        """
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            return klines
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            raise

    def _execute_trade(self, symbol: str, signal: Dict[str, Any]) -> bool:
        """
        根据信号执行交易

        Args:
            symbol: 交易对符号
            signal: 来自策略的交易信号

        Returns:
            表示成功的布尔值
        """
        if signal['action'] == 'hold':
            return True

        trading_symbols = self.config['trading']['symbols']
        symbol_config = trading_symbols.get(symbol, {})
        position_size = symbol_config.get('position_size', 0.001)

        # 发送交易通知（无论哪种模式都会发送）
        self.notifier.send_trade_notification(
            symbol=symbol,
            action=signal['action'],
            price=signal.get('price', 0),
            reason=signal.get('reason', ''),
            position_size=position_size
        )

        # 根据运行模式决定是否真正下单
        if self.mode == "monitor":
            logger.info(f"[监控模式] 发现交易信号但不执行下单: {signal}")
            return True
        elif self.mode == "auto":
            try:
                # 确定订单方向
                side = signal['action'].upper()

                # 下市价单
                order = self.client.place_order(
                    symbol=symbol,
                    side=side,
                    order_type="MARKET",
                    quantity=position_size
                )

                logger.info(f"订单已下单: {order}")

                # 更新持仓状态
                self.positions[symbol] = {
                    'side': side,
                    'size': position_size,
                    'entry_price': signal.get('price', 0)
                }

                return True

            except Exception as e:
                logger.error(f"执行交易失败: {e}")
                self.notifier.send_system_alert(
                    "交易执行失败",
                    f"错误: {str(e)}"
                )
                return False
        else:
            logger.warning(f"未知的运行模式: {self.mode}，默认不执行交易")
            return False

    def evaluate_strategy(self, symbol: str) -> Dict[str, Any]:
        """
        使用最新市场数据评估指定交易对的策略

        Args:
            symbol: 交易对符号

        Returns:
            策略评估结果
        """
        try:
            # 获取市场数据
            klines = self._get_market_data(symbol)

            # 获取对应交易对的策略
            strategy = self.strategies.get(symbol)
            if not strategy:
                logger.error(f"未找到交易对 {symbol} 的策略")
                return {"action": "hold", "reason": f"未找到交易对 {symbol} 的策略"}

            # 评估策略
            signal = strategy.evaluate(klines)

            logger.info(f"交易对 {symbol} 的策略信号: {signal}")
            return signal

        except Exception as e:
            logger.error(f"评估交易对 {symbol} 的策略失败: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}

    def evaluate_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """
        评估所有交易对的策略

        Returns:
            包含所有交易对策略信号的字典
        """
        signals = {}
        for symbol in self.strategies.keys():
            signals[symbol] = self.evaluate_strategy(symbol)
        return signals

    def run_once(self) -> bool:
        """
        运行一次交易循环（为向后兼容保留）

        Returns:
            表示成功的布尔值
        """
        # 如果只有一个交易对，则使用原来的逻辑
        if len(self.strategies) == 1:
            symbol = next(iter(self.strategies.keys()))
            return self.run_once_for_symbol(symbol)
        else:
            # 多个交易对的情况，运行所有交易对
            return self.run_once_for_all_symbols()

    def run_once_for_symbol(self, symbol: str) -> bool:
        """
        为指定交易对运行一次交易循环

        Args:
            symbol: 交易对符号

        Returns:
            表示成功的布尔值
        """
        try:
            # 评估策略
            signal = self.evaluate_strategy(symbol)

            # 检查是否是新信号
            if signal != self.last_signals.get(symbol):
                logger.info(f"交易对 {symbol} 检测到新信号: {signal}")

                # 执行交易
                success = self._execute_trade(symbol, signal)

                # 更新最后信号
                self.last_signals[symbol] = signal

                return success
            else:
                logger.debug(f"交易对 {symbol} 无新信号")
                return True

        except Exception as e:
            logger.error(f"运行交易对 {symbol} 的交易循环失败: {e}")
            self.notifier.send_system_alert(
                "交易循环错误",
                f"交易对 {symbol} 错误: {str(e)}"
            )
            return False

    def run_once_for_all_symbols(self) -> bool:
        """
        为所有交易对运行一次交易循环

        Returns:
            表示成功的布尔值
        """
        success = True
        signals = self.evaluate_all_strategies()

        for symbol, signal in signals.items():
            try:
                # 检查是否是新信号
                if signal != self.last_signals.get(symbol):
                    logger.info(f"交易对 {symbol} 检测到新信号: {signal}")

                    # 执行交易
                    trade_success = self._execute_trade(symbol, signal)
                    success = success and trade_success

                    # 更新最后信号
                    self.last_signals[symbol] = signal
                else:
                    logger.debug(f"交易对 {symbol} 无新信号")

            except Exception as e:
                logger.error(f"运行交易对 {symbol} 的交易循环失败: {e}")
                self.notifier.send_system_alert(
                    "交易循环错误",
                    f"交易对 {symbol} 错误: {str(e)}"
                )
                success = False

        return success

    def run_continuously(self, interval: int = 3600):
        """
        持续运行交易引擎

        Args:
            interval: 每次循环之间的秒数
        """
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
                self.notifier.send_system_alert(
                    "持续运行错误",
                    f"错误: {str(e)}"
                )
                time.sleep(interval)  # 尽管出错也继续运行


# 示例用法
if __name__ == "__main__":
    # 初始化交易引擎
    engine = TradingEngine()

    # 运行一次
    engine.run_once()

    # 或持续运行（取消注释使用）
    # engine.run_continuously(interval=3600)  # 每小时检查一次
