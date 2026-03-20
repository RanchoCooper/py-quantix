"""
配置解析工具模块
提供配置解析的公共函数
"""
from typing import Any, Dict, List, Union


def parse_symbol_config(
    symbols_config: Union[List, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    解析交易对配置，支持列表和字典两种格式

    Args:
        symbols_config: 交易对配置
            - 列表格式: [{'symbol': 'BTCUSDT', 'leverage': 10}, ...]
            - 字典格式: {'BTCUSDT': {'leverage': 10}, ...}

    Returns:
        交易对配置列表

    Examples:
        >>> parse_symbol_config(['BTCUSDT', 'ETHUSDT'])
        [{'symbol': 'BTCUSDT'}, {'symbol': 'ETHUSDT'}]
        >>> parse_symbol_config({'BTCUSDT': {'leverage': 10}})
        [{'symbol': 'BTCUSDT', 'leverage': 10}]
    """
    if isinstance(symbols_config, list):
        # 确保每个元素都有 symbol 字段
        result = []
        for item in symbols_config:
            if isinstance(item, str):
                result.append({'symbol': item})
            elif isinstance(item, dict):
                result.append(item)
            else:
                continue
        return result
    elif isinstance(symbols_config, dict):
        return [
            {'symbol': k, **v} if isinstance(v, dict) else {'symbol': k}
            for k, v in symbols_config.items()
        ]
    return []


def get_symbol_list(symbols_config: Union[List, Dict[str, Any]]) -> List[str]:
    """
    获取交易对符号列表

    Args:
        symbols_config: 交易对配置

    Returns:
        符号列表

    Examples:
        >>> get_symbol_list(['BTCUSDT', 'ETHUSDT'])
        ['BTCUSDT', 'ETHUSDT']
        >>> get_symbol_config({'BTCUSDT': {'leverage': 10}})
        ['BTCUSDT']
    """
    parsed = parse_symbol_config(symbols_config)
    return [item.get('symbol', '') for item in parsed if item.get('symbol')]


def get_symbol_config(
    symbols_config: Union[List, Dict[str, Any]],
    symbol: str
) -> Dict[str, Any]:
    """
    获取指定交易对的配置

    Args:
        symbols_config: 交易对配置
        symbol: 交易对符号

    Returns:
        交易对配置字典，如果不存在则返回空字典
    """
    parsed = parse_symbol_config(symbols_config)
    for item in parsed:
        if item.get('symbol') == symbol:
            return item
    return {}


def merge_symbol_config(
    global_config: Dict[str, Any],
    symbol_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    合并全局配置和交易对特定配置

    Args:
        global_config: 全局配置
        symbol_config: 交易对特定配置

    Returns:
        合并后的配置

    Examples:
        >>> merge_symbol_config(
        ...     {'leverage': 10, 'position_size': 0.001},
        ...     {'leverage': 20}
        ... )
        {'leverage': 20, 'position_size': 0.001}
    """
    result = global_config.copy()
    result.update(symbol_config)
    return result
