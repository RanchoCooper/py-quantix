"""
设置管理 API
提供运行时配置管理，页面设置优先级高于 config.yaml
设置存储在内存中（重启重置），如需持久化可保存到 JSON

配置项分类：
1. run: 运行设置 (run_mode, signal_output)
2. exchange: 交易所配置 (api_client, testnet, mode, proxy)
3. binance: 币安凭证 (api_key, api_secret) - 敏感
4. trading: 交易配置 (symbols, 策略参数)
5. strategies: 策略配置 (trend_following, mean_reversion, turtle_trading)
6. notifications: 通知配置 (dingtalk, feishu)
7. logging: 日志配置 (level, file)
8. llm: LLM分析配置
9. market_data: 市场数据配置
"""
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


# ==================== 设置数据模型 ====================

class RunSettings(BaseModel):
    """运行设置"""
    run_mode: str = Field(default="monitor", description="monitor / analyzer")
    signal_output: List[str] = Field(default_factory=lambda: ["console"], description="console / dingtalk / feishu")


class ProxySettings(BaseModel):
    """代理配置"""
    http: str = ""
    https: str = ""


class ExchangeSettings(BaseModel):
    """交易所配置"""
    api_client: str = Field(default="ccxt", description="ccxt / binance")
    testnet: bool = Field(default=True, description="是否使用测试网络")
    mode: str = Field(default="futures", description="spot / futures / swap")
    proxy: ProxySettings = Field(default_factory=ProxySettings)


class BinanceSettings(BaseModel):
    """币安凭证（敏感信息）"""
    api_key: Optional[str] = Field(None, exclude=True)
    api_key_configured: bool = False
    api_secret: Optional[str] = Field(None, exclude=True)
    api_secret_configured: bool = False


class SymbolConfig(BaseModel):
    """单个交易对配置"""
    symbol: str
    leverage: int = Field(default=10, ge=1, le=125)
    position_size: float = Field(default=0.001, ge=0)
    strategy: str = Field(default="trend_following")
    strategy_params: Dict[str, Any] = Field(default_factory=dict)


class TradingSettings(BaseModel):
    """交易配置"""
    symbols: List[SymbolConfig] = Field(default_factory=list)
    confirm_via_feishu: bool = Field(default=False)


class StrategyParams(BaseModel):
    """策略参数"""
    period: Optional[int] = None
    multiplier: Optional[float] = None
    std_dev_multiplier: Optional[float] = None
    entry_period: Optional[int] = None
    exit_period: Optional[int] = None
    atr_period: Optional[int] = None


class StrategiesSettings(BaseModel):
    """策略配置"""
    trend_following: StrategyParams = Field(default_factory=StrategyParams)
    mean_reversion: StrategyParams = Field(default_factory=StrategyParams)
    turtle_trading: StrategyParams = Field(default_factory=StrategyParams)


class DingtalkSettings(BaseModel):
    """钉钉通知设置"""
    webhook_url: str = ""
    secret: str = ""
    enabled: bool = Field(default=False)


class FeishuSettings(BaseModel):
    """飞书通知设置"""
    webhook_url: str = ""
    template_id: str = ""
    template_version: str = ""
    enabled: bool = Field(default=True)


class NotificationSettings(BaseModel):
    """通知设置"""
    dingtalk: DingtalkSettings = Field(default_factory=DingtalkSettings)
    feishu: FeishuSettings = Field(default_factory=FeishuSettings)


class LoggingSettings(BaseModel):
    """日志配置"""
    level: str = Field(default="INFO")
    file: str = Field(default="logs/trading.log")


class LLMSettings(BaseModel):
    """LLM 分析设置"""
    enabled: bool = False
    api_key: Optional[str] = Field(None, exclude=True)
    api_key_configured: bool = False
    base_url: str = "https://api.minimax.chat/v1"
    model: str = "Claude Opus-4.6"
    style: str = "基本面+技术面"
    style_options: List[str] = ["基本面+技术面", "纯技术面", "波段交易", "趋势跟踪", "均值回归"]
    proxy: ProxySettings = Field(default_factory=ProxySettings)


class MarketDataSettings(BaseModel):
    """市场数据配置"""
    interval: str = Field(default="1h")
    limit: int = Field(default=100, ge=10, le=1000)


class SystemSettings(BaseModel):
    """系统设置（只读）"""
    db_path: str = ""
    api_port: int = 8000


class AppSettings(BaseModel):
    """完整应用设置"""
    run: RunSettings = Field(default_factory=RunSettings)
    exchange: ExchangeSettings = Field(default_factory=ExchangeSettings)
    binance: BinanceSettings = Field(default_factory=BinanceSettings)
    trading: TradingSettings = Field(default_factory=TradingSettings)
    strategies: StrategiesSettings = Field(default_factory=StrategiesSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    market_data: MarketDataSettings = Field(default_factory=MarketDataSettings)
    system: SystemSettings = Field(default_factory=SystemSettings)


# ==================== 全局运行时设置存储 ====================

# 缓存 config.yaml 默认设置（避免每次请求重新加载）
_cached_base_settings: Optional[AppSettings] = None

# 运行时覆盖设置（页面级别，高优先级）
_runtime_overrides: Dict[str, Any] = {}


def _load_from_config() -> AppSettings:
    """从 config.yaml 加载默认设置（带缓存）"""
    global _cached_base_settings
    if _cached_base_settings is not None:
        return _cached_base_settings

    # 初始化所有设置对象
    run = RunSettings()
    exchange = ExchangeSettings()
    binance = BinanceSettings()
    trading = TradingSettings()
    strategies = StrategiesSettings()
    notifications = NotificationSettings()
    logging_cfg = LoggingSettings()
    llm = LLMSettings()
    market_data = MarketDataSettings()
    system = SystemSettings()

    try:
        from config.settings import get_settings
        cfg = get_settings()

        # 运行设置
        if hasattr(cfg, "run_mode") and cfg.run_mode:
            run.run_mode = cfg.run_mode
        if hasattr(cfg, "signal_output") and cfg.signal_output:
            run.signal_output = cfg.signal_output if isinstance(cfg.signal_output, list) else [cfg.signal_output]

        # 交易所配置
        e = getattr(cfg, "exchange", None)
        if e:
            if hasattr(e, "api_client") and e.api_client:
                exchange.api_client = e.api_client
            if hasattr(e, "testnet"):
                exchange.testnet = e.testnet
            if hasattr(e, "mode") and e.mode:
                exchange.mode = e.mode
            proxy = getattr(e, "proxy", None)
            if proxy:
                exchange.proxy.http = getattr(proxy, "http", "") or ""
                exchange.proxy.https = getattr(proxy, "https", "") or ""

        # 币安凭证
        b = getattr(cfg, "binance", None)
        if b:
            if getattr(b, "api_key", None):
                binance.api_key_configured = True
            if getattr(b, "api_secret", None):
                binance.api_secret_configured = True

        # 交易配置
        t = getattr(cfg, "trading", None)
        if t:
            symbols_cfg = getattr(t, "symbols", [])
            if symbols_cfg and isinstance(symbols_cfg, list):
                trading.symbols = [
                    SymbolConfig(
                        symbol=item.get("symbol", "") if isinstance(item, dict) else item,
                        leverage=item.get("leverage", 10) if isinstance(item, dict) else 10,
                        position_size=item.get("position_size", 0.001) if isinstance(item, dict) else 0.001,
                        strategy=item.get("strategy", "trend_following") if isinstance(item, dict) else "trend_following",
                        strategy_params=item.get("strategy_params", {}) if isinstance(item, dict) else {},
                    )
                    for item in symbols_cfg
                ]

        # 策略配置
        s = getattr(cfg, "strategies", None)
        if s:
            tf = getattr(s, "trend_following", None)
            if tf:
                strategies.trend_following = StrategyParams(
                    period=getattr(tf, "period", None),
                    multiplier=getattr(tf, "multiplier", None),
                )
            mr = getattr(s, "mean_reversion", None)
            if mr:
                strategies.mean_reversion = StrategyParams(
                    period=getattr(mr, "period", None),
                    std_dev_multiplier=getattr(mr, "std_dev_multiplier", None),
                )
            tt = getattr(s, "turtle_trading", None)
            if tt:
                strategies.turtle_trading = StrategyParams(
                    entry_period=getattr(tt, "entry_period", None),
                    exit_period=getattr(tt, "exit_period", None),
                    atr_period=getattr(tt, "atr_period", None),
                )

        # 通知配置
        n = getattr(cfg, "notifications", None)
        if n:
            dt = getattr(n, "dingtalk", None)
            if dt:
                notifications.dingtalk.webhook_url = getattr(dt, "webhook_url", "") or ""
                notifications.dingtalk.secret = getattr(dt, "secret", "") or ""
            fs = getattr(n, "feishu", None)
            if fs:
                notifications.feishu.webhook_url = getattr(fs, "webhook_url", "") or ""
                notifications.feishu.template_id = getattr(fs, "template_id", "") or ""
                notifications.feishu.template_version = getattr(fs, "template_version", "") or ""

        # 日志配置
        l = getattr(cfg, "logging", None)
        if l:
            if hasattr(l, "level") and l.level:
                logging_cfg.level = l.level
            if hasattr(l, "file") and l.file:
                logging_cfg.file = l.file

        # LLM 配置
        if hasattr(cfg, "llm") and cfg.llm:
            llm.enabled = cfg.llm.enabled or False
            if cfg.llm.api_key:
                llm.api_key_configured = True
            if cfg.llm.base_url:
                llm.base_url = cfg.llm.base_url
            if cfg.llm.model:
                llm.model = cfg.llm.model
            if cfg.llm.style:
                llm.style = cfg.llm.style
            llm_proxy = getattr(cfg.llm, "proxy", None)
            if llm_proxy:
                llm.proxy.http = getattr(llm_proxy, "http", "") or ""
                llm.proxy.https = getattr(llm_proxy, "https", "") or ""

        # 市场数据配置
        md = getattr(cfg, "market_data", None)
        if md:
            if hasattr(md, "interval") and md.interval:
                market_data.interval = md.interval
            if hasattr(md, "limit"):
                market_data.limit = md.limit

    except Exception as e:
        # 允许 config.yaml 不存在或格式错误，使用默认值
        import logging
        logging.getLogger(__name__).warning(f"加载配置文件失败，使用默认值: {e}")

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
        run=run,
        exchange=exchange,
        binance=binance,
        trading=trading,
        strategies=strategies,
        notifications=notifications,
        logging=logging_cfg,
        llm=llm,
        market_data=market_data,
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
                if value is not None and hasattr(target, key):
                    setattr(target, key, value)

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

        配置分类：
        - run: 运行设置
        - exchange: 交易所配置
        - binance: 币安凭证
        - trading: 交易配置
        - strategies: 策略配置
        - notifications: 通知配置
        - logging: 日志配置
        - llm: LLM分析配置
        - market_data: 市场数据配置
        """
        global _runtime_overrides

        updates: Dict[str, Any] = {}

        def non_null(obj: BaseModel) -> Dict[str, Any]:
            return {
                k: v
                for k, v in obj.model_dump(exclude_unset=True, exclude_none=True).items()
                if v != "" and v != []
            }

        # 处理所有配置分类
        if settings.run:
            updates["run"] = non_null(settings.run)
        if settings.exchange:
            updates["exchange"] = non_null(settings.exchange)
        if settings.binance:
            updates["binance"] = non_null(settings.binance)
        if settings.trading:
            updates["trading"] = non_null(settings.trading)
        if settings.strategies:
            updates["strategies"] = non_null(settings.strategies)
        if settings.notifications:
            updates["notifications"] = non_null(settings.notifications)
        if settings.logging:
            updates["logging"] = non_null(settings.logging)
        if settings.llm:
            updates["llm"] = non_null(settings.llm)
        if settings.market_data:
            updates["market_data"] = non_null(settings.market_data)

        if updates:
            _runtime_overrides.update(updates)

        return get_effective_settings()

    @app.delete("/api/settings", response_model=AppSettings, tags=["设置"])
    async def reset_settings():
        """重置所有页面覆盖，恢复到 config.yaml 默认值"""
        global _runtime_overrides
        _runtime_overrides.clear()
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