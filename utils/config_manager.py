import json
import os
from typing import Any, Dict

import yaml
from loguru import logger

from utils.symbol_parser import parse_symbol_config, get_symbol_list


class ConfigManager:
    """
    配置管理器，用于加载、验证和管理交易系统的配置
    支持YAML和JSON格式的配置文件，支持环境变量覆盖
    """

    # 支持的策略列表
    SUPPORTED_STRATEGIES = ['trend_following', 'mean_reversion', 'turtle_trading']
    # 支持的运行模式
    SUPPORTED_RUN_MODES = ['monitor', 'analyzer']

    @staticmethod
    def load_config(config_path: str, use_env: bool = True) -> Dict[str, Any]:
        """
        从文件加载配置，支持YAML和JSON格式

        Args:
            config_path (str): 配置文件路径

        Returns:
            Dict[str, Any]: 配置字典

        Raises:
            FileNotFoundError: 当配置文件不存在时抛出
            yaml.YAMLError: 当YAML配置文件格式不正确时抛出
            json.JSONDecodeError: 当JSON配置文件格式不正确时抛出

        Example:
            >>> config = ConfigManager.load_config("config/config.yaml")
            >>> print(config['binance']['api_key'])
            your_api_key
        """
        try:
            with open(config_path, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                    logger.info(f"YAML配置已从 {config_path} 加载")
                else:
                    config = json.load(f)
                    logger.info(f"JSON配置已从 {config_path} 加载")
            return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        验证配置的有效性

        Args:
            config (Dict[str, Any]): 配置字典

        Returns:
            bool: 配置是否有效

        Validation Checks:
            - 必需字段存在性检查
            - 币安API密钥格式验证
            - 交易对配置验证
            - 策略配置验证
            - 通知配置验证

        Example:
            >>> is_valid = ConfigManager.validate_config(config)
            >>> if is_valid:
            ...     logger.info("配置验证通过")
        """
        try:
            # 检查运行模式
            run_mode = config.get('run_mode', 'monitor')
            if run_mode not in ConfigManager.SUPPORTED_RUN_MODES:
                logger.error(f"无效的运行模式: {run_mode}，支持的模式: {ConfigManager.SUPPORTED_RUN_MODES}")
                return False
            logger.info(f"运行模式: {run_mode}")

            # 检查必需的顶级字段（analyzer 模式只需要 notifications）
            if run_mode == 'monitor':
                required_fields = ['binance', 'trading', 'strategies', 'notifications']
            else:  # analyzer 模式
                required_fields = ['notifications', 'llm', 'market_data']

            for field in required_fields:
                if field not in config:
                    logger.error(f"缺少必需的配置字段: {field}")
                    return False

            # 验证币安配置
            binance_config = config['binance']
            if not isinstance(binance_config.get('api_key'), str) or len(binance_config['api_key']) == 0:
                logger.error("无效的币安API密钥")
                return False
            if not isinstance(binance_config.get('api_secret'), str) or len(binance_config['api_secret']) == 0:
                logger.error("无效的币安API密钥")
                return False
            if 'testnet' not in binance_config:
                logger.warning("未设置testnet字段，默认为True")
                config['binance']['testnet'] = True

            # 验证交易配置
            trading_config = config['trading']
            if 'symbols' not in trading_config:
                logger.error("无效的交易配置: 缺少 symbols 字段")
                return False

            # 使用统一的符号配置解析函数
            symbols = trading_config['symbols']
            symbol_list = parse_symbol_config(symbols)

            if not symbol_list:
                logger.error("无效的交易配置: symbols 解析失败")
                return False

            # 验证每个交易对配置
            for symbol_config in symbol_list:
                symbol = symbol_config.get('symbol', 'UNKNOWN')
                if not isinstance(symbol_config, dict):
                    logger.error(f"交易对 {symbol} 的配置无效")
                    return False

                # 验证杠杆
                if 'leverage' not in symbol_config or not isinstance(symbol_config['leverage'], int):
                    logger.error(f"交易对 {symbol} 缺少有效的杠杆配置")
                    return False

                # 验证头寸大小
                if 'position_size' not in symbol_config or not isinstance(symbol_config['position_size'], (int, float)):
                    logger.error(f"交易对 {symbol} 缺少有效的头寸大小配置")
                    return False

                # 验证策略
                if 'strategy' not in symbol_config or not isinstance(symbol_config['strategy'], str):
                    logger.error(f"交易对 {symbol} 缺少有效的策略配置")
                    return False

                # 验证策略是否受支持
                if symbol_config['strategy'] not in ConfigManager.SUPPORTED_STRATEGIES:
                    logger.error(f"交易对 {symbol} 使用了不支持的策略: {symbol_config['strategy']}")
                    return False

                # 验证策略参数（如果存在）
                if 'strategy_params' in symbol_config and not isinstance(symbol_config['strategy_params'], dict):
                    logger.error(f"交易对 {symbol} 的策略参数配置无效")
                    return False

            # 验证策略配置
            strategies_config = config['strategies']
            if not isinstance(strategies_config, dict):
                logger.error("无效的策略配置")
                return False

            # 验证通知配置
            notifications_config = config['notifications']
            if not isinstance(notifications_config, dict):
                logger.error("无效的通知配置")
                return False

            logger.info("配置验证通过")
            return True

        except Exception as e:
            logger.error(f"配置验证过程中出现错误: {e}")
            return False

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """
        保存配置到文件，支持YAML和JSON格式

        Args:
            config (Dict[str, Any]): 配置字典
            config_path (str): 配置文件路径

        Raises:
            yaml.YAMLError: 当YAML配置文件格式不正确时抛出
            json.JSONDecodeError: 当JSON配置文件格式不正确时抛出

        Example:
            >>> ConfigManager.save_config(config, "config/config.yaml")
            >>> logger.info("配置已保存到 config/config.yaml")
        """
        try:
            # 如果目录不存在则创建
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
                    logger.info(f"YAML配置已保存到 {config_path}")
                else:
                    json.dump(config, f, indent=4)
                    logger.info(f"JSON配置已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
