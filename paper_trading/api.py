"""
FastAPI 路由定义 + SSE 实时推送
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional, Any

from fastapi import Depends, FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from loguru import logger

from paper_trading.database import init_db, close_db
from paper_trading.config import PaperTradingConfig
from paper_trading.service import PaperTradingService
from paper_trading.feishu_integration import init_feishu_integration, get_feishu_integration
from paper_trading.models import (
    AccountCreate, AccountUpdate, AccountResponse,
    PositionUpdate, PositionResponse,
    OrderCreate, OrderResponse,
    SignalCreate, SignalResponse,
    AccountStatsResponse,
    FeishuConfirmRequest,
)
from paper_trading import storage
from paper_trading.analyzer import register_analyzer_routes
from paper_trading.settings_api import register_settings_routes


# ==================== 全局状态 ====================

# 模块级状态字典（供测试使用）
# 运行时状态使用 app.state（见 lifespan 函数）
app_state = {
    "running": False,
    "service": None,
}


def get_service(request: Any = None) -> Optional[PaperTradingService]:
    """获取服务实例（通过 app.state 或 app_state 兼容测试场景）"""
    if request is not None:
        return getattr(request.app.state, "service", None)
    # 兼容非 FastAPI 调用场景（如测试）
    return app_state.get("service")


def emit_event(event_type: str, data: dict):
    """向 SSE 队列推送事件"""
    try:
        queue = app_state.get("event_queue")
        if queue:
            queue.put_nowait({"event": event_type, "data": data})
    except Exception as e:
        logger.warning(f"Failed to emit event {event_type}: {e}")


# ==================== SSE 实时推送 ====================

async def sse_stream(request: Any):
    """SSE 事件流"""
    app = request.app
    while app.state.running:
        try:
            event = await asyncio.wait_for(
                app.state.event_queue.get(),
                timeout=30.0,
            )
            yield {
                "event": event["event"],
                "data": json.dumps(event["data"], default=str),
            }
        except asyncio.TimeoutError:
            yield {"event": "heartbeat", "data": json.dumps({"time": str(date.today())})}
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            break


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理（替代废弃的 @app.on_event）"""
    # 初始化状态
    app.state.service = PaperTradingService()
    app.state.event_queue = asyncio.Queue()
    app.state.running = True
    # 同步到模块级 app_state（兼容测试直接调用）
    app_state["service"] = app.state.service
    app_state["event_queue"] = app.state.event_queue
    app_state["running"] = True

    # 注册事件监听器
    app.state.service.engine.add_listener(
        lambda event_type, data: app.state.event_queue.put_nowait({
            "event": event_type,
            "data": data,
        })
    )

    # 初始化数据库
    await init_db()

    # 初始化飞书集成
    try:
        from config.settings import get_settings
        settings = get_settings()
        feishu_cfg = settings.notifications.feishu
        if feishu_cfg and feishu_cfg.webhook_url:
            init_feishu_integration(feishu_cfg.webhook_url)
            logger.info("飞书集成已初始化")
    except Exception as e:
        logger.warning(f"飞书集成初始化失败: {e}")

    logger.info("模拟交易 API 已启动")
    yield
    app.state.running = False
    app_state["running"] = False
    app_state["service"] = None
    await close_db()
    logger.info("模拟交易 API 已关闭")


app = FastAPI(
    title="Paper Trading API",
    description="模拟交易系统管理后台 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
_allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 注册分析路由
register_analyzer_routes(app)

# 注册设置路由
register_settings_routes(app)


# ==================== 健康检查端点 ====================

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "paper-trading-api",
        "version": "1.0.0"
    }


@app.get("/ready")
async def readiness_check():
    """就绪检查端点"""
    try:
        # 检查数据库连接
        from paper_trading.database import engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}


# ==================== SSE 端点 ====================

@app.get("/api/events/stream")
async def events_stream(request: Any):
    """SSE 实时推送端点"""
    return EventSourceResponse(sse_stream(request))


# ==================== 通用依赖 ====================

async def get_account_or_404(account_id: str) -> str:
    """账户存在性校验：仅校验存在，返回 account_id"""
    exists = await storage.get_account(account_id)
    if not exists:
        raise HTTPException(status_code=404, detail="账户不存在")
    return account_id


# ==================== 账户端点 ====================

@app.get("/api/accounts", response_model=list[AccountResponse])
async def list_accounts(service: PaperTradingService = Depends(get_service)):
    """账户列表"""
    return await service.list_accounts()


@app.post("/api/accounts", response_model=AccountResponse)
async def create_account(req: AccountCreate, service: PaperTradingService = Depends(get_service)):
    """创建模拟账户"""
    return await service.create_account(
        name=req.name,
        initial_balance=req.initial_balance,
        leverage=req.leverage,
    )


@app.get("/api/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str = Depends(get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户详情"""
    return await service.get_account(account_id)


@app.put("/api/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str = Depends(get_account_or_404),
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


@app.delete("/api/accounts/{account_id}")
async def delete_account(
    account_id: str = Depends(get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """删除账户"""
    ok = await service.delete_account(account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="账户不存在")
    return {"success": True}


# ==================== 持仓端点 ====================

@app.get("/api/accounts/{account_id}/positions", response_model=list[PositionResponse])
async def list_positions(
    account_id: str = Depends(get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户持仓列表"""
    return await service.get_positions(account_id)


@app.put("/api/positions/{position_id}", response_model=PositionResponse)
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


@app.delete("/api/positions/{position_id}")
async def close_position(
    position_id: str,
    exit_price: float = Query(...),
    background_tasks: BackgroundTasks = None,
    service: PaperTradingService = Depends(get_service),
):
    """平仓"""
    result = await service.force_close_position(position_id, exit_price)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "平仓失败"))
    return result


# ==================== 订单端点 ====================

@app.get("/api/accounts/{account_id}/orders")
async def list_orders(
    account_id: str = Depends(get_account_or_404),
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


@app.post("/api/orders", response_model=dict)
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


async def _execute_open_order(service: PaperTradingService, req: OrderCreate) -> dict:
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


async def _execute_close_order(service: PaperTradingService, req: OrderCreate) -> dict:
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


def _serialize_engine_result(result: dict) -> dict:
    """将引擎返回结果中的 ORM 对象转换为可序列化字典"""
    for key in ("position", "order"):
        if key in result and hasattr(result[key], "__dict__"):
            obj = result[key]
            safe_fields = ("id", "symbol", "side", "quantity", "entry_price", "status")
            result[key] = {f: getattr(obj, f, None) for f in safe_fields}
    return result


@app.get("/api/orders/pending", response_model=list[OrderResponse])
async def list_pending_orders(service: PaperTradingService = Depends(get_service)):
    """待确认订单列表"""
    return await service.get_pending_orders()


# ==================== 飞书回调端点 ====================

@app.post("/api/feishu/webhook")
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


@app.get("/api/feishu/signals", response_model=list[SignalResponse])
async def list_pending_signals(service: PaperTradingService = Depends(get_service)):
    """待确认信号列表"""
    return await service.list_pending_signals()


# ==================== 统计端点 ====================

@app.get("/api/accounts/{account_id}/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    account_id: str = Depends(get_account_or_404),
    service: PaperTradingService = Depends(get_service),
):
    """账户统计"""
    return await service.get_account_stats(account_id)


@app.get("/api/accounts/{account_id}/stats/daily")
async def get_daily_stats(
    account_id: str = Depends(get_account_or_404),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    service: PaperTradingService = Depends(get_service),
):
    """每日统计"""
    return await service.get_daily_stats(account_id, page, page_size)


@app.get("/api/accounts/{account_id}/equity-curve")
async def get_equity_curve(
    account_id: str = Depends(get_account_or_404),
    days: int = Query(90, ge=1, le=365),
    service: PaperTradingService = Depends(get_service),
):
    """权益曲线数据"""
    return await service.get_equity_curve(account_id, days)


# ==================== 信号端点 ====================

@app.post("/api/signals", response_model=SignalResponse)
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


# ==================== 价格更新 ====================

class PriceUpdateRequest(BaseModel):
    """价格更新请求"""
    prices: dict[str, float]


@app.post("/api/prices/update")
async def update_prices(
    account_id: str = Depends(get_account_or_404),
    body: PriceUpdateRequest = None,
    service: PaperTradingService = Depends(get_service),
):
    """
    手动更新持仓价格（通常由定时任务调用）
    示例: POST /api/prices/update?account_id=xxx  body: {"prices": {"BTCUSDT": 95000}}
    """
    updated = await service.update_position_prices(account_id, body.prices)
    return {"updated": len(updated), "positions": updated}
