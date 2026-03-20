#!/usr/bin/env python3
"""
主程序入口，初始化交易引擎并启动交易循环

支持多种运行模式：
- monitor: 监控模式，只发送信号通知，不执行实际交易
- auto: 自动模式，自动执行交易信号
- backtest: 回测模式，使用历史数据测试策略表现

配置选项：
- 支持多币种交易配置
- 支持多种交易策略选择
- 支持钉钉通知或命令行打印两种信号输出方式
- 支持灵活的风险管理设置（杠杆、仓位等）
"""

import argparse
import sys

from loguru import logger

from core.engine import create_engine
from utils.config_manager import ConfigManager
from utils.logger import setup_logger


def main():
    """
    主函数
    """
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

    # 设置日志
    setup_logger(log_level=args.log_level)

    try:
        # 验证配置
        config = ConfigManager.load_config(args.config)

        if not ConfigManager.validate_config(config):
            logger.error("配置验证失败")
            sys.exit(1)

        # 优先使用命令行参数，否则从配置读取
        run_mode = args.mode if args.mode else config.get('run_mode', 'monitor')
        logger.info(f"运行模式: {run_mode}")

        # 创建引擎（传递 run_mode 以便正确创建）
        engine = create_engine(args.config, run_mode=run_mode)

        if engine is None:
            logger.error("引擎创建失败")
            sys.exit(1)

        # 根据引擎类型运行
        engine_type = type(engine).__name__
        logger.info(f"使用引擎: {engine_type}")

        if engine_type == 'MarketAnalyzerRunner':
            # 分析器模式
            logger.info("运行模式: analyzer (市场分析)")
            if args.once:
                engine.run(send_notification=True)
            else:
                engine.run_loop(interval_seconds=args.interval)
        else:
            # 交易引擎模式 (monitor/auto)
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
