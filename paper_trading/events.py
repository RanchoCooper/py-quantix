"""
事件总线
提供 SSE 事件广播能力，替代分散的 emit_event + 全局队列
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
                # 不应抛出异常打断业务流程
                pass

    def __len__(self) -> int:
        return len(self._subscribers)


# 向后兼容的全局函数（内部由 app.state 中的 EventBus 实例提供）
_legacy_bus: EventBus = EventBus()


def get_event_bus() -> EventBus:
    """向后兼容：获取事件总线实例"""
    return _legacy_bus


def emit_event(event_type: str, data: Dict[str, Any]) -> None:
    """向后兼容的全局 emit_event"""
    _legacy_bus.emit(event_type, data)
