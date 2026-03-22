"""
数据访问层 (Repository Pattern)
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from paper_trading.database import get_session
from paper_trading.models import (
    PaperAccount, Position, Order, Signal, DailyStats,
    OrderStatus, SignalStatus
)


def new_id() -> str:
    return str(uuid.uuid4())


async def _update_by_id(
    model: type,
    id_: str,
    **kwargs: Any,
) -> Optional[Any]:
    """通用单条记录更新：查询 -> 设置字段 -> 提交 -> 返回"""
    async with get_session() as session:
        result = await session.execute(select(model).where(model.id == id_))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key) and value is not None:
                setattr(obj, key, value)
        if hasattr(obj, "updated_at"):
            obj.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(obj)
        return obj


# ==================== Account CRUD ====================

async def create_account(
    name: str,
    initial_balance: float,
    leverage: int = 10,
) -> PaperAccount:
    async with get_session() as session:
        account = PaperAccount(
            id=new_id(),
            name=name,
            initial_balance=initial_balance,
            balance=initial_balance,
            frozen_margin=0.0,
            total_pnl=0.0,
            leverage=leverage,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account


async def get_account(account_id: str) -> Optional[PaperAccount]:
    async with get_session() as session:
        result = await session.execute(
            select(PaperAccount).where(PaperAccount.id == account_id)
        )
        return result.scalar_one_or_none()


async def get_all_accounts() -> List[PaperAccount]:
    async with get_session() as session:
        result = await session.execute(select(PaperAccount).order_by(PaperAccount.created_at.desc()))
        return list(result.scalars().all())


async def update_account(account_id: str, **kwargs) -> Optional[PaperAccount]:
    return await _update_by_id(PaperAccount, account_id, **kwargs)


async def delete_account(account_id: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(PaperAccount).where(PaperAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            return False
        await session.delete(account)
        await session.commit()
        return True


# ==================== Position CRUD ====================

async def create_position(
    account_id: str,
    symbol: str,
    side: str,
    quantity: float,
    entry_price: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Position:
    async with get_session() as session:
        position = Position(
            id=new_id(),
            account_id=account_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            unrealized_pnl=0.0,
            unrealized_pnl_pct=0.0,
        )
        session.add(position)
        await session.commit()
        await session.refresh(position)
        return position


async def get_position(position_id: str) -> Optional[Position]:
    async with get_session() as session:
        result = await session.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()


async def get_positions_by_account(account_id: str) -> List[Position]:
    async with get_session() as session:
        result = await session.execute(
            select(Position)
            .where(Position.account_id == account_id)
            .order_by(Position.opened_at.desc())
        )
        return list(result.scalars().all())


async def update_position(position_id: str, **kwargs) -> Optional[Position]:
    return await _update_by_id(Position, position_id, **kwargs)


async def delete_position(position_id: str) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(Position).where(Position.id == position_id)
        )
        position = result.scalar_one_or_none()
        if not position:
            return False
        await session.delete(position)
        await session.commit()
        return True


# ==================== Order CRUD ====================

async def create_order(
    account_id: str,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    position_side: Optional[str] = None,
    price: Optional[float] = None,
    position_id: Optional[str] = None,
    signal_id: Optional[str] = None,
    source: str = "manual",
    reason: Optional[str] = None,
) -> Order:
    async with get_session() as session:
        order = Order(
            id=new_id(),
            account_id=account_id,
            symbol=symbol,
            side=side,
            position_side=position_side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status="pending",
            position_id=position_id,
            signal_id=signal_id,
            source=source,
            reason=reason,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


async def get_order(order_id: str) -> Optional[Order]:
    async with get_session() as session:
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()


async def get_orders_by_account(
    account_id: str,
    page: int = 1,
    page_size: int = 20,
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[List[Order], int]:
    async with get_session() as session:
        query = select(Order).where(Order.account_id == account_id)
        count_query = select(func.count()).select_from(Order).where(Order.account_id == account_id)

        if symbol:
            query = query.where(Order.symbol == symbol)
            count_query = count_query.where(Order.symbol == symbol)
        if side:
            query = query.where(Order.side == side)
            count_query = count_query.where(Order.side == side)
        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)

        total = (await session.execute(count_query)).scalar()

        query = query.order_by(Order.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(query)
        return list(result.scalars().all()), total


async def update_order(order_id: str, **kwargs) -> Optional[Order]:
    return await _update_by_id(Order, order_id, **kwargs)


async def get_pending_orders() -> List[Order]:
    async with get_session() as session:
        result = await session.execute(
            select(Order)
            .where(Order.status == "pending")
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())


# ==================== Signal CRUD ====================

async def create_signal(
    symbol: str,
    signal_type: str,
    timeframe: Optional[str] = None,
    reason: Optional[str] = None,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Signal:
    async with get_session() as session:
        signal = Signal(
            id=new_id(),
            symbol=symbol,
            timeframe=timeframe,
            signal_type=signal_type,
            reason=reason,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="pending",
        )
        session.add(signal)
        await session.commit()
        await session.refresh(signal)
        return signal


async def get_signal(signal_id: str) -> Optional[Signal]:
    async with get_session() as session:
        result = await session.execute(
            select(Signal).where(Signal.id == signal_id)
        )
        return result.scalar_one_or_none()


async def update_signal(signal_id: str, **kwargs) -> Optional[Signal]:
    return await _update_by_id(Signal, signal_id, **kwargs)


async def get_pending_signals() -> List[Signal]:
    async with get_session() as session:
        result = await session.execute(
            select(Signal)
            .where(Signal.status == "pending")
            .order_by(Signal.created_at.desc())
        )
        return list(result.scalars().all())


# ==================== DailyStats CRUD ====================

async def upsert_daily_stats(
    account_id: str,
    stats: dict,
) -> DailyStats:
    today = date.today().isoformat()
    async with get_session() as session:
        result = await session.execute(
            select(DailyStats).where(
                and_(
                    DailyStats.account_id == account_id,
                    DailyStats.date == today
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in stats.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            await session.commit()
            await session.refresh(existing)
            return existing
        else:
            daily = DailyStats(
                id=new_id(),
                account_id=account_id,
                date=today,
                **stats,
            )
            session.add(daily)
            await session.commit()
            await session.refresh(daily)
            return daily


async def get_daily_stats(
    account_id: str,
    page: int = 1,
    page_size: int = 30,
) -> tuple[List[DailyStats], int]:
    async with get_session() as session:
        count_q = select(func.count()).select_from(DailyStats).where(
            DailyStats.account_id == account_id
        )
        total = (await session.execute(count_q)).scalar()

        q = (
            select(DailyStats)
            .where(DailyStats.account_id == account_id)
            .order_by(DailyStats.date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await session.execute(q)
        return list(result.scalars().all()), total


async def get_equity_curve(account_id: str, days: int = 90) -> List[dict]:
    async with get_session() as session:
        q = (
            select(DailyStats)
            .where(DailyStats.account_id == account_id)
            .order_by(DailyStats.date.asc())
            .limit(days)
        )
        result = await session.execute(q)
        stats = result.scalars().all()
        return [
            {
                "date": s.date,
                "balance": s.closing_balance,
                "daily_pnl": s.daily_pnl,
            }
            for s in stats
        ]


# ==================== Statistics ====================

async def get_account_trade_stats(account_id: str) -> dict:
    async with get_session() as session:
        result = await session.execute(
            select(Order).where(
                and_(
                    Order.account_id == account_id,
                    Order.status == "filled",
                    Order.pnl.isnot(None),
                )
            )
        )
        orders = list(result.scalars().all())

        if not orders:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
            }

        winning = [o for o in orders if o.pnl > 0]
        losing = [o for o in orders if o.pnl <= 0]

        total_pnl = sum(o.pnl for o in orders)
        total_wins = sum(o.pnl for o in winning)
        total_losses = abs(sum(o.pnl for o in losing)) if losing else 0

        return {
            "total_trades": len(orders),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": len(winning) / len(orders) if orders else 0.0,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl / orders[0].price * 100 if orders and orders[0].price else 0.0,
            "avg_win": total_wins / len(winning) if winning else 0.0,
            "avg_loss": total_losses / len(losing) if losing else 0.0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else 0.0,
            "largest_win": max((o.pnl for o in winning), default=0.0),
            "largest_loss": min((o.pnl for o in losing), default=0.0),
        }
