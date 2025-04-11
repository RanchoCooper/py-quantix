"""
Example service implementation.

This module provides the implementation of the Example domain service.
"""
import logging
from typing import Dict, List, Optional

from domain.event.base_event import EventBus
from domain.model.errors import EntityNotFoundError, ExampleNameAlreadyExistsError
from domain.model.example import Example
from domain.repository.example_repository import ExampleRepository
from domain.service.example_service import ExampleService

logger = logging.getLogger(__name__)


class ExampleServiceImpl(ExampleService):
    """
    Implementation of the Example domain service.
    
    This service contains domain logic for managing examples.
    """
    
    def __init__(self, repository: ExampleRepository, event_bus: EventBus):
        """
        Initialize the Example service.
        
        Args:
            repository: The Example repository to use
            event_bus: The event bus to publish events to
        """
        self._repository = repository
        self._event_bus = event_bus
    
    def create_example(self, name: str, description: Optional[str] = None) -> Example:
        """
        Create a new example.
        
        Args:
            name: The name of the example
            description: The description of the example
            
        Returns:
            The created example
            
        Raises:
            ExampleNameAlreadyExistsError: If an example with the given name already exists
        """
        # Check if example with the same name already exists
        existing = self._repository.find_by_name(name)
        if existing:
            logger.warning(f"Example with name '{name}' already exists")
            raise ExampleNameAlreadyExistsError(name)
        
        # Create and save the example
        example = Example(name=name, description=description)
        saved_example = self._repository.save(example)
        
        # Publish event
        self._publish_created_event(saved_example)
        
        logger.info(f"Example created: {saved_example.id}")
        return saved_example
    
    def get_example(self, example_id: str) -> Example:
        """
        Get an example by ID.
        
        Args:
            example_id: The ID of the example to get
            
        Returns:
            The found example
            
        Raises:
            EntityNotFoundError: If the example is not found
        """
        example = self._repository.find_by_id(example_id)
        if not example:
            logger.warning(f"Example not found: {example_id}")
            raise EntityNotFoundError("Example", example_id)
        
        logger.info(f"Example retrieved: {example_id}")
        return example
    
    def get_all_examples(self) -> List[Example]:
        """
        Get all examples.
        
        Returns:
            A list of all examples
        """
        examples = self._repository.find_all()
        logger.info(f"Retrieved {len(examples)} examples")
        return examples
    
    def update_example(self, example_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None) -> Example:
        """
        Update an example.
        
        Args:
            example_id: The ID of the example to update
            name: The new name of the example
            description: The new description of the example
            
        Returns:
            The updated example
            
        Raises:
            EntityNotFoundError: If the example is not found
            ExampleNameAlreadyExistsError: If an example with the given name already exists
        """
        # Find the example
        example = self._repository.find_by_id(example_id)
        if not example:
            logger.warning(f"Example not found for update: {example_id}")
            raise EntityNotFoundError("Example", example_id)
        
        # Check if the new name already exists on a different example
        if name and name != example.name:
            existing = self._repository.find_by_name(name)
            if existing and existing.id != example_id:
                logger.warning(f"Example with name '{name}' already exists")
                raise ExampleNameAlreadyExistsError(name)
        
        # Update and save the example
        example.update(name=name, description=description)
        saved_example = self._repository.save(example)
        
        # Publish event
        self._publish_updated_event(saved_example)
        
        logger.info(f"Example updated: {saved_example.id}")
        return saved_example
    
    def delete_example(self, example_id: str) -> bool:
        """
        Delete an example.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            True if the example was deleted, False if not found
        """
        # Find the example first to publish event if it exists
        example = self._repository.find_by_id(example_id)
        
        # Delete the example
        deleted = self._repository.delete(example_id)
        
        # Publish event if the example was deleted
        if deleted and example:
            self._publish_deleted_event(example)
            logger.info(f"Example deleted: {example_id}")
        else:
            logger.warning(f"Example not found for deletion: {example_id}")
        
        return deleted
    
    def _publish_created_event(self, example: Example) -> None:
        """
        Publish an example created event.
        
        Args:
            example: The created example
        """
        from domain.event.example_events import ExampleCreatedEvent
        event = ExampleCreatedEvent(example_id=example.id, example_data=example.to_dict())
        self._event_bus.publish(event)
    
    def _publish_updated_event(self, example: Example) -> None:
        """
        Publish an example updated event.
        
        Args:
            example: The updated example
        """
        from domain.event.example_events import ExampleUpdatedEvent
        event = ExampleUpdatedEvent(example_id=example.id, example_data=example.to_dict())
        self._event_bus.publish(event)
    
    def _publish_deleted_event(self, example: Example) -> None:
        """
        Publish an example deleted event.
        
        Args:
            example: The deleted example
        """
        from domain.event.example_events import ExampleDeletedEvent
        event = ExampleDeletedEvent(example_id=example.id, example_data=example.to_dict())
        self._event_bus.publish(event) 