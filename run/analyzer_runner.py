# -*- coding: utf-8 -*-
"""
市场分析器运行器
用于 analyzer 模式：获取K线数据 → 调用大模型分析 → 发送到消息渠道
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from llm.analyzer import MarketAnalyzer
from exchange.factory import create_exchange_client
from notifications.dingtalk import DingTalkNotifier
from notifications.feishu import FeishuNotifier
from utils.data_formatter import DataFormatter
from utils.symbol_parser import get_symbol_list


class MarketAnalyzerRunner:
    """
    市场分析运行器

    负责：
    1. 从币安获取K线数据
    2. 格式化数据
    3. 调用大模型分析
    4. 发送分析结果到配置的消息渠道
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        llm_config = config.get('llm', {})
        exchange_config = config.get('exchange', config.get('binance', {}))

        self.market_client = create_exchange_client(
            exchange_id="binance",
            testnet=exchange_config.get('testnet', True)
        )

        self.formatter = DataFormatter()

        self.analyzer = MarketAnalyzer(
            api_key=llm_config.get('api_key'),
            base_url=llm_config.get('base_url'),
            model=llm_config.get('model')
        )

        self.market_config = config.get('market_data', {})
        self.interval = self.market_config.get('interval', '1h')
        self.limit = self.market_config.get('limit', 100)

        trading_config = config.get('trading', {})
        self.signal_output = config.get('signal_output', trading_config.get('signal_output', ['console']))

        self.notifiers = self._init_notifiers()

        symbols = trading_config.get('symbols', ['BTCUSDT'])
        self.symbols = get_symbol_list(symbols)

        logger.info(f"市场分析器初始化完成，分析交易对: {self.symbols}")

    @classmethod
    def from_settings(cls, settings):
        """从 Settings 对象创建分析运行器"""
        config = {
            'llm': {
                'api_key': getattr(settings.llm, 'api_key', '') if hasattr(settings, 'llm') else '',
                'base_url': getattr(settings.llm, 'base_url', '') if hasattr(settings, 'llm') else '',
                'model': getattr(settings.llm, 'model', '') if hasattr(settings, 'llm') else '',
            },
            'exchange': {
                'testnet': getattr(settings.exchange, 'testnet', True) if hasattr(settings, 'exchange') else True,
            },
            'trading': {
                'symbols': getattr(settings.trading, 'symbols', ['BTCUSDT']) if hasattr(settings, 'trading') else ['BTCUSDT'],
                'signal_output': getattr(settings.trading, 'signal_output', ['console']) if hasattr(settings, 'trading') else ['console'],
            },
            'notifications': {
                'dingtalk': {
                    'webhook_url': getattr(settings.notifications, 'dingtalk', None) and getattr(settings.notifications.dingtalk, 'webhook_url', '') or '',
                    'secret': getattr(settings.notifications, 'dingtalk', None) and getattr(settings.notifications.dingtalk, 'secret', '') or '',
                },
                'feishu': {
                    'webhook_url': getattr(settings.notifications, 'feishu', None) and getattr(settings.notifications.feishu, 'webhook_url', '') or '',
                    'template_id': getattr(settings.notifications, 'feishu', None) and getattr(settings.notifications.feishu, 'template_id', '') or '',
                    'template_version': getattr(settings.notifications, 'feishu', None) and getattr(settings.notifications.feishu, 'template_version', '') or '',
                },
            },
            'market_data': {
                'interval': getattr(settings.data, 'default_timeframe', '1h') if hasattr(settings, 'data') else '1h',
                'limit': getattr(settings.data, 'limit', 100) if hasattr(settings, 'data') else 100,
            },
        }
        return cls(config)

    def _init_notifiers(self) -> Dict[str, Any]:
        """初始化通知器"""
        notifiers = {}
        notifications_config = self.config.get('notifications', {})
        signal_output = self.signal_output

        logger.info(f"信号输出配置: {signal_output}")

        if 'dingtalk' in notifications_config:
            dingtalk_config = notifications_config['dingtalk']
            if dingtalk_config.get('webhook_url'):
                notifiers['dingtalk'] = DingTalkNotifier(
                    webhook_url=dingtalk_config['webhook_url'],
                    secret=dingtalk_config.get('secret')
                )
                logger.info("钉钉通知器已初始化")

        if 'feishu' in notifications_config:
            feishu_config = notifications_config['feishu']
            if feishu_config.get('webhook_url'):
                notifiers['feishu'] = FeishuNotifier(
                    webhook_url=feishu_config['webhook_url'],
                    template_id=feishu_config.get('template_id'),
                    template_version=feishu_config.get('template_version')
                )
                logger.info("飞书通知器已初始化")

        return notifiers

    def run(self, send_notification: bool = True) -> Dict[str, Any]:
        logger.info("=" * 50)
        logger.info("开始市场分析流程")
        logger.info("=" * 50)

        results = {}

        logger.info("步骤1: 获取K线数据...")
        klines_data = self.market_client.fetch_klines(
            self.symbols, self.interval, self.limit
        )

        if not klines_data:
            logger.error("获取K线数据失败")
            return {}

        logger.info(f"成功获取 {len(klines_data)} 个交易对的数据")

        logger.info("步骤2: 格式化数据...")
        formatted_data = {}
        for symbol, klines in klines_data.items():
            formatted_text = self.formatter.format_for_analysis(
                symbol, klines, self.interval
            )
            if "无数据" not in formatted_text:
                formatted_data[symbol] = formatted_text
            else:
                logger.warning(f"{symbol} 无数据，跳过分析")

        if not formatted_data:
            logger.error("所有交易对都无数据，无法进行分析")
            return {}

        logger.info(f"有效数据交易对: {list(formatted_data.keys())}")

        logger.info("步骤3: 调用大模型分析...")
        analysis_results = self.analyzer.analyze_multiple(formatted_data)

        for symbol, result in analysis_results.items():
            if result:
                logger.info(f"{symbol} 分析结果长度: {len(result)} 字符")
            else:
                logger.warning(f"{symbol} 分析结果为空")

        if send_notification and analysis_results:
            logger.info("步骤4: 发送通知...")
            self._send_notifications(analysis_results)

        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbols": self.symbols,
            "interval": self.interval,
            "klines_data": klines_data,
            "formatted_data": formatted_data,
            "analysis_results": analysis_results
        }

        logger.info("=" * 50)
        logger.info("市场分析流程完成!")
        logger.info("=" * 50)

        return results

    def _send_notifications(self, analysis_results: Dict[str, Optional[str]]):
        """发送分析结果到配置的消息渠道"""
        summary = "📊 量化分析报告\n"
        summary += f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        summary += f"分析交易对: {', '.join(analysis_results.keys())}\n\n"

        for symbol, result in analysis_results.items():
            if result:
                summary += f"• {symbol}: 分析完成\n"

        for output in self.signal_output:
            if output == 'console':
                logger.info("=" * 50)
                logger.info("分析报告汇总")
                logger.info("=" * 50)
                logger.info(summary)
                for symbol, result in analysis_results.items():
                    if result:
                        logger.info(f"--- {symbol} 分析结果 ---")
                        logger.info(result)
                logger.info("=" * 50)

            elif output == 'dingtalk' and 'dingtalk' in self.notifiers:
                self.notifiers['dingtalk'].send_text(summary)
                for symbol, result in analysis_results.items():
                    if result:
                        self.notifiers['dingtalk'].send_text(
                            f"\n--- {symbol} 分析 ---\n{result}"
                        )

            elif output == 'feishu' and 'feishu' in self.notifiers:
                logger.info("准备发送飞书通知...")
                result1 = self.notifiers['feishu'].send_text(summary)
                logger.info(f"飞书摘要发送结果: {result1}")
                for symbol, result in analysis_results.items():
                    if result:
                        trend = self._detect_trend(result)
                        logger.info(f"发送 {symbol} 分析报告到飞书...")
                        result2 = self.notifiers['feishu'].send_analysis_report(
                            symbol, result, trend
                        )
                        logger.info(f"飞书分析报告发送结果: {result2}")

        logger.info("通知发送完成")

    def _detect_trend(self, result: str) -> str:
        """从分析结果中检测趋势"""
        result_lower = result.lower()
        if "看涨" in result or "上涨" in result or " bullish" in result_lower or "看多" in result:
            return "bull"
        elif "看跌" in result or "下跌" in result or "bearish" in result_lower or "看空" in result:
            return "bear"
        return "neutral"

    def run_loop(self, interval_seconds: int = 3600):
        """循环运行分析"""
        logger.info(f"开始循环分析，间隔: {interval_seconds}秒")

        while True:
            try:
                self.run()
                logger.info(f"等待 {interval_seconds} 秒...")
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("用户中断分析循环")
                break
            except Exception as e:
                logger.error(f"分析循环出错: {e}")
                time.sleep(60)


def run_analyzer(config_path: str = "config/config.yaml"):
    """运行分析器的便捷函数"""
    from config.settings import get_settings

    settings = get_settings(config_path)
    runner = MarketAnalyzerRunner.from_settings(settings)
    runner.run()
