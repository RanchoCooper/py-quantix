#!/usr/bin/env python3
"""
量化交易系统主入口点
"""

import argparse
import sys

from loguru import logger

from core.engine import TradingEngine
from utils.config_manager import ConfigManager
from utils.logger import setup_logger


def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="量化交易系统")
    parser.add_argument(
        "--config",
        default="config/config.json",
        help="配置文件路径"
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "monitor"],
        help="运行模式：auto（自动交易）或 monitor（监控模式）"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="运行一次策略评估后退出"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=3600,
        help="评估间隔秒数（默认：3600）"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认：INFO）"
    )

    args = parser.parse_args()

    # 设置日志
    setup_logger(log_level=args.log_level)

    try:
        # 验证配置
        config = ConfigManager.load_config(args.config)
        if not ConfigManager.validate_config(config):
            logger.error("配置验证失败")
            sys.exit(1)

        # 初始化交易引擎，传递运行模式参数
        engine = TradingEngine(args.config, mode=args.mode)

        # 运行交易引擎
        if args.once:
            logger.info(f"运行一次策略评估，模式: {args.mode}")
            engine.run_once()
        else:
            logger.info(f"启动持续交易循环，间隔{args.interval}秒，模式: {args.mode}")
            engine.run_continuously(interval=args.interval)

    except Exception as e:
        logger.error(f"致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
