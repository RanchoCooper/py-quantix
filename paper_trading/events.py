"""
事件总线
提供 SSE 事件广播能力
"""
from typing import Callable, Dict, Any, List


class EventBus:
    """
    事件总线：支持订阅/取消订阅/广播

    用法：
        bus = EventBus()
        bus.subscribe(handler)
        bus.emit("position_opened", {"position_id": "..."})
        bus.unsubscribe(handler)
    """

    def __init__(self) -> None:
        self._subscribers: List[Callable[[str, Dict[str, Any]], None]] = []

    def subscribe(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """注册事件处理器"""
        if handler not in self._subscribers:
            self._subscribers.append(handler)

    def unsubscribe(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """取消注册事件处理器"""
        if handler in self._subscribers:
            self._subscribers.remove(handler)

    def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """向所有订阅者广播事件"""
        for handler in self._subscribers:
            try:
                handler(event_type, data)
            except Exception:
                pass

    def __len__(self) -> int:
        return len(self._subscribers)
