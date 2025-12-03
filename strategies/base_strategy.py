from abc import ABC, abstractmethod
from typing import Any, Dict, List

import pandas as pd
from loguru import logger


class BaseStrategy(ABC):
    """
    所有交易策略的抽象基类
    """

    def __init__(self, **kwargs):
        """
        初始化策略基类

        Args:
            **kwargs: 策略参数
        """
        self.params = kwargs
        logger.info(f"{self.__class__.__name__} 策略初始化")

    @abstractmethod
    def calculate_indicators(self, klines: List[List]) -> pd.DataFrame:
        """
        计算技术指标

        Args:
            klines: K线数据

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
            # 将K线数据转换为DataFrame
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                               'close_time', 'quote_asset_volume', 'number_of_trades',
                                               'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            
            df = self.calculate_indicators(df)
            signal = self.generate_signals(df)
            return signal
        except Exception as e:
            logger.error(f"评估策略 {self.__class__.__name__} 时出错: {e}")
            return {"action": "hold", "reason": f"错误: {str(e)}"}