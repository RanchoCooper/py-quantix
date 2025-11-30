import os
import sys

from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: str = "logs/trading.log"):
    """
    设置具有指定配置的日志记录器

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径
    """
    # 移除默认日志记录器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )

    # 如果日志目录不存在则创建
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # 添加文件处理器
    logger.add(
        log_file,
        rotation="10 MB",
        retention="30 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}"
    )

    logger.info(f"日志记录器已初始化，级别 {log_level}")
    return logger


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    全局异常处理程序
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
    if exc_traceback:
        logger.critical(f"追踪信息: {exc_traceback}")


# 设置全局异常处理程序
sys.excepthook = handle_exception
