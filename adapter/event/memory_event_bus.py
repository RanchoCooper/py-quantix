"""
In-memory event bus implementation.

This module provides an in-memory implementation of the event bus.
"""
import logging
from typing import Dict, List, Set, Type

from domain.event.base_event import Event, EventBus, EventHandler

logger = logging.getLogger(__name__)


class MemoryEventBus(EventBus):
    """
    In-memory implementation of the event bus.
    
    This class provides a simple implementation of the event bus that
    keeps handlers in memory and publishes events synchronously.
    """
    
    def __init__(self):
        """Initialize an empty subscription map."""
        self._handlers: Dict[Type[Event], List[EventHandler]] = {}
    
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: The event to publish
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"No handlers for event type {event_type.__name__}")
            return
        
        logger.debug(f"Publishing event {event_type.__name__} to {len(handlers)} handlers")
        
        for handler in handlers:
            try:
                handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling event {event_type.__name__} by {handler.__class__.__name__}: {str(e)}")
    
    def subscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when the event is published
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Handler {handler.__class__.__name__} subscribed to event {event_type.__name__}")
    
    def unsubscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler {handler.__class__.__name__} unsubscribed from event {event_type.__name__}")
            
            # Clean up empty lists
            if not self._handlers[event_type]:
                del self._handlers[event_type] 