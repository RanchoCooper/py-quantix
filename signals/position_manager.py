"""
仓位管理器
负责管理持仓信息
"""
from typing import Any, Dict, Optional

from loguru import logger


class PositionManager:
    """仓位管理器 - 负责管理持仓信息"""

    def __init__(self):
        self.positions: Dict[str, Dict[str, Any]] = {}

    def update_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float
    ) -> None:
        self.positions[symbol] = {
            'side': side,
            'size': size,
            'entry_price': entry_price
        }

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.positions.get(symbol)

    def clear_position(self, symbol: str) -> None:
        if symbol in self.positions:
            del self.positions[symbol]

    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        return self.positions.copy()
