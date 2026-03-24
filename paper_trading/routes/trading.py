"""
交易相关路由
"""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from paper_trading.dependencies import get_service
from paper_trading.models import (
    OrderCreate, OrderResponse,
    PositionUpdate, PositionResponse,
)
from paper_trading.service import PaperTradingService
from paper_trading import storage

router = APIRouter(tags=["交易"])


def _serialize_engine_result(result: dict) -> dict:
    """将引擎返回结果中的 ORM 对象转换为可序列化字典"""
    for key in ("position", "order"):
        if key in result and hasattr(result[key], "__dict__"):
            obj = result[key]
            safe_fields = ("id", "symbol", "side", "quantity", "entry_price", "status")
            result[key] = {f: getattr(obj, f, None) for f in safe_fields}
    return result


async def _execute_open_order(
    service: PaperTradingService,
    req: OrderCreate,
) -> dict:
    """执行开仓订单"""
    if not req.price:
        raise HTTPException(status_code=400, detail="开仓价格不能为空")
    return await service.create_order_and_confirm(
        account_id=req.account_id,
        symbol=req.symbol,
        side=req.side,
        quantity=req.quantity,
        entry_price=req.price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        source=req.source or "manual",
        signal_id=req.signal_id,
        reason=req.reason,
    )


async def _execute_close_order(
    service: PaperTradingService,
    req: OrderCreate,
) -> dict:
    """执行平仓订单"""
    position = await storage.get_position(req.position_id)
    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")
    if position.quantity < req.quantity:
        raise HTTPException(status_code=400, detail="平仓数量超过持仓量")
    return await service.force_close_position(
        position_id=req.position_id,
        exit_price=req.price,
        quantity=req.quantity,
    )


# ==================== 持仓路由 ====================

@router.put("/api/positions/{position_id}", response_model=PositionResponse)
async def update_position(
    position_id: str,
    req: PositionUpdate,
    service: PaperTradingService = Depends(get_service),
):
    """更新持仓止损/止盈"""
    position = await service.update_position(
        position_id,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
    )
    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return position


@router.delete("/api/positions/{position_id}")
async def close_position(
    position_id: str,
    exit_price: float = Query(...),
    service: PaperTradingService = Depends(get_service),
):
    """平仓"""
    result = await service.force_close_position(position_id, exit_price)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "平仓失败"))
    return result


# ==================== 订单路由 ====================

@router.post("/api/orders", response_model=dict)
async def create_order(
    req: OrderCreate,
    service: PaperTradingService = Depends(get_service),
):
    """
    创建订单（开仓/平仓）

    如果是开仓（position_side 指定），走飞书确认流程
    如果是平仓（position_id 指定），直接执行
    """
    if req.position_id:
        result = await _execute_close_order(service, req)
    else:
        result = await _execute_open_order(service, req)

    return _serialize_engine_result(result)


@router.get("/api/orders/pending", response_model=list[OrderResponse])
async def list_pending_orders(
    service: PaperTradingService = Depends(get_service),
):
    """待确认订单列表"""
    return await service.get_pending_orders()


# ==================== 价格更新路由 ====================

class PriceUpdateRequest(BaseModel):
    """价格更新请求"""
    prices: dict[str, float]


@router.post("/api/prices/update")
async def update_prices(
    account_id: str,
    body: PriceUpdateRequest,
    service: PaperTradingService = Depends(get_service),
):
    """手动更新持仓价格（通常由定时任务调用）"""
    updated = await service.update_position_prices(account_id, body.prices)
    return {"updated": len(updated), "positions": updated}
