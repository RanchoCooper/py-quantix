"""
FastAPI 应用入口
路由定义委托给 paper_trading.routes 模块
"""
import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, Optional

from starlette.requests import Request

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from paper_trading.database import init_db, close_db
from paper_trading.service import PaperTradingService
from paper_trading.feishu_integration import init_feishu_integration, get_feishu_integration
from paper_trading.events import EventBus
from paper_trading import routes
from paper_trading.dependencies import get_service
from loguru import logger


# ==================== 生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理"""
    app.state.service = PaperTradingService()
    app.state.event_queue = asyncio.Queue()
    app.state.event_bus = EventBus()
    app.state.running = True

    # 注册引擎事件监听器 → SSE 队列
    app.state.service.engine.add_listener(
        lambda event_type, data: app.state.event_queue.put_nowait({
            "event": event_type,
            "data": data,
        })
    )

    await init_db()

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
    await close_db()
    logger.info("模拟交易 API 已关闭")


# ==================== 应用实例 ====================

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

# 注册路由
app.include_router(routes.health.router)
app.include_router(routes.events.router)
app.include_router(routes.accounts.router)
app.include_router(routes.trading.router)
app.include_router(routes.signals.router)
app.include_router(routes.signals.feishu_router)

# 注册 analyzer 和 settings 路由
from paper_trading.analyzer import register_analyzer_routes
from paper_trading.settings_api import register_settings_routes

register_analyzer_routes(app)
register_settings_routes(app)
