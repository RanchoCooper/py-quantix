# -*- coding: utf-8 -*-
"""
K线数据格式化模块
将原始K线数据转换为适合大模型分析的格式
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

# ==================== 常量定义 ====================
MA_PERIODS = (5, 10, 20)
VOLATILITY_PERIOD = 14


class DataFormatter:
    """K线数据格式化器"""

    def _fmt_indicator(self, value: Any, fmt: str = '.4f') -> str:
        """
        格式化技术指标值

        Args:
            value: 指标值
            fmt: 格式字符串

        Returns:
            格式化后的字符串
        """
        if value is None or (isinstance(value, float) and value == 0):
            return 'N/A'
        return f"{value:{fmt}}" if isinstance(value, (int, float)) else str(value)

    def format_for_analysis(
        self,
        symbol: str,
        klines: List,
        interval: str
    ) -> str:
        """
        将K线数据格式化为适合LLM分析的文本格式

        Args:
            symbol: 交易对，如 BTCUSDT
            klines: K线数据列表，支持两种格式：
                - 字典格式: [{open_time, open, high, low, close, volume}, ...]
                - 列表格式: [[timestamp, open, high, low, close, volume], ...]
            interval: K线周期

        Returns:
            格式化后的文本
        """
        if not klines:
            return f"{symbol}: 无数据"

        # 统一转换为字典格式
        normalized_klines = self._normalize_klines(klines)

        # 基础信息
        latest = normalized_klines[-1]
        prev = normalized_klines[-2] if len(normalized_klines) > 1 else latest

        # 计算技术指标
        indicators = self._calculate_indicators(normalized_klines)

        # 构建分析报告
        report = f"""## {symbol} 行情数据 ({interval})

### 最新K线信息
- 时间: {self._format_time(latest['open_time'])}
- 开盘价: {latest['open']:.4f}
- 最高价: {latest['high']:.4f}
- 最低价: {latest['low']:.4f}
- 收盘价: {latest['close']:.4f}
- 成交量: {latest['volume']:.4f}

### 价格变动
- 涨跌幅: {self._calc_change_percent(prev['close'], latest['close']):.2f}%
- 涨跌额: {latest['close'] - prev['close']:.4f}

### 技术指标
- MA5: {self._fmt_indicator(indicators.get('ma5'))}
- MA10: {self._fmt_indicator(indicators.get('ma10'))}
- MA20: {self._fmt_indicator(indicators.get('ma20'))}
- 成交量变化: {self._fmt_indicator(indicators.get('volume_change'), '.2f')}%
- 波动率: {self._fmt_indicator(indicators.get('volatility'), '.2f')}%

### 最近20根K线数据
```
时间              开盘      最高      最低      收盘      成交量
"""

        # 添加最近20根K线
        recent_klines = normalized_klines[-20:] if len(normalized_klines) >= 20 else normalized_klines
        for k in recent_klines:
            report += f"{self._format_time(k['open_time']):12s} {k['open']:8.4f} {k['high']:8.4f} {k['low']:8.4f} {k['close']:8.4f} {k['volume']:12.4f}\n"

        report += "```"

        return report

    def _normalize_klines(self, klines: List) -> List[Dict[str, Any]]:
        """
        统一K线数据格式为字典列表

        Args:
            klines: 原始K线数据

        Returns:
            字典格式的K线列表

        Raises:
            ValueError: 当K线元素少于6个字段时
        """
        if not klines:
            return []

        # 检查第一个元素是否为字典
        first = klines[0]
        if isinstance(first, dict):
            return klines  # 已经是字典格式

        # 列表格式转换为字典格式
        # ccxt 格式: [timestamp, open, high, low, close, volume, ...]
        normalized = []
        for k in klines:
            if len(k) < 6:
                raise ValueError(f"K线元素至少需要6个字段，实际: {len(k)}")
            normalized.append({
                'open_time': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
            })

        return normalized

    def _calculate_indicators(self, klines: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算简单技术指标（已规范化为字典格式）"""
        if len(klines) < 5:
            return {}

        closes = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]

        # 移动平均线
        ma5 = sum(closes[-5:]) / MA_PERIODS[0] if len(closes) >= MA_PERIODS[0] else 0
        ma10 = sum(closes[-10:]) / MA_PERIODS[1] if len(closes) >= MA_PERIODS[1] else 0
        ma20 = sum(closes[-20:]) / MA_PERIODS[2] if len(closes) >= MA_PERIODS[2] else 0

        # 成交量变化
        avg_volume = sum(volumes[-5:]) / 5
        volume_change = ((volumes[-1] - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

        # 波动率 (真正的 ATR)
        volatility = self._calculate_atr(klines)

        return {
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'volume_change': volume_change,
            'volatility': volatility
        }

    def _calculate_atr(self, klines: List[Dict[str, Any]]) -> float:
        """
        计算平均真实波幅 (ATR)

        使用 True Range: max(high-low, |high-prev_close|, |low-prev_close|)
        """
        if len(klines) < VOLATILITY_PERIOD:
            return 0.0

        true_ranges = []
        for i in range(-VOLATILITY_PERIOD, 0):
            current = klines[i]
            prev = klines[i - 1] if i > 0 else current
            tr0 = current['high'] - current['low']
            tr1 = abs(current['high'] - prev['close'])
            tr2 = abs(current['low'] - prev['close'])
            true_ranges.append(max(tr0, tr1, tr2))

        atr = sum(true_ranges) / VOLATILITY_PERIOD
        return atr / klines[-1]['close'] * 100

    def _format_time(self, timestamp: int) -> str:
        """
        格式化时间戳

        Args:
            timestamp: 时间戳（支持毫秒或秒，自动检测）

        Returns:
            格式化的时间字符串
        """
        # 自动检测时间戳单位：> 10^10 则为毫秒，否则为秒
        ts = timestamp / 1000 if timestamp > 10**10 else timestamp
        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _calc_change_percent(self, old: float, new: float) -> float:
        """计算涨跌幅"""
        if old == 0:
            return 0
        return (new - old) / old * 100
