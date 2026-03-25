#!/usr/bin/env python3
"""
CLI 入口点
"""
import argparse
import sys

from loguru import logger

from run.engine import create_engine
from config.settings import get_settings
from utils.logger import setup_logger


def main():
    parser = argparse.ArgumentParser(description="量化交易系统")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径 (支持JSON和YAML格式)"
    )
    parser.add_argument(
        "--mode",
        default="",
        choices=["auto", "monitor", "analyzer"],
        help="运行模式：auto 或 monitor 或 analyzer（留空从配置读取）"
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

    setup_logger(log_level=args.log_level)

    try:
        settings = get_settings(args.config)

        run_mode = args.mode if args.mode else settings.run_mode
        logger.info(f"运行模式: {run_mode}")

        engine = create_engine(args.config, run_mode=run_mode)

        if engine is None:
            logger.error("引擎创建失败")
            sys.exit(1)

        engine_type = type(engine).__name__
        logger.info(f"使用引擎: {engine_type}")

        if engine_type == 'MarketAnalyzerRunner':
            logger.info("运行模式: analyzer (市场分析)")
            if args.once:
                engine.run(send_notification=True)
            else:
                engine.run_loop(interval_seconds=args.interval)
        else:
            mode = args.mode if args.mode else 'monitor'
            logger.info(f"运行模式: {mode}")
            if args.once:
                engine.run_once()
            else:
                engine.run_continuously(interval=args.interval)

    except Exception as e:
        logger.error(f"致命错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
