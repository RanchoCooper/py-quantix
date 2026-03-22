#!/usr/bin/env python3
"""
模拟交易管理后台启动脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from paper_trading.database import init_db

def main():
    import asyncio

    async def setup():
        await init_db()
        print("数据库初始化完成")

    asyncio.run(setup())

    print("\n启动模拟交易管理后台...")
    print("API 文档: http://localhost:8000/docs")
    print("前端界面: http://localhost:5173 (需先启动前端)")
    print()

    uvicorn.run(
        "paper_trading.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

if __name__ == "__main__":
    main()
