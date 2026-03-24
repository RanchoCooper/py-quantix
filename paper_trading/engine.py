"""
模拟交易引擎
负责开仓、平仓、持仓更新、盈亏计算等核心逻辑
"""
from typing import Optional, List, Dict, Any

from loguru import logger

from paper_trading.config import PaperTradingConfig
from paper_trading.calculations import calc_margin, calc_fee, calc_pnl
from paper_trading.events import EventBus, get_event_bus
from paper_trading import storage


class PaperTradingEngine:
    """
    模拟交易引擎

    规则：
    - 所有订单假定实时成交（无滑点）
    - 开仓冻结保证金 = 数量 * 入场价 / 杠杆
    - 手续费 = 数量 * 价格 * fee_rate（双向收取）
    - 浮动盈亏 = 数量 * (当前价 - 入场价) * direction
    - 平仓盈亏 = 数量 * (平仓价 - 入场价) * direction - 手续费
    """

    def __init__(self, config: Optional[PaperTradingConfig] = None):
        self.config = config or PaperTradingConfig()
        self._event_bus: EventBus = get_event_bus()

    def add_listener(self, handler):
        """注册事件监听器（用于 SSE 推送）"""
        self._event_bus.subscribe(handler)

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        self._event_bus.emit(event_type, data)


    async def open_position(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_id: Optional[str] = None,
        signal_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        开仓操作

        Args:
            account_id: 账户ID
            symbol: 交易对
            side: 开仓方向 (long/short)
            quantity: 数量
            entry_price: 入场价格
            stop_loss: 止损价格
            take_profit: 止盈价格
            order_id: 关联订单ID
            signal_id: 关联信号ID

        Returns:
            结果字典 {success, position?, order?, error?}
        """
        account = await storage.get_account(account_id)
        if not account:
            return {"success": False, "error": "账户不存在"}

        margin = calc_margin(quantity, entry_price, account.leverage)
        fee = calc_fee(quantity * entry_price, self.config.default_fee_rate)

        available = account.balance - account.frozen_margin
        if margin > available:
            return {
                "success": False,
                "error": f"保证金不足。需 {margin:.2f}，可用 {available:.2f}",
            }

        position = await storage.create_position(
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        order = await storage.create_order(
            account_id=account_id,
            symbol=symbol,
            side="buy",
            order_type="market",
            quantity=quantity,
            position_side=side,
            price=entry_price,
            position_id=position.id,
            signal_id=signal_id,
            source="manual",
            reason=f"开仓: {side.upper()} {quantity} @ {entry_price}",
        )

        await storage.update_order(
            order.id,
            status="filled",
            filled_price=entry_price,
            fee=fee,
        )

        await storage.update_account(
            account_id,
            frozen_margin=account.frozen_margin + margin,
            balance=account.balance - margin - fee,
        )

        self._emit("position_opened", {
            "position_id": position.id,
            "account_id": account_id,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "entry_price": entry_price,
        })

        logger.info(
            f"开仓成功: {symbol} {side.upper()} {quantity} @ {entry_price}, "
            f"保证金: {margin:.2f}, 手续费: {fee:.2f}"
        )

        return {
            "success": True,
            "position": position,
            "order": order,
            "margin_used": margin,
            "fee": fee,
        }

    async def close_position(
        self,
        position_id: str,
        quantity: Optional[float] = None,
        exit_price: Optional[float] = None,
        order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        平仓操作（全平或部分平仓）

        Args:
            position_id: 持仓ID
            quantity: 平仓数量（None = 全平）
            exit_price: 平仓价格（None = 使用传入价格）
            order_id: 关联订单ID

        Returns:
            结果字典
        """
        position = await storage.get_position(position_id)
        if not position:
            return {"success": False, "error": "持仓不存在"}

        account = await storage.get_account(position.account_id)
        if not account:
            return {"success": False, "error": "账户不存在"}

        close_qty = quantity if quantity is not None else position.quantity
        if close_qty > position.quantity:
            return {"success": False, "error": f"平仓数量超过持仓量 ({position.quantity})"}

        if exit_price is None:
            return {"success": False, "error": "平仓价格不能为空"}

        is_full_close = close_qty >= position.quantity

        margin_release = calc_margin(close_qty, position.entry_price, account.leverage)
        fee = calc_fee(close_qty * exit_price, self.config.default_fee_rate)
        raw_pnl = calc_pnl(position.side, position.entry_price, exit_price, close_qty)
        pnl = raw_pnl - fee

        order = await storage.create_order(
            account_id=position.account_id,
            symbol=position.symbol,
            side="sell",
            order_type="market",
            quantity=close_qty,
            position_side=position.side,
            price=exit_price,
            position_id=position_id,
            source="manual",
            reason=f"平仓: {position.side.upper()} {close_qty} @ {exit_price}",
        )

        await storage.update_order(
            order.id,
            status="filled",
            filled_price=exit_price,
            fee=fee,
            pnl=pnl,
        )

        await storage.update_account(
            account.id,
            frozen_margin=max(0, account.frozen_margin - margin_release),
            balance=account.balance + margin_release + pnl,
            total_pnl=account.total_pnl + pnl,
        )

        if is_full_close:
            await storage.delete_position(position_id)
        else:
            await storage.update_position(
                position_id,
                quantity=position.quantity - close_qty,
            )

        await self._update_daily_stats(account.id, pnl)

        self._emit("position_closed", {
            "position_id": position_id,
            "account_id": position.account_id,
            "symbol": position.symbol,
            "quantity": close_qty,
            "exit_price": exit_price,
            "pnl": pnl,
            "is_full_close": is_full_close,
        })

        logger.info(
            f"平仓成功: {position.symbol} {close_qty} @ {exit_price}, "
            f"盈亏: {pnl:.2f}, 手续费: {fee:.2f}"
        )

        return {
            "success": True,
            "order": order,
            "pnl": pnl,
            "fee": fee,
            "margin_released": margin_release,
            "is_full_close": is_full_close,
        }

    async def update_position_prices(
        self,
        account_id: str,
        prices: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """
        批量更新持仓的当前价格和浮动盈亏

        Args:
            account_id: 账户ID
            prices: {symbol: current_price} 字典

        Returns:
            更新后的持仓列表
        """
        positions = await storage.get_positions_by_account(account_id)
        updated = []

        for pos in positions:
            if pos.symbol not in prices:
                continue

            current_price = prices[pos.symbol]
            unrealized_pnl = calc_pnl(pos.side, pos.entry_price, current_price, pos.quantity)

            entry_value = pos.entry_price * pos.quantity
            unrealized_pnl_pct = unrealized_pnl / entry_value * 100 if entry_value > 0 else 0.0

            await storage.update_position(
                pos.id,
                current_price=current_price,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
            )

            updated.append({
                "position_id": pos.id,
                "symbol": pos.symbol,
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
            })

        if updated:
            self._emit("prices_updated", {"positions": updated})

        return updated

    async def check_stop_loss_take_profit(self, position_id: str) -> Optional[Dict[str, Any]]:
        """检查止损止盈，触发则自动平仓"""
        position = await storage.get_position(position_id)
        if not position:
            return None

        triggered = None
        if position.side == "long":
            if position.stop_loss and position.current_price <= position.stop_loss:
                triggered = "stop_loss"
            elif position.take_profit and position.current_price >= position.take_profit:
                triggered = "take_profit"
        else:
            if position.stop_loss and position.current_price >= position.stop_loss:
                triggered = "stop_loss"
            elif position.take_profit and position.current_price <= position.take_profit:
                triggered = "take_profit"

        if triggered:
            price = position.stop_loss if triggered == "stop_loss" else position.take_profit
            return await self.close_position(
                position_id=position_id,
                exit_price=price,
            )
        return None

    async def _update_daily_stats(self, account_id: str, pnl: float):
        """更新日统计数据"""
        account = await storage.get_account(account_id)
        if not account:
            return

        from datetime import date
        today = date.today().isoformat()

        # 查询当天统计以累加 trade_count
        from paper_trading.database import get_session
        from sqlalchemy import select
        from paper_trading.models import DailyStats
        async with get_session() as session:
            result = await session.execute(
                select(DailyStats).where(
                    DailyStats.account_id == account_id,
                    DailyStats.date == today,
                )
            )
            existing = result.scalar_one_or_none()
            prev_count = existing.trade_count if existing else 0
            prev_wins = existing.win_count if existing else 0
            prev_losses = existing.lose_count if existing else 0

        win = 1 if pnl > 0 else 0
        lose = 1 if pnl <= 0 else 0

        await storage.upsert_daily_stats(
            account_id,
            {
                "opening_balance": account.balance - account.total_pnl,
                "closing_balance": account.balance,
                "daily_pnl": pnl,
                "daily_pnl_pct": pnl / account.balance * 100 if account.balance > 0 else 0,
                "trade_count": prev_count + 1,
                "win_count": prev_wins + win,
                "lose_count": prev_losses + lose,
                "largest_win": max(existing.largest_win if existing and existing.largest_win > 0 else 0, pnl) if pnl > 0 else (existing.largest_win if existing else 0),
                "largest_loss": min(existing.largest_loss if existing and existing.largest_loss < 0 else 0, pnl) if pnl < 0 else (existing.largest_loss if existing else 0),
                "win_rate": (prev_wins + win) / (prev_count + 1) if (prev_count + 1) > 0 else 0.0,
            },
        )

    async def risk_check(
        self,
        account_id: str,
        margin_needed: float,
    ) -> tuple[bool, str]:
        """
        风控检查

        Returns:
            (通过, 错误信息)
        """
        account = await storage.get_account(account_id)
        if not account:
            return False, "账户不存在"

        available = account.balance - account.frozen_margin
        if margin_needed > available:
            return False, f"保证金不足：需 {margin_needed:.2f}，可用 {available:.2f}"

        return True, ""
