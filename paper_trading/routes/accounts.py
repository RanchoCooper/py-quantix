"""
账户相关路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from paper_trading.dependencies import get_service
from paper_trading.models import (
    AccountCreate, AccountUpdate, AccountResponse,
    PositionResponse, OrderResponse,
    AccountStatsResponse, DailyStatsResponse, PaginatedResponse,
    EquityCurvePoint,
)
from paper_trading.service import PaperTradingService
from paper_trading import storage

router = APIRouter(prefix="/api/accounts", tags=["账户"])


async def _get_account_or_404(account_id: str) -> str:
    """账户存在性校验"""
    exists = await storage.get_account(account_id)
    if not exists:
        raise HTTPException(status_code=404, detail="账户不存在")
    return account_id


@router.get("", response_model=list[AccountResponse])
async def list_accounts(service: PaperTradingService = Depends(get_service)):
    """账户列表"""
    return await service.list_accounts()


@router.post("", response_model=AccountResponse)
async def create_account(
    req: AccountCreate,
    service: PaperTradingService = Depends(get_service),
):
    """创建模拟账户"""
    return await service.create_account(
        name=req.name,
        initial_balance=req.initial_balance,
        leverage=req.leverage,
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str = Depends(_get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户详情"""
    return await service.get_account(account_id)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str = Depends(_get_account_or_404),
    req: AccountUpdate = None,
    service: PaperTradingService = Depends(get_service),
):
    """更新账户"""
    account = await service.update_account(
        account_id,
        name=req.name,
        leverage=req.leverage,
    )
    if not account:
        raise HTTPException(status_code=404, detail="账户不存在")
    return account


@router.delete("/{account_id}")
async def delete_account(
    account_id: str = Depends(_get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """删除账户"""
    ok = await service.delete_account(account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="账户不存在")
    return {"success": True}


@router.get("/{account_id}/positions", response_model=list[PositionResponse])
async def list_positions(
    account_id: str = Depends(_get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户持仓列表"""
    return await service.get_positions(account_id)


@router.get("/{account_id}/orders")
async def list_orders(
    account_id: str = Depends(_get_account_or_404),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    symbol: Optional[str] = None,
    side: Optional[str] = None,
    status: Optional[str] = None,
    service: PaperTradingService = Depends(get_service),
):
    """订单历史（分页）"""
    return await service.list_orders(
        account_id, page, page_size, symbol, side, status
    )


@router.get("/{account_id}/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    account_id: str = Depends(_get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户统计"""
    return await service.get_account_stats(account_id)


@router.get("/{account_id}/stats/daily")
async def get_daily_stats(
    account_id: str = Depends(_get_account_or_404),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    service: PaperTradingService = Depends(get_service),
):
    """每日统计"""
    return await service.get_daily_stats(account_id, page, page_size)


@router.get("/{account_id}/equity-curve")
async def get_equity_curve(
    account_id: str = Depends(_get_account_or_404),
    days: int = Query(90, ge=1, le=365),
    service: PaperTradingService = Depends(get_service),
):
    """权益曲线数据"""
    return await service.get_equity_curve(account_id, days)
