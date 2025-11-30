import json
import os
from typing import Any, Dict

from loguru import logger


class ConfigManager:
    """
    配置管理器，用于处理配置文件
    """

    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        从JSON文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"配置已从 {config_path} 加载")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"配置文件中的JSON无效: {e}")
            raise
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            raise

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """
        保存配置到JSON文件

        Args:
            config: 配置字典
            config_path: 配置文件路径
        """
        try:
            # 如果目录不存在则创建
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"配置已保存到 {config_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """
        验证配置结构

        Args:
            config: 配置字典

        Returns:
            表示有效性的布尔值
        """
        required_sections = ['binance', 'trading', 'strategies', 'notifications']

        for section in required_sections:
            if section not in config:
                logger.error(f"配置中缺少必需的部分: {section}")
                return False

        # 验证binance部分
        binance_required = ['api_key', 'api_secret']
        for field in binance_required:
            if field not in config['binance']:
                logger.error(f"binance配置中缺少必需字段: {field}")
                return False

        # 验证trading部分
        trading_required = ['symbol', 'leverage', 'position_size', 'strategy']
        for field in trading_required:
            if field not in config['trading']:
                logger.error(f"trading配置中缺少必需字段: {field}")
                return False

        # 验证选择的策略存在
        strategy = config['trading']['strategy']
        if strategy not in config['strategies']:
            logger.error(f"选择的策略 '{strategy}' 在策略配置中未找到")
            return False

        # 验证notifications部分
        if 'dingtalk' not in config['notifications']:
            logger.error("notifications配置中缺少dingtalk部分")
            return False

        dingtalk_required = ['webhook_url']
        for field in dingtalk_required:
            if field not in config['notifications']['dingtalk']:
                logger.error(f"dingtalk配置中缺少必需字段: {field}")
                return False

        logger.info("配置验证通过")
        return True
