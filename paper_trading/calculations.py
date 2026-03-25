"""
交易核心计算函数
纯函数，无副作用，供 engine、storage 等模块复用
"""


def calc_margin(quantity: float, price: float, leverage: int) -> float:
    """
    计算开仓所需保证金

    Args:
        quantity: 持仓数量
        price: 入场价格
        leverage: 杠杆倍数

    Returns:
        所需保证金
    """
    return quantity * price / leverage


def calc_fee(amount: float, fee_rate: float = 0.0004) -> float:
    """
    计算手续费（双向）

    Args:
        amount: 成交金额 (quantity * price)
        fee_rate: 手续费率，默认 0.04%

    Returns:
        手续费
    """
    return amount * fee_rate


def calc_pnl(side: str, entry_price: float, current_price: float, quantity: float) -> float:
    """
    计算多头/空头的已实现或浮动盈亏

    Args:
        side: 持仓方向 (long / short)
        entry_price: 入场价格
        current_price: 当前价格
        quantity: 持仓数量

    Returns:
        盈亏金额（已扣除手续费）
    """
    if side == "long":
        return (current_price - entry_price) * quantity
    return (entry_price - current_price) * quantity


def calc_liquidation_price(
    entry_price: float,
    leverage: int,
    side: str,
    mm_ratio: float = 0.5,
) -> float:
    """
    计算预估爆仓价

    Args:
        entry_price: 入场价格
        leverage: 杠杆倍数
        side: 持仓方向 (long / short)
        mm_ratio: 维持保证金率，默认 0.5%

    Returns:
        预估爆仓价
    """
    if leverage <= 0:
        return 0.0
    if side == "long":
        return entry_price * (1 - 1 / leverage - mm_ratio)
    return entry_price * (1 + 1 / leverage + mm_ratio)


def calc_risk_amount(balance: float, risk_per_trade: float) -> float:
    """
    根据账户余额和风险比例计算单笔交易风险金额

    Args:
        balance: 账户余额
        risk_per_trade: 每笔交易风险比例

    Returns:
        风险金额
    """
    return balance * risk_per_trade
