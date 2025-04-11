"""
Example event handlers.

This module provides event handlers for Example-related domain events.
"""
import logging

from domain.event.base_event import Event, EventHandler
from domain.event.example_events import (
    ExampleCreatedEvent, ExampleDeletedEvent, ExampleUpdatedEvent
)

logger = logging.getLogger(__name__)


class ExampleCreatedEventHandler(EventHandler):
    """Handler for the ExampleCreatedEvent."""
    
    def handle(self, event: ExampleCreatedEvent) -> None:
        """
        Handle an ExampleCreatedEvent.
        
        Args:
            event: The event to handle
        """
        logger.info(f"Example created: {event.example_id}")
        
        # Here you would perform side effects like:
        # - Updating search indexes
        # - Sending notifications
        # - Updating caches
        # - Logging audit trails
        # etc.


class ExampleUpdatedEventHandler(EventHandler):
    """Handler for the ExampleUpdatedEvent."""
    
    def handle(self, event: ExampleUpdatedEvent) -> None:
        """
        Handle an ExampleUpdatedEvent.
        
        Args:
            event: The event to handle
        """
        logger.info(f"Example updated: {event.example_id}")
        
        # Here you would perform side effects like:
        # - Updating search indexes
        # - Sending notifications
        # - Updating caches
        # - Logging audit trails
        # etc.


class ExampleDeletedEventHandler(EventHandler):
    """Handler for the ExampleDeletedEvent."""
    
    def handle(self, event: ExampleDeletedEvent) -> None:
        """
        Handle an ExampleDeletedEvent.
        
        Args:
            event: The event to handle
        """
        logger.info(f"Example deleted: {event.example_id}")
        
        # Here you would perform side effects like:
        # - Updating search indexes
        # - Sending notifications
        # - Updating caches
        # - Logging audit trails
        # etc. 