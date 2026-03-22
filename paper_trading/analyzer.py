"""
LLM 市场分析 API
提供基于大模型的市场分析接口，支持配置化的 K 线数据获取和分析
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

# 尝试导入现有组件（分析器模块不一定存在时优雅降级）
_analyzer_module = None
_fetcher_module = None
_formatter_module = None


def _lazy_import():
    """延迟导入核心分析模块"""
    global _analyzer_module, _fetcher_module, _formatter_module
    if _analyzer_module is None:
        try:
            import sys
            import os
            # 将项目根目录加入 path
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root not in sys.path:
                sys.path.insert(0, root)

            from core.analyzer import MarketAnalyzer
            from data.fetchers.market_fetcher import ExchangeClient
            from utils.data_formatter import DataFormatter
            _analyzer_module = MarketAnalyzer
            _fetcher_module = ExchangeClient
            _formatter_module = DataFormatter
        except ImportError as e:
            logger.warning(f"核心分析模块导入失败: {e}")
            raise


# ==================== 请求/响应模型 ====================

class KlineRequest(BaseModel):
    """K 线数据获取请求"""
    symbols: List[str] = Field(..., min_length=1, max_length=20, description="交易对列表")
    timeframe: str = Field(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|1d|1w)$", description="K 线周期")
    limit: int = Field(default=100, ge=10, le=1000, description="K 线数量")


class AnalysisRequest(BaseModel):
    """LLM 分析请求"""
    symbols: List[str] = Field(..., min_length=1, max_length=20, description="交易对列表")
    timeframe: str = Field(default="1h", pattern="^(1m|5m|15m|30m|1h|4h|1d|1w)$", description="K 线周期")
    limit: int = Field(default=100, ge=10, le=1000, description="K 线数量")
    style: str = Field(default="基本面+技术面", description="分析风格")
    llm_api_key: Optional[str] = Field(None, description="LLM API Key（可选，默认用环境变量）")
    llm_base_url: Optional[str] = Field(None, description="LLM API URL（可选）")
    llm_model: Optional[str] = Field(None, description="LLM 模型（可选）")


class KLineDataPoint(BaseModel):
    """单根 K 线数据结构"""
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class SymbolKLineResponse(BaseModel):
    """单个交易对的 K 线数据响应"""
    symbol: str
    interval: str
    klines: List[KLineDataPoint]
    fetched_at: str


class AnalysisResult(BaseModel):
    """单个交易对分析结果"""
    symbol: str
    timestamp: str
    interval: str
    trend: str = Field(description="bull/bear/neutral")
    kline_count: int
    raw_analysis: str
    indicators: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    """完整分析响应"""
    timestamp: str
    results: List[AnalysisResult]
    errors: Dict[str, str] = Field(default_factory=dict)


class LLMConfigResponse(BaseModel):
    """LLM 配置状态响应"""
    configured: bool
    model: Optional[str] = None
    base_url: Optional[str] = None
    style_options: List[str] = Field(default_factory=list)


# ==================== 辅助函数 ====================

# 复用 DataFormatter 中的工具函数
_formatter = None


def _get_formatter():
    """获取 DataFormatter 单例"""
    global _formatter
    if _formatter is None:
        from utils.data_formatter import DataFormatter
        _formatter = DataFormatter()
    return _formatter


def _detect_trend(analysis: str) -> str:
    """从分析文本中检测趋势"""
    text = analysis.lower()
    if any(kw in text for kw in ["看涨", "上涨", "看多", "bullish", "多头", "买入", "做多"]):
        return "bull"
    if any(kw in text for kw in ["看跌", "下跌", "看空", "bearish", "空头", "卖出", "做空"]):
        return "bear"
    return "neutral"


def _normalize_klines(raw: List) -> List[Dict]:
    """规范化 K 线数据"""
    return _get_formatter()._normalize_klines(raw)


def _calc_indicators(klines: List[Dict]) -> Dict[str, Any]:
    """计算简单技术指标"""
    indicators = _get_formatter()._calculate_indicators(klines)
    # 添加 change_pct 和 latest_price
    if len(klines) >= 2:
        latest = klines[-1]
        prev = klines[-2]
        indicators["change_pct"] = round(((latest["close"] - prev["close"]) / prev["close"] * 100), 2) if prev["close"] else 0
        indicators["latest_price"] = latest["close"]
    return indicators


# ==================== API 端点 ====================

def register_analyzer_routes(app: FastAPI):
    """注册分析相关路由"""

    @app.get("/api/analyzer/config", response_model=LLMConfigResponse)
    async def get_llm_config():
        """获取 LLM 配置状态"""
        try:
            _lazy_import()
            import os
            api_key = os.getenv("MINIMAX_API_KEY", "")
            base_url = os.getenv("MINIMAX_BASE_URL", "")
            model = os.getenv("MODEL_NAME", "")
            return LLMConfigResponse(
                configured=bool(api_key),
                model=model or None,
                base_url=base_url or None,
                style_options=["基本面+技术面", "纯技术面", "波段交易", "趋势跟踪", "均值回归"],
            )
        except ImportError:
            return LLMConfigResponse(
                configured=False,
                style_options=["基本面+技术面", "纯技术面", "波段交易", "趋势跟踪", "均值回归"],
            )

    @app.post("/api/analyzer/klines", response_model=List[SymbolKLineResponse])
    async def fetch_klines(req: KlineRequest):
        """
        获取 K 线数据（不经过 LLM 分析）

        用于预览 K 线数据是否正确
        """
        try:
            _lazy_import()
        except ImportError:
            raise HTTPException(status_code=503, detail="分析模块未安装，请检查 core/ 目录")

        client = _fetcher_module(exchange_id="binance", testnet=True)
        results: List[SymbolKLineResponse] = []

        for symbol in req.symbols:
            try:
                raw = await client.fetch_ohlcv(symbol, req.timeframe, req.limit)
                klines = _normalize_klines(raw)
                results.append(SymbolKLineResponse(
                    symbol=symbol,
                    interval=req.timeframe,
                    klines=[KLineDataPoint(**k) for k in klines],
                    fetched_at=datetime.now().isoformat(),
                ))
            except Exception as e:
                logger.error(f"获取 {symbol} K 线失败: {e}")
                raise HTTPException(status_code=400, detail=f"获取 {symbol} K 线失败: {str(e)}")

        return results

    @app.post("/api/analyzer/analyze", response_model=AnalysisResponse)
    async def analyze(req: AnalysisRequest):
        """
        执行 LLM 市场分析

        完整流程：获取 K 线 → 格式化 → 调用 LLM → 返回结果
        """
        try:
            _lazy_import()
        except ImportError:
            raise HTTPException(status_code=503, detail="分析模块未安装，请检查 core/ 目录")

        # 初始化客户端
        api_key = req.llm_api_key or ""
        if not api_key:
            import os
            api_key = os.getenv("MINIMAX_API_KEY", "")

        if not api_key:
            raise HTTPException(status_code=400, detail="未配置 LLM API Key，请设置 MINIMAX_API_KEY 环境变量或传入 llm_api_key 参数")

        analyzer = _analyzer_module(
            api_key=api_key,
            base_url=req.llm_base_url or None,
            model=req.llm_model or None,
        )
        client = _fetcher_module(exchange_id="binance", testnet=True)
        formatter = _formatter_module()

        results: List[AnalysisResult] = []
        errors: Dict[str, str] = {}

        for symbol in req.symbols:
            try:
                # 获取 K 线
                raw = await client.fetch_ohlcv(symbol, req.timeframe, req.limit)
                klines = _normalize_klines(raw)

                if not klines:
                    errors[symbol] = "无 K 线数据"
                    continue

                # 计算指标
                indicators = _calc_indicators(klines[-min(20, len(klines)):])

                # 格式化数据
                formatted = formatter.format_for_analysis(symbol, klines, req.timeframe)

                # 调用 LLM 分析（同步阻塞，包装到线程池避免阻塞事件循环）
                analysis = await asyncio.to_thread(
                    analyzer.analyze, symbol, formatted, req.style
                )

                if not analysis:
                    errors[symbol] = "LLM 分析返回为空"
                    continue

                trend = _detect_trend(analysis)

                results.append(AnalysisResult(
                    symbol=symbol,
                    timestamp=datetime.now().isoformat(),
                    interval=req.timeframe,
                    trend=trend,
                    kline_count=len(klines),
                    raw_analysis=analysis,
                    indicators=indicators,
                ))

            except Exception as e:
                logger.error(f"分析 {symbol} 失败: {e}")
                errors[symbol] = str(e)

        return AnalysisResponse(
            timestamp=datetime.now().isoformat(),
            results=results,
            errors=errors if errors else {},
        )

    @app.get("/api/analyzer/timeframes")
    async def get_timeframes():
        """获取支持的 K 线周期"""
        return {
            "options": [
                {"value": "1m", "label": "1 分钟"},
                {"value": "5m", "label": "5 分钟"},
                {"value": "15m", "label": "15 分钟"},
                {"value": "30m", "label": "30 分钟"},
                {"value": "1h", "label": "1 小时"},
                {"value": "4h", "label": "4 小时"},
                {"value": "1d", "label": "1 天"},
                {"value": "1w", "label": "1 周"},
            ]
        }

    @app.get("/api/analyzer/symbols/popular")
    async def get_popular_symbols():
        """获取常用交易对列表"""
        return {
            "symbols": [
                {"value": "BTCUSDT", "label": "BTC/USDT"},
                {"value": "ETHUSDT", "label": "ETH/USDT"},
                {"value": "BNBUSDT", "label": "BNB/USDT"},
                {"value": "SOLUSDT", "label": "SOL/USDT"},
                {"value": "XRPUSDT", "label": "XRP/USDT"},
                {"value": "ADAUSDT", "label": "ADA/USDT"},
                {"value": "DOGEUSDT", "label": "DOGE/USDT"},
                {"value": "AVAXUSDT", "label": "AVAX/USDT"},
                {"value": "DOTUSDT", "label": "DOT/USDT"},
                {"value": "LINKUSDT", "label": "LINK/USDT"},
                {"value": "MATICUSDT", "label": "MATIC/USDT"},
                {"value": "LTCUSDT", "label": "LTC/USDT"},
            ]
        }
