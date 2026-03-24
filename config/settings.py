"""
配置管理模块
使用 pydantic-settings 进行配置管理，支持 .env 文件和环境变量
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProxyConfig(BaseSettings):
    """代理配置"""
    http: str = ""
    https: str = ""

    model_config = SettingsConfigDict(env_prefix="PROXY_", extra="ignore")


class ExchangeConfig(BaseSettings):
    """交易所配置"""
    # 交易所名称: binance, okx, bybit 等
    exchange: str = "binance"

    # API密钥（通过 EXCHANGE_API_KEY / EXCHANGE_API_SECRET / EXCHANGE_PASSPHRASE 环境变量覆盖）
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""

    # 交易模式: spot, futures, swap
    mode: str = "futures"

    # 合约类型: linear (线性合约), inverse (反向合约)
    contract_type: str = "linear"

    # 测试模式
    testnet: bool = True

    # API 客户端类型: ccxt, binance (官方API)
    api_client: str = "ccxt"

    # 代理配置
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    # 交易手续费返佣ID
    rebate_id: str = ""

    model_config = SettingsConfigDict(env_prefix="EXCHANGE_", extra="ignore")


class SymbolConfig(BaseSettings):
    """单个交易对配置"""
    symbol: str
    leverage: int = 10
    position_size: float = 0.001
    strategy: str = "trend_following"
    strategy_params: Dict[str, Any] = {}

    model_config = SettingsConfigDict(env_prefix="SYMBOL_", extra="ignore")


class TradingConfig(BaseSettings):
    """交易配置"""
    # 交易标的 - 支持两种格式：
    # 1. 简单列表: ["BTCUSDT", "BNBUSDT"]
    # 2. 详细配置: [{symbol: "BTCUSDT", leverage: 10, ...}, ...]
    symbols: List[Union[str, Dict[str, Any]]] = ["BTCUSDT"]

    # 仓位管理
    max_position_size: float = 0.1
    risk_per_trade: float = 0.02

    # 杠杆倍数
    leverage: int = 10

    # 止盈止损
    take_profit_pct: float = 0.02
    stop_loss_pct: float = 0.01

    # 滑点设置
    slippage_pct: float = 0.0005

    # 信号输出方式
    signal_output: List[str] = ["console"]

    model_config = SettingsConfigDict(env_prefix="TRADING_", extra="ignore")


class DataConfig(BaseSettings):
    """数据配置"""
    # K线时间周期
    timeframes: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]

    # 默认时间周期
    default_timeframe: str = "1h"

    # 数据存储路径
    data_path: str = "./data/storage"

    # K线缓存数量
    max_candles_in_memory: int = 1000

    # 获取数量
    limit: int = 100

    model_config = SettingsConfigDict(env_prefix="DATA_", extra="ignore")


class NetworkConfig(BaseSettings):
    """网络请求配置"""
    # API 重试配置
    max_retries: int = 3
    retry_delay: float = 1.0  # 初始重试延迟（秒）
    backoff_factor: float = 2.0  # 退避因子

    # 请求间隔
    request_delay: float = 0.2  # 请求之间的延迟（秒）

    # 超时配置
    timeout: int = 30  # 请求超时（秒）

    model_config = SettingsConfigDict(env_prefix="NETWORK_", extra="ignore")


class BacktestConfig(BaseSettings):
    """回测配置"""
    # 回测时间范围
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"

    # 初始资金
    initial_balance: float = 10000

    # 手续费率
    commission: float = 0.0004

    # 滑点
    slippage: float = 0.0005

    model_config = SettingsConfigDict(env_prefix="BACKTEST_", extra="ignore")


class DingtalkConfig(BaseSettings):
    """钉钉配置"""
    webhook_url: str = ""
    secret: str = ""

    model_config = SettingsConfigDict(env_prefix="DINGTALK_", extra="ignore")


class FeishuConfig(BaseSettings):
    """飞书配置"""
    webhook_url: str = ""
    secret: str = ""

    model_config = SettingsConfigDict(env_prefix="FEISHU_", extra="ignore")


class NotificationConfig(BaseSettings):
    """通知配置"""
    # 通知开关
    enabled: bool = True

    # 钉钉
    dingtalk: DingtalkConfig = Field(default_factory=DingtalkConfig)

    # 飞书
    feishu: FeishuConfig = Field(default_factory=FeishuConfig)

    # 通知事件
    notify_on_trade: bool = True
    notify_on_error: bool = True
    notify_on_daily: bool = True

    model_config = SettingsConfigDict(env_prefix="NOTIFY_", extra="ignore")


class LLMConfig(BaseSettings):
    """LLM 分析配置"""
    enabled: bool = False
    api_key: str = ""
    base_url: str = "https://api.minimax.chat/v1"
    model: str = "Claude Opus-4.6"
    style: str = "基本面+技术面"
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")


class LogConfig(BaseSettings):
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/trading.log"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")


class StrategyConfig(BaseSettings):
    """策略配置"""
    trend_following: Dict[str, Any] = {"period": 14, "multiplier": 2}
    mean_reversion: Dict[str, Any] = {"period": 20, "std_dev_multiplier": 2}
    turtle_trading: Dict[str, Any] = {"entry_period": 20, "exit_period": 10}

    model_config = SettingsConfigDict(env_prefix="STRATEGY_", extra="ignore")


class Settings(BaseSettings):
    """全局配置"""
    # 环境
    env: str = "development"

    # 模式: backtest, paper, live
    mode: str = "paper"

    # 运行模式: monitor, analyzer
    run_mode: str = "monitor"

    # 交易所
    exchange: ExchangeConfig = Field(default_factory=ExchangeConfig)

    # 交易
    trading: TradingConfig = Field(default_factory=TradingConfig)

    # 数据
    data: DataConfig = Field(default_factory=DataConfig)

    # 回测
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    # 通知
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    # LLM
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # 日志
    logging: LogConfig = Field(default_factory=LogConfig)

    # 策略
    strategies: StrategyConfig = Field(default_factory=StrategyConfig)

    # 网络配置
    network: NetworkConfig = Field(default_factory=NetworkConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",  # 允许 YAML 中的额外字段
    )

    @classmethod
    def from_yaml(cls, config_path: str) -> "Settings":
        """
        从 YAML 配置文件加载。

        环境变量优先于 YAML 配置（支持 EXCHANGE_API_KEY, EXCHANGE_API_SECRET 等覆盖）。
        """
        import yaml
        from pathlib import Path

        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        # 先用 env vars 初始化（优先级高于 YAML）
        instance = cls()

        # 再用 YAML 值覆盖（非凭证字段优先使用 YAML）
        if config_data:
            instance._apply_yaml(config_data)

        return instance

    def _apply_yaml(self, data: Dict[str, Any]) -> None:
        """
        将 YAML 配置应用到实例。

        对于嵌套的 BaseSettings 子类字段（如 exchange.proxy），
        使用 model_validate 正确构造子模型实例，而非 setattr 直接赋值
        （后者在 BaseSettings 上不会触发 pydantic 验证，会导致嵌套字段
        被保存为原始 dict 而非子模型对象）。
        """
        import os

        for key, value in data.items():
            if key == "exchange" and isinstance(value, dict):
                secret_fields = {"api_key", "api_secret", "passphrase"}
                env_prefix_map = {
                    "api_key": "EXCHANGE_API_KEY",
                    "api_secret": "EXCHANGE_API_SECRET",
                    "passphrase": "EXCHANGE_PASSPHRASE",
                }
                if hasattr(self, key):
                    nested = getattr(self, key)
                    for field_name in secret_fields:
                        env_var = env_prefix_map.get(field_name)
                        yaml_val = value.get(field_name)
                        current_val = getattr(nested, field_name, None)
                        if (env_var and os.getenv(env_var)) or (not current_val and yaml_val):
                            if hasattr(nested, field_name):
                                setattr(nested, field_name, os.getenv(env_var) or yaml_val)
                    for k, v in value.items():
                        if k not in secret_fields and hasattr(nested, k):
                            if k == "proxy" and isinstance(v, dict):
                                # 正确构造 ProxyConfig 子模型实例
                                proxy_instance = ProxyConfig.model_validate(v)
                                setattr(nested, k, proxy_instance)
                            else:
                                setattr(nested, k, v)
            elif key == "llm" and isinstance(value, dict):
                if hasattr(self, key):
                    nested = getattr(self, key)
                    llm_env = os.getenv("LLM_API_KEY")
                    for k, v in value.items():
                        if k == "api_key" and llm_env:
                            setattr(nested, k, llm_env)
                        elif k == "proxy" and isinstance(v, dict):
                            proxy_instance = ProxyConfig.model_validate(v)
                            setattr(nested, k, proxy_instance)
                        elif hasattr(nested, k):
                            setattr(nested, k, v)
            elif key == "notifications" and isinstance(value, dict):
                if hasattr(self, key):
                    nested = getattr(self, key)
                    for sub_key, sub_data in value.items():
                        if isinstance(sub_data, dict) and hasattr(nested, sub_key):
                            sub_nested = getattr(nested, sub_key)
                            for k, v in sub_data.items():
                                if hasattr(sub_nested, k):
                                    setattr(sub_nested, k, v)
            elif key in ("strategies", "logging", "trading", "data", "backtest", "network", "market_data"):
                if hasattr(self, key) and isinstance(value, dict):
                    nested = getattr(self, key)
                    for k, v in value.items():
                        if hasattr(nested, k):
                            setattr(nested, k, v)
            else:
                if hasattr(self, key):
                    setattr(self, key, value)


# 模块级缓存（用于向后兼容）
_settings_cache: Dict[str, Settings] = {}


def get_settings(config_path: Optional[str] = None) -> Settings:
    """
    获取配置实例（带缓存）

    Args:
        config_path: 配置文件路径（YAML格式）

    Returns:
        Settings 实例
    """
    cache_key = config_path or "__default__"

    if cache_key in _settings_cache:
        return _settings_cache[cache_key]

    if config_path and os.path.exists(config_path):
        settings = Settings.from_yaml(config_path)
    else:
        settings = Settings()

    _settings_cache[cache_key] = settings
    return settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """重新加载配置（清除缓存）"""
    cache_key = config_path or "__default__"

    if config_path and os.path.exists(config_path):
        settings = Settings.from_yaml(config_path)
    else:
        settings = Settings()

    _settings_cache[cache_key] = settings
    return settings


def clear_settings_cache() -> None:
    """清除配置缓存"""
    _settings_cache.clear()


# 向后兼容别名
settings: Optional[Settings] = None
