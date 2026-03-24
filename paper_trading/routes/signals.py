"""
信号和飞书回调路由
"""
from fastapi import APIRouter, Depends, HTTPException

from paper_trading.dependencies import get_service
from paper_trading.models import SignalCreate, SignalResponse
from paper_trading.service import PaperTradingService
from paper_trading.feishu_integration import get_feishu_integration

router = APIRouter(tags=["信号"])


@router.post("/api/signals", response_model=SignalResponse)
async def create_signal(
    req: SignalCreate,
    service: PaperTradingService = Depends(get_service),
):
    """创建信号（来自 analyzer）"""
    signal_type = req.signal_type.value if hasattr(req.signal_type, "value") else req.signal_type
    return await service.create_signal(
        symbol=req.symbol,
        signal_type=signal_type,
        entry_price=req.entry_price,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit,
        reason=req.reason,
        timeframe=req.timeframe,
    )


# ==================== 飞书回调路由 ====================

feishu_router = APIRouter(prefix="/api/feishu", tags=["飞书"])


@feishu_router.post("/webhook")
async def feishu_webhook(
    body: dict,
    service: PaperTradingService = Depends(get_service),
):
    """飞书卡片按钮回调"""
    feishu = get_feishu_integration()
    if not feishu:
        raise HTTPException(status_code=500, detail="飞书集成未初始化")

    parsed = feishu.parse_callback(body)
    if not parsed:
        raise HTTPException(status_code=400, detail="无法解析飞书回调")

    return await service.confirm_order_from_feishu(
        signal_id=parsed["signal_id"],
        action=parsed["action"],
        account_id=parsed.get("account_id"),
    )


@feishu_router.get("/signals", response_model=list[SignalResponse])
async def list_pending_signals(
    service: PaperTradingService = Depends(get_service),
):
    """待确认信号列表"""
    return await service.list_pending_signals()
