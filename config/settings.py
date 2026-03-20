"""
配置管理模块
使用 pydantic-settings 进行配置管理，支持 .env 文件和环境变量
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProxyConfig(BaseSettings):
    """代理配置"""
    http: str = ""
    https: str = ""

    model_config = SettingsConfigDict(env_prefix="PROXY_")


class ExchangeConfig(BaseSettings):
    """交易所配置"""
    # 交易所名称: binance, okx, bybit 等
    exchange: str = "binance"

    # API密钥
    api_key: str = Field(default="", validation_alias="EXCHANGE_API_KEY")
    api_secret: str = Field(default="", validation_alias="EXCHANGE_API_SECRET")
    passphrase: str = Field(default="", validation_alias="EXCHANGE_PASSPHRASE")

    # 交易模式: spot, futures, swap
    mode: str = "futures"

    # 合约类型: linear (线性合约), inverse (反向合约)
    contract_type: str = "linear"

    # 测试模式
    testnet: bool = True

    # 代理配置
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    # 交易手续费返佣ID
    rebate_id: str = ""

    model_config = SettingsConfigDict(env_prefix="EXCHANGE_")


class SymbolConfig(BaseSettings):
    """单个交易对配置"""
    symbol: str
    leverage: int = 10
    position_size: float = 0.001
    strategy: str = "trend_following"
    strategy_params: Dict[str, Any] = {}


class TradingConfig(BaseSettings):
    """交易配置"""
    # 交易标的 - 支持列表和字典两种格式
    symbols: List[str] = ["BTCUSDT"]

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

    model_config = SettingsConfigDict(env_prefix="TRADING_")


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

    model_config = SettingsConfigDict(env_prefix="DATA_")


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

    model_config = SettingsConfigDict(env_prefix="BACKTEST_")


class DingtalkConfig(BaseSettings):
    """钉钉配置"""
    webhook_url: str = ""
    secret: str = ""

    model_config = SettingsConfigDict(env_prefix="DINGTALK_")


class FeishuConfig(BaseSettings):
    """飞书配置"""
    webhook_url: str = ""
    secret: str = ""

    model_config = SettingsConfigDict(env_prefix="FEISHU_")


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

    model_config = SettingsConfigDict(env_prefix="NOTIFY_")


class LLMConfig(BaseSettings):
    """LLM 分析配置"""
    enabled: bool = False
    api_key: str = ""
    base_url: str = "https://api.minimax.chat/v1"
    model: str = "Claude Opus-4.6"
    style: str = "基本面+技术面"
    proxy: ProxyConfig = Field(default_factory=ProxyConfig)

    model_config = SettingsConfigDict(env_prefix="LLM_")


class LogConfig(BaseSettings):
    """日志配置"""
    level: str = "INFO"
    file: str = "logs/trading.log"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

    model_config = SettingsConfigDict(env_prefix="LOG_")


class StrategyConfig(BaseSettings):
    """策略配置"""
    trend_following: Dict[str, Any] = {"period": 14, "multiplier": 2}
    mean_reversion: Dict[str, Any] = {"period": 20, "std_dev_multiplier": 2}
    turtle_trading: Dict[str, Any] = {"entry_period": 20, "exit_period": 10}

    model_config = SettingsConfigDict(env_prefix="STRATEGY_")


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    @classmethod
    def from_yaml(cls, config_path: str) -> "Settings":
        """从 YAML 配置文件加载"""
        import yaml
        from pathlib import Path

        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


# 全局配置实例
settings: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None) -> Settings:
    """
    获取配置实例

    Args:
        config_path: 配置文件路径（YAML格式）

    Returns:
        Settings 实例
    """
    global settings

    if settings is not None:
        return settings

    if config_path and os.path.exists(config_path):
        settings = Settings.from_yaml(config_path)
    else:
        settings = Settings()

    return settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """重新加载配置"""
    global settings

    if config_path and os.path.exists(config_path):
        settings = Settings.from_yaml(config_path)
    else:
        settings = Settings()

    return settings
