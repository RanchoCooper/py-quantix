"""
FastAPI 依赖注入
供 api.py 和 routes 模块共用
"""
from starlette.requests import Request
from fastapi import HTTPException, status

from paper_trading.service import PaperTradingService


def get_service(request: Request) -> PaperTradingService:
    """获取服务实例（通过 FastAPI Request），未初始化时返回 503"""
    service = getattr(request.app.state, "service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized",
        )
    return service
