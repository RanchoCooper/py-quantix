# -*- coding: utf-8 -*-
"""
K线数据格式化模块
将原始K线数据转换为适合大模型分析的格式
"""

from typing import Any, Dict, List
from datetime import datetime


class DataFormatter:
    """K线数据格式化器"""

    def format_for_analysis(
        self,
        symbol: str,
        klines: List[Dict[str, Any]],
        interval: str
    ) -> str:
        """
        将K线数据格式化为适合LLM分析的文本格式

        Args:
            symbol: 交易对，如 BTCUSDT
            klines: K线数据列表
            interval: K线周期

        Returns:
            格式化后的文本
        """
        if not klines:
            return f"{symbol}: 无数据"

        # 基础信息
        latest = klines[-1]
        prev = klines[-2] if len(klines) > 1 else latest

        # 计算技术指标
        indicators = self._calculate_indicators(klines)

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
- MA5: {indicators.get('ma5', 'N/A'):.4f}
- MA10: {indicators.get('ma10', 'N/A'):.4f}
- MA20: {indicators.get('ma20', 'N/A'):.4f}
- 成交量变化: {indicators.get('volume_change', 'N/A'):.2f}%
- 波动率: {indicators.get('volatility', 'N/A'):.2f}%

### 最近20根K线数据
```
时间              开盘      最高      最低      收盘      成交量
"""

        # 添加最近20根K线
        recent_klines = klines[-20:] if len(klines) >= 20 else klines
        for k in recent_klines:
            report += f"{self._format_time(k['open_time']):12s} {k['open']:8.4f} {k['high']:8.4f} {k['low']:8.4f} {k['close']:8.4f} {k['volume']:12.4f}\n"

        report += "```"

        return report

    def _calculate_indicators(self, klines: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算简单技术指标"""
        if len(klines) < 5:
            return {}

        closes = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]

        # 移动平均线
        ma5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
        ma10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else 0

        # 成交量变化
        avg_volume = sum(volumes[-5:]) / 5
        volume_change = ((volumes[-1] - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

        # 波动率 (ATR简化版)
        high_low = [k['high'] - k['low'] for k in klines[-14:] if len(klines) >= 14]
        volatility = (sum(high_low) / len(high_low) / closes[-1] * 100) if high_low else 0

        return {
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'volume_change': volume_change,
            'volatility': volatility
        }

    def _format_time(self, timestamp: int) -> str:
        """格式化时间戳"""
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d %H:%M")

    def _calc_change_percent(self, old: float, new: float) -> float:
        """计算涨跌幅"""
        if old == 0:
            return 0
        return (new - old) / old * 100
