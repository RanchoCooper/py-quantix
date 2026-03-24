"""
健康检查路由
"""
from fastapi import APIRouter
from sqlalchemy import text

from paper_trading.database import get_engine

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "paper-trading-api",
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """就绪检查端点"""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not_ready", "database": "disconnected", "error": str(e)}
