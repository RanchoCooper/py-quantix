"""
业务逻辑层
编排存储层、引擎层和飞书集成
"""
from typing import Optional, List, Dict, Any

from loguru import logger

from paper_trading import storage
from paper_trading.config import PaperTradingConfig
from paper_trading.engine import PaperTradingEngine
from paper_trading.feishu_integration import get_feishu_integration
from paper_trading.models import (
    AccountResponse, PositionResponse, OrderResponse,
    SignalResponse, DailyStatsResponse, AccountStatsResponse,
    EquityCurvePoint, PaginatedResponse,
)


class PaperTradingService:
    """
    模拟交易服务层

    统一入口，负责协调 storage、engine 和 feishu_integration
    """

    def __init__(self, config: Optional[PaperTradingConfig] = None):
        self.config = config or PaperTradingConfig()
        self.engine = PaperTradingEngine(self.config)

    # ==================== 账户 ====================

    async def create_account(
        self,
        name: str,
        initial_balance: float,
        leverage: int = 10,
    ) -> AccountResponse:
        account = await storage.create_account(
            name=name,
            initial_balance=initial_balance,
            leverage=leverage,
        )
        return self._account_to_response(account)

    async def get_account(self, account_id: str) -> Optional[AccountResponse]:
        account = await storage.get_account(account_id)
        if not account:
            return None
        return self._account_to_response(account)

    async def list_accounts(self) -> List[AccountResponse]:
        accounts = await storage.get_all_accounts()
        return [self._account_to_response(a) for a in accounts]

    async def update_account(
        self,
        account_id: str,
        name: Optional[str] = None,
        leverage: Optional[int] = None,
    ) -> Optional[AccountResponse]:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if leverage is not None:
            kwargs["leverage"] = leverage
        if not kwargs:
            return await self.get_account(account_id)
        account = await storage.update_account(account_id, **kwargs)
        if not account:
            return None
        return self._account_to_response(account)

    async def delete_account(self, account_id: str) -> bool:
        return await storage.delete_account(account_id)

    # ==================== 持仓 ====================

    async def get_positions(self, account_id: str) -> List[PositionResponse]:
        positions = await storage.get_positions_by_account(account_id)
        return [self._position_to_response(p) for p in positions]

    async def update_position(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[PositionResponse]:
        kwargs = {}
        if stop_loss is not None:
            kwargs["stop_loss"] = stop_loss
        if take_profit is not None:
            kwargs["take_profit"] = take_profit
        position = await storage.update_position(position_id, **kwargs)
        if not position:
            return None
        return self._position_to_response(position)

    async def force_close_position(
        self,
        position_id: str,
        exit_price: float,
        quantity: Optional[float] = None,
    ) -> Dict[str, Any]:
        return await self.engine.close_position(
            position_id=position_id,
            exit_price=exit_price,
            quantity=quantity,
        )

    async def update_position_prices(
        self,
        account_id: str,
        prices: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        return await self.engine.update_position_prices(account_id, prices)

    # ==================== 订单 ====================

    async def create_order_and_confirm(
        self,
        account_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        source: str = "manual",
        signal_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        创建订单并确认执行（核心下单流程）

        每次下单都走飞书确认流程：
        1. 创建信号（pending）
        2. 发送飞书确认卡片
        3. 用户在飞书回复确认/取消
        4. 回调执行实际开仓
        """
        # 如果不需要飞书确认，直接执行
        if not self.config.confirm_via_feishu:
            return await self.engine.open_position(
                account_id=account_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_id=signal_id,
            )

        # 创建信号记录
        signal = await storage.create_signal(
            symbol=symbol,
            signal_type=side,
            reason=reason,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )

        # 发送飞书确认
        feishu = get_feishu_integration()
        if feishu:
            await feishu.send_order_confirmation(
                signal_id=signal.id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reason=reason,
            )
            logger.info(f"订单确认请求已发送到飞书: signal_id={signal.id}")
        else:
            logger.warning("飞书集成未初始化，跳过确认直接开仓")
            # 没有飞书集成时，直接确认
            await storage.update_signal(signal.id, status="confirmed")
            return await self.engine.open_position(
                account_id=account_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                signal_id=signal.id,
            )

        return {
            "success": True,
            "pending": True,
            "signal_id": signal.id,
            "message": "订单确认请求已发送到飞书，请等待确认",
        }

    async def confirm_order_from_feishu(
        self,
        signal_id: str,
        action: str,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """处理飞书回调，执行或取消订单"""
        feishu = get_feishu_integration()
        if feishu:
            result = await feishu.process_confirmation(signal_id, action, account_id)
        else:
            return {"success": False, "error": "飞书集成未初始化"}

        if not result["success"]:
            # 信号状态异常时仍应更新信号状态
            if signal.status.value == "pending":
                await storage.update_signal(signal_id, status="rejected")
            return result

        if result["action"] == "confirmed":
            signal = result["signal"]
            # 执行开仓
            exec_result = await self.engine.open_position(
                account_id=account_id or signal.account_id,
                symbol=signal.symbol,
                side=signal.signal_type,
                quantity=signal.quantity if hasattr(signal, "quantity") else 0.01,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                signal_id=signal.id,
            )
            return exec_result

        return result

    async def list_orders(
        self,
        account_id: str,
        page: int = 1,
        page_size: int = 20,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PaginatedResponse:
        orders, total = await storage.get_orders_by_account(
            account_id, page, page_size, symbol, side, status
        )
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return PaginatedResponse(
            items=[self._order_to_response(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_pending_orders(self) -> List[OrderResponse]:
        orders = await storage.get_pending_orders()
        return [self._order_to_response(o) for o in orders]

    # ==================== 统计 ====================

    async def get_account_stats(self, account_id: str) -> AccountStatsResponse:
        positions = await storage.get_positions_by_account(account_id)
        open_pnl = sum(p.unrealized_pnl for p in positions)

        stats = await storage.get_account_trade_stats(account_id)

        return AccountStatsResponse(
            total_trades=stats["total_trades"],
            winning_trades=stats["winning_trades"],
            losing_trades=stats["losing_trades"],
            win_rate=stats["win_rate"],
            total_pnl=stats["total_pnl"],
            total_pnl_pct=stats.get("total_pnl_pct", 0.0),
            avg_win=stats["avg_win"],
            avg_loss=stats["avg_loss"],
            profit_factor=stats["profit_factor"],
            largest_win=stats["largest_win"],
            largest_loss=stats["largest_loss"],
            current_positions=len(positions),
            open_position_pnl=open_pnl,
        )

    async def get_daily_stats(
        self,
        account_id: str,
        page: int = 1,
        page_size: int = 30,
    ) -> PaginatedResponse:
        stats, total = await storage.get_daily_stats(account_id, page, page_size)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        return PaginatedResponse(
            items=[self._daily_stats_to_response(s) for s in stats],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_equity_curve(
        self,
        account_id: str,
        days: int = 90,
    ) -> List[EquityCurvePoint]:
        curve = await storage.get_equity_curve(account_id, days)
        return [EquityCurvePoint(**point) for point in curve]

    # ==================== 信号 ====================

    async def create_signal(
        self,
        symbol: str,
        signal_type: str,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reason: Optional[str] = None,
        timeframe: Optional[str] = None,
    ) -> SignalResponse:
        signal = await storage.create_signal(
            symbol=symbol,
            signal_type=signal_type,
            timeframe=timeframe,
            reason=reason,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        return self._signal_to_response(signal)

    async def list_pending_signals(self) -> List[SignalResponse]:
        signals = await storage.get_pending_signals()
        return [self._signal_to_response(s) for s in signals]

    # ==================== 响应转换 ====================

    def _account_to_response(self, account) -> AccountResponse:
        available = account.balance - account.frozen_margin
        total_pnl = account.balance - account.initial_balance
        total_pnl_pct = (total_pnl / account.initial_balance * 100) if account.initial_balance > 0 else 0
        return AccountResponse(
            id=account.id,
            name=account.name,
            initial_balance=account.initial_balance,
            balance=account.balance,
            frozen_margin=account.frozen_margin,
            available_balance=available,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            leverage=account.leverage,
            created_at=account.created_at,
            updated_at=account.updated_at,
        )

    def _position_to_response(self, position) -> PositionResponse:
        return PositionResponse.model_validate(position)

    def _order_to_response(self, order) -> OrderResponse:
        return OrderResponse.model_validate(order)

    def _signal_to_response(self, signal) -> SignalResponse:
        return SignalResponse.model_validate(signal)

    def _daily_stats_to_response(self, stats) -> DailyStatsResponse:
        return DailyStatsResponse.model_validate(stats)
