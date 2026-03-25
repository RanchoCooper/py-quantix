"""
测试配置和 fixtures
每个测试使用独立的临时 SQLite 数据库
"""
import asyncio
import os
import sys
import tempfile
from typing import AsyncGenerator

import pytest
import pytest_asyncio

# 项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """会话级事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def fresh_db():
    """
    每个测试函数使用独立的临时数据库
    关键：需要 patch database 模块的全局引擎和会话工厂
    """
    import paper_trading.database as db_module
    import paper_trading.storage as storage_module
    import paper_trading.api as api_module

    # 创建临时数据库
    db_path = tempfile.mktemp(suffix=".db")
    url = f"sqlite+aiosqlite:///{db_path}"

    # 保存原始值
    old_engine = db_module._engine
    old_factory = db_module._session_factory
    old_url = db_module.DATABASE_URL

    # 替换为测试数据库
    db_module._engine = None
    db_module._session_factory = None
    db_module.DATABASE_URL = url

    # 创建新引擎
    from sqlalchemy.ext.asyncio import create_async_engine
    test_engine = create_async_engine(url, echo=False)

    # 初始化表
    async with test_engine.begin() as conn:
        await conn.run_sync(db_module.Base.metadata.create_all)

    # 设置全局引擎
    db_module._engine = test_engine
    db_module._session_factory = None  # 强制重新创建

    # 重置 app.state（运行时状态）
    if hasattr(api_module.app, "state"):
        api_module.app.state.running = True
        api_module.app.state.service = None

    yield db_path

    # 清理
    await test_engine.dispose()
    db_module._engine = old_engine
    db_module._session_factory = old_factory
    db_module.DATABASE_URL = old_url

    # 尝试删除临时文件
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest_asyncio.fixture(scope="function")
async def service(fresh_db):
    """提供 PaperTradingService 实例，使用隔离数据库"""
    from paper_trading.service import PaperTradingService
    from paper_trading.config import PaperTradingConfig

    config = PaperTradingConfig(confirm_via_feishu=False)
    svc = PaperTradingService(config)
    return svc


@pytest_asyncio.fixture(scope="function")
async def api_client(fresh_db):
    """提供 FastAPI TestClient，使用隔离数据库"""
    from paper_trading.api import app
    from fastapi.testclient import TestClient

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def sample_account(service):
    """创建示例账户"""
    account = await service.create_account(
        name="Sample Account",
        initial_balance=10000.0,
        leverage=10,
    )
    return account
