"""
模拟交易配置
"""
from pydantic import BaseModel


class PaperTradingConfig(BaseModel):
    default_leverage: int = 10
    default_fee_rate: float = 0.0004  # 0.04% 手续费（双向）
    max_position_per_symbol: float = 1.0  # 单交易对最大持仓量
    confirm_via_feishu: bool = True  # 是否每次下单都需要飞书确认
