"""
设置管理 API
提供运行时配置管理，页面设置优先级高于 config.yaml
设置存储在内存中（重启重置），如需持久化可保存到 JSON
"""
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


# ==================== 设置数据模型 ====================

class LLMSettings(BaseModel):
    """LLM 分析设置"""
    enabled: bool = False
    # api_key 只在 PUT 时接收，永不在 GET 响应中返回
    api_key: Optional[str] = Field(None, exclude=True)
    api_key_configured: bool = False  # GET 响应用，指示是否已配置
    base_url: str = "https://api.minimax.chat/v1"
    model: str = "Claude Opus-4.6"
    style: str = "基本面+技术面"
    style_options: list[str] = ["基本面+技术面", "纯技术面", "波段交易", "趋势跟踪", "均值回归"]


class NotificationSettings(BaseModel):
    """通知设置"""
    enabled: bool = True
    feishu_webhook: str = ""
    feishu_secret: str = ""
    notify_on_trade: bool = True
    notify_on_error: bool = True
    notify_on_daily: bool = True


class TradingSettings(BaseModel):
    """交易设置"""
    default_leverage: int = Field(default=10, ge=1, le=125)
    default_fee_rate: float = Field(default=0.0004, ge=0, le=0.01)
    confirm_via_feishu: bool = False
    default_symbols: list[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]


class MarketSettings(BaseModel):
    """市场数据设置"""
    default_timeframe: str = Field(default="1h")
    testnet: bool = True
    symbols: list[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]


class SystemSettings(BaseModel):
    """系统设置（只读）"""
    db_path: str = ""
    api_port: int = 8000


class AppSettings(BaseModel):
    """完整应用设置"""
    llm: LLMSettings = Field(default_factory=LLMSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    market: MarketSettings = Field(default_factory=MarketSettings)
    system: SystemSettings = Field(default_factory=SystemSettings)


# ==================== 全局运行时设置存储 ====================

# 缓存 config.yaml 默认设置（避免每次请求重新加载）
_cached_base_settings: Optional[AppSettings] = None

# 运行时覆盖设置（页面级别，高优先级）
_runtime_overrides: Dict[str, Any] = {}

# 存储 API Key（单独管理，永不序列化到缓存）
_stored_api_keys: Dict[str, str] = {}


def _load_from_config() -> AppSettings:
    """从 config.yaml 加载默认设置（带缓存）"""
    global _cached_base_settings
    if _cached_base_settings is not None:
        return _cached_base_settings

    llm = LLMSettings()
    notifications = NotificationSettings()
    trading = TradingSettings()
    market = MarketSettings()
    system = SystemSettings()

    try:
        from config.settings import get_settings
        cfg = get_settings()

        # LLM 配置
        if hasattr(cfg, "llm") and cfg.llm:
            llm.enabled = cfg.llm.enabled or False
            if cfg.llm.api_key:
                llm.api_key_configured = True
                _stored_api_keys["llm"] = cfg.llm.api_key
            if cfg.llm.base_url:
                llm.base_url = cfg.llm.base_url
            if cfg.llm.model:
                llm.model = cfg.llm.model
            if cfg.llm.style:
                llm.style = cfg.llm.style

        # 通知配置
        n = getattr(cfg, "notifications", None)
        if n:
            notifications.enabled = getattr(n, "enabled", True)
            feishu = getattr(n, "feishu", None)
            if feishu and getattr(feishu, "webhook_url", None):
                notifications.feishu_webhook = feishu.webhook_url
            if feishu and getattr(feishu, "secret", None):
                notifications.feishu_secret = feishu.secret
            notifications.notify_on_trade = getattr(n, "notify_on_trade", True)
            notifications.notify_on_error = getattr(n, "notify_on_error", True)
            notifications.notify_on_daily = getattr(n, "notify_on_daily", True)

        # 交易配置
        t = getattr(cfg, "trading", None)
        if t:
            if getattr(t, "leverage", None):
                trading.default_leverage = min(max(t.leverage, 1), 125)
            symbols = getattr(t, "symbols", [])
            if symbols and isinstance(symbols, list) and isinstance(symbols[0], str):
                trading.default_symbols = symbols

        # 市场配置
        d = getattr(cfg, "data", None)
        if d and getattr(d, "default_timeframe", None):
            market.default_timeframe = d.default_timeframe

        e = getattr(cfg, "exchange", None)
        if e:
            market.testnet = getattr(e, "testnet", True)

    except Exception:
        # 允许 config.yaml 不存在或格式错误，使用默认值
        pass

    # 系统设置
    db_path = os.getenv("PAPER_TRADING_DB", "")
    if not db_path:
        try:
            from paper_trading.database import DATABASE_URL
            if "sqlite" in (DATABASE_URL or ""):
                db_path = DATABASE_URL.split(":///")[1]
        except Exception:
            pass
    system.db_path = db_path or "data/paper_trading.db"

    _cached_base_settings = AppSettings(
        llm=llm,
        notifications=notifications,
        trading=trading,
        market=market,
        system=system,
    )
    return _cached_base_settings


def _merge_settings(base: AppSettings, overrides: Dict[str, Any]) -> AppSettings:
    """合并配置：overrides 优先级高于 base"""
    result = base.model_copy(deep=True)

    for category, values in overrides.items():
        if not hasattr(result, category) or values is None:
            continue
        target = getattr(result, category)
        if isinstance(target, BaseModel):
            for key, value in values.items():
                # api_key 特殊处理：存储到 _stored_api_keys
                if key == "api_key" and value:
                    _stored_api_keys[category] = value
                    continue
                if value is not None and hasattr(target, key):
                    setattr(target, key, value)

    # 补充 api_key_configured 状态
    result.llm.api_key_configured = bool(
        _stored_api_keys.get("llm") or
        (getattr(base.llm, "api_key_configured", False) or
        (overrides.get("llm") or {}).get("api_key")
    ))

    return result


def get_effective_settings() -> AppSettings:
    """获取生效配置（页面覆盖 > config.yaml）"""
    base = _load_from_config()
    if _runtime_overrides:
        return _merge_settings(base, _runtime_overrides)
    return base


# ==================== API 端点 ====================

def register_settings_routes(app: FastAPI):
    """注册设置相关路由"""

    @app.get("/api/settings", response_model=AppSettings, tags=["设置"])
    async def get_settings():
        """获取当前生效配置（合并后的结果）"""
        return get_effective_settings()

    @app.get("/api/settings/defaults", response_model=AppSettings, tags=["设置"])
    async def get_default_settings():
        """获取 config.yaml 默认配置（不含页面覆盖）"""
        return _load_from_config()

    @app.put("/api/settings", response_model=AppSettings, tags=["设置"])
    async def update_settings(settings: AppSettings):
        """
        更新页面级设置（仅更新非空字段）

        设置分为以下类别：
        - llm: LLM 分析配置
        - notifications: 通知配置
        - trading: 交易配置
        - market: 市场配置
        """
        global _runtime_overrides

        updates: Dict[str, Any] = {}

        def non_null(obj: BaseModel) -> Dict[str, Any]:
            return {
                k: v
                for k, v in obj.model_dump(exclude_unset=True, exclude_none=True).items()
                if v != "" and v != []
            }

        if settings.llm:
            updates["llm"] = non_null(settings.llm)
        if settings.notifications:
            updates["notifications"] = non_null(settings.notifications)
        if settings.trading:
            updates["trading"] = non_null(settings.trading)
        if settings.market:
            updates["market"] = non_null(settings.market)

        if updates:
            _runtime_overrides.update(updates)

        return get_effective_settings()

    @app.delete("/api/settings", response_model=AppSettings, tags=["设置"])
    async def reset_settings():
        """重置所有页面覆盖，恢复到 config.yaml 默认值"""
        global _runtime_overrides, _stored_api_keys
        _runtime_overrides.clear()
        _stored_api_keys.clear()
        return _load_from_config()

    @app.get("/api/settings/categories", tags=["设置"])
    async def get_settings_categories():
        """获取设置分类元数据（用于前端渲染）"""
        return {
            "categories": [
                {
                    "key": "llm",
                    "label": "LLM 分析",
                    "icon": "Cpu",
                    "description": "配置大模型 API，用于市场分析",
                    "fields": [
                        {"key": "enabled", "label": "启用 LLM", "type": "switch", "default": False},
                        {"key": "api_key", "label": "API Key", "type": "password", "default": ""},
                        {"key": "api_key_configured", "label": "API Key 状态", "type": "badge", "default": False},
                        {"key": "base_url", "label": "API 地址", "type": "input", "default": "https://api.minimax.chat/v1"},
                        {"key": "model", "label": "模型", "type": "input", "default": "Claude Opus-4.6"},
                        {"key": "style", "label": "分析风格", "type": "select", "options": ["基本面+技术面", "纯技术面", "波段交易", "趋势跟踪", "均值回归"]},
                    ],
                },
                {
                    "key": "notifications",
                    "label": "通知",
                    "icon": "Bell",
                    "description": "配置飞书/钉钉通知推送",
                    "fields": [
                        {"key": "enabled", "label": "启用通知", "type": "switch", "default": True},
                        {"key": "feishu_webhook", "label": "飞书 Webhook", "type": "input", "default": ""},
                        {"key": "feishu_secret", "label": "飞书密钥", "type": "password", "default": ""},
                        {"key": "notify_on_trade", "label": "交易通知", "type": "switch", "default": True},
                        {"key": "notify_on_error", "label": "错误通知", "type": "switch", "default": True},
                        {"key": "notify_on_daily", "label": "每日报告", "type": "switch", "default": True},
                    ],
                },
                {
                    "key": "trading",
                    "label": "交易",
                    "icon": "TrendCharts",
                    "description": "模拟交易默认参数",
                    "fields": [
                        {"key": "default_leverage", "label": "默认杠杆", "type": "number", "min": 1, "max": 125, "default": 10},
                        {"key": "default_fee_rate", "label": "手续费率", "type": "number", "min": 0, "max": 0.01, "step": 0.0001, "default": 0.0004},
                        {"key": "confirm_via_feishu", "label": "飞书确认下单", "type": "switch", "default": False},
                        {"key": "default_symbols", "label": "默认交易对", "type": "tags", "default": ["BTCUSDT", "ETHUSDT"]},
                    ],
                },
                {
                    "key": "market",
                    "label": "市场数据",
                    "icon": "DataLine",
                    "description": "K 线获取和显示配置",
                    "fields": [
                        {"key": "default_timeframe", "label": "默认周期", "type": "select", "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"], "default": "1h"},
                        {"key": "testnet", "label": "使用 Testnet", "type": "switch", "default": True},
                        {"key": "symbols", "label": "交易对列表", "type": "tags", "default": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]},
                    ],
                },
                {
                    "key": "system",
                    "label": "系统",
                    "icon": "Setting",
                    "description": "系统运行参数（部分只读）",
                    "readonly_fields": ["db_path", "api_port"],
                    "fields": [
                        {"key": "db_path", "label": "数据库路径", "type": "readonly", "default": ""},
                        {"key": "api_port", "label": "API 端口", "type": "readonly", "default": 8000},
                    ],
                },
            ]
        }