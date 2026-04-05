# -*- coding: utf-8 -*-
"""
大模型分析模块 - 支持 MiniMax Claude
"""

import os
from typing import Any, Dict, Optional

import requests
from loguru import logger


class MarketAnalyzer:
    """市场分析器 - 调用大模型分析K线数据"""

    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"
    DEFAULT_MODEL = "Claude Opus-4.6"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.base_url = base_url or os.getenv("MINIMAX_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = model or os.getenv("MODEL_NAME", self.DEFAULT_MODEL)
        self.session = requests.Session()

    def analyze(
        self,
        symbol: str,
        formatted_data: str,
        style: str = "基本面+技术面"
    ) -> Optional[str]:
        if not self.api_key:
            logger.error("未配置 MINIMAX_API_KEY，请在配置文件的 llm.api_key 中设置，或设置环境变量 MINIMAX_API_KEY")
            return None

        logger.info(f"开始分析 {symbol}, API URL: {self.base_url}/text/chatcompletion_v2, Model: {self.model}")

        system_prompt = self._build_system_prompt(style)
        user_prompt = self._build_user_prompt(symbol, formatted_data)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/text/chatcompletion_v2",
                headers=headers,
                json=payload,
                timeout=60
            )
            logger.info(f"API 响应状态码: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            if result.get("choices"):
                logger.info(f"API 响应成功，返回 {len(result.get('choices', []))} 个结果")
            else:
                logger.warning(f"API 响应无有效内容: {result}")
            return self._parse_response(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"调用大模型失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析响应失败: {e}")
            return None

    def _build_system_prompt(self, style: str) -> str:
        return f"""你是一位专业的数字货币量化交易分析师，擅长{style}分析。

请根据提供的K线数据给出具体的、可执行的仓位建议。输出必须包含以下JSON格式的操作指令：

```json
{{
  "signal": "做多" | "做空" | "观望",
  "confidence": 0.0-1.0,
  "entry_price": number,
  "stop_loss": number,
  "take_profit_1": number,
  "take_profit_2": number,
  "position_size_pct": 0-100,
  "risk_reward_ratio": number,
  "reasoning": "做多/做空/观望的理由"
}}
```

信号规则：
- signal: "做多" 表示建议开多仓，"做空" 表示建议开空仓，"观望" 表示当前不适合入场
- entry_price: 建议的开仓点位（当前价或关键支撑/阻力位附近）
- stop_loss: 止损点位（必须设置在入场价的反方向）
- take_profit_1: 第一止盈点位（较近的目标）
- take_profit_2: 第二止盈点位（较远的目标）
- position_size_pct: 建议仓位比例（百分比）
- risk_reward_ratio: 风险回报比（止盈幅度/止损幅度）

分析要求：
1. 结合技术面分析（均线、成交量、波动率、RSI、布林带等）
2. 识别关键支撑位和阻力位
3. 计算合理的止损止盈位置
4. 评估当前趋势强度和趋势持续性
5. 风险提示（高波动性、流动性风险等）

请先输出结构化分析，最后以JSON格式输出操作指令。"""

    def _build_user_prompt(self, symbol: str, data: str) -> str:
        return f"""请分析以下 {symbol} 的行情数据：

{data}

请输出完整分析报告，结构如下：

## 一、技术面分析
### 1. 近期走势概述
### 2. 均线系统解读（MA5/MA10/MA20/MA60）
### 3. 成交量分析
### 4. 波动率评估

## 二、关键价位
- 支撑位1:
- 支撑位2:
- 阻力位1:
- 阻力位2:
- 当前价格:

## 三、技术指标解读
- RSI:
- MACD:
- 布林带:
- ATR:

## 四、综合判断
[结合以上分析，给出综合判断]

## 五、操作指令（必须以JSON格式输出）
```json
{{
  "signal": "做多",
  "confidence": 0.75,
  "entry_price": 65000,
  "stop_loss": 63000,
  "take_profit_1": 67000,
  "take_profit_2": 69000,
  "position_size_pct": 30,
  "risk_reward_ratio": 1.5,
  "reasoning": "理由说明"
}}
```"""

    def _parse_response(self, response: Dict) -> Optional[str]:
        try:
            choices = response.get("choices", [])
            if choices and len(choices) > 0:
                return choices[0].get("message", {}).get("content", "")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"解析响应格式错误: {e}")
            return None

    def analyze_multiple(
        self,
        symbols_data: Dict[str, str],
        style: str = "基本面+技术面"
    ) -> Dict[str, Optional[str]]:
        results = {}
        for symbol, data in symbols_data.items():
            logger.info(f"正在分析 {symbol}...")
            result = self.analyze(symbol, data, style)
            results[symbol] = result
        return results
