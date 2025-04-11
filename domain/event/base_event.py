"""
Base event classes.

This module defines the base event classes and event bus interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import uuid
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    """
    Base class for all domain events.
    
    Domain events represent something significant that happened in the domain.
    """
    id: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Initialize event properties if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventHandler(ABC):
    """
    Interface for event handlers.
    
    Event handlers respond to domain events by executing business logic.
    """
    
    @abstractmethod
    def handle(self, event: Event) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        pass


class EventBus(ABC):
    """
    Interface for event buses.
    
    Event buses facilitate the publish-subscribe pattern between event publishers
    and event handlers.
    """
    
    @abstractmethod
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event: The event to publish
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when the event is published
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Unsubscribe a handler from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        pass 