from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd
from loguru import logger

# K线列名常量
KLINE_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                 'close_time', 'quote_asset_volume', 'number_of_trades',
                 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']


class BaseStrategy(ABC):
    """
    所有交易策略的抽象基类
    """

    # 子类需要定义最小数据周期
    MIN_PERIOD = 1

    def __init__(self, **kwargs):
        """
        初始化策略基类

        Args:
            **kwargs: 策略参数
        """
        self.params = kwargs
        logger.info(f"{self.__class__.__name__} 策略初始化")

    @staticmethod
    def convert_klines_to_dataframe(klines: List) -> pd.DataFrame:
        """
        将K线数据转换为DataFrame

        支持两种格式：
        1. 原始格式: List[List] - Binance API 返回的原始数据
        2. 字典格式: List[Dict] - BinanceMarketData 返回的格式化数据

        Args:
            klines: K线数据列表

        Returns:
            转换后的DataFrame
        """
        if not klines:
            return pd.DataFrame()

        # 检测数据格式
        first_item = klines[0]
        if isinstance(first_item, dict):
            # 字典格式（BinanceMarketData 返回）
            df = pd.DataFrame(klines)
        else:
            # 原始列表格式
            df = pd.DataFrame(klines, columns=KLINE_COLUMNS)

        # 确保数值列
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            df: 包含K线数据的DataFrame

        Returns:
            包含计算指标的DataFrame
        """
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        基于指标生成交易信号

        Args:
            df: 包含指标的DataFrame

        Returns:
            交易信号字典
        """
        pass

    def evaluate(self, klines: List[List]) -> Dict[str, Any]:
        """
        评估策略并生成交易信号

        Args:
            klines: K线数据

        Returns:
            交易信号字典
        """
        try:
            # 检查数据量
            if len(klines) < self.MIN_PERIOD:
                return {"action": "hold", "reason": f"数据不足，需要至少{self.MIN_PERIOD}条K线数据"}

            # 将K线数据转换为DataFrame
            df = self.convert_klines_to_dataframe(klines)

            # 计算指标
            df = self.calculate_indicators(df)

            # 生成信号
            signal = self.generate_signals(df)
            return signal
        except Exception as e:
            logger.error(f"评估策略 {self.__class__.__name__} 时出错: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}