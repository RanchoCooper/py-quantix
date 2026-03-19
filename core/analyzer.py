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

    # 默认配置
    DEFAULT_BASE_URL = "https://api.minimax.chat/v1"
    DEFAULT_MODEL = "Claude Opus-4.6"

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None
    ):
        """
        初始化市场分析器

        Args:
            api_key: API密钥，默认从环境变量读取
            base_url: API地址
            model: 模型名称
        """
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
        """
        调用大模型分析K线数据并预测走势

        Args:
            symbol: 交易对
            formatted_data: 格式化后的K线数据
            style: 分析风格

        Returns:
            分析报告文本，失败返回None
        """
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
            # 检查响应是否包含有效内容
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
        """构建系统提示词"""
        return f"""你是一位专业的数字货币量化交易分析师，擅长{style}分析。

请根据提供的K线数据进行分析，预测未来走势。

分析要求：
1. 结合技术面分析（均线、成交量、波动率等）
2. 结合市场基本面（如有相关信息）
3. 给出明确的涨跌预测和关键支撑/阻力位
4. 风险提示

请用中文输出分析报告，结构清晰，结论明确。"""

    def _build_user_prompt(self, symbol: str, data: str) -> str:
        """构建用户提示词"""
        return f"""请分析以下 {symbol} 的行情数据：

{data}

请给出：
1. 近期走势分析
2. 技术指标解读
3. 未来1-4小时走势预测
4. 关键支撑位和阻力位
5. 风险提示"""

    def _parse_response(self, response: Dict) -> Optional[str]:
        """解析API响应"""
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
        """
        批量分析多个交易对

        Args:
            symbols_data: {symbol: formatted_data} 字典
            style: 分析风格

        Returns:
            {symbol: analysis_result} 字典
        """
        results = {}

        for symbol, data in symbols_data.items():
            logger.info(f"正在分析 {symbol}...")
            result = self.analyze(symbol, data, style)
            results[symbol] = result

        return results
