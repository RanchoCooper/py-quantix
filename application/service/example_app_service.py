"""
Example application service.

This module provides the application service for managing examples.
"""
import logging
from typing import Dict, List, Optional

from domain.model.errors import EntityNotFoundError, ExampleNameAlreadyExistsError
from domain.service.example_service import ExampleService

logger = logging.getLogger(__name__)


class ExampleAppService:
    """
    Application service for managing examples.
    
    This service provides a facade for the domain logic, providing
    use cases for client code to interact with.
    """
    
    def __init__(self, example_service: ExampleService):
        """
        Initialize the Example application service.
        
        Args:
            example_service: The domain service for examples
        """
        self._example_service = example_service
    
    def create_example(self, name: str, description: Optional[str] = None) -> Dict:
        """
        Create a new example.
        
        Args:
            name: The name of the example
            description: The description of the example
            
        Returns:
            A dictionary representation of the created example
            
        Raises:
            ValueError: If an example with the given name already exists
        """
        try:
            example = self._example_service.create_example(name, description)
            logger.info(f"Example created via app service: {example.id}")
            return example.to_dict()
        except ExampleNameAlreadyExistsError as e:
            logger.warning(f"Failed to create example: {str(e)}")
            raise ValueError(str(e))
    
    def get_example(self, example_id: str) -> Dict:
        """
        Get an example by ID.
        
        Args:
            example_id: The ID of the example to get
            
        Returns:
            A dictionary representation of the example
            
        Raises:
            EntityNotFoundError: If the example is not found
        """
        example = self._example_service.get_example(example_id)
        logger.info(f"Example retrieved via app service: {example_id}")
        return example.to_dict()
    
    def get_all_examples(self) -> List[Dict]:
        """
        Get all examples.
        
        Returns:
            A list of dictionary representations of all examples
        """
        examples = self._example_service.get_all_examples()
        logger.info(f"Retrieved {len(examples)} examples via app service")
        return [example.to_dict() for example in examples]
    
    def update_example(self, example_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None) -> Dict:
        """
        Update an example.
        
        Args:
            example_id: The ID of the example to update
            name: The new name of the example
            description: The new description of the example
            
        Returns:
            A dictionary representation of the updated example
            
        Raises:
            EntityNotFoundError: If the example is not found
            ValueError: If an example with the given name already exists
        """
        try:
            example = self._example_service.update_example(
                example_id, name, description
            )
            logger.info(f"Example updated via app service: {example_id}")
            return example.to_dict()
        except ExampleNameAlreadyExistsError as e:
            logger.warning(f"Failed to update example: {str(e)}")
            raise ValueError(str(e))
    
    def delete_example(self, example_id: str) -> bool:
        """
        Delete an example.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            True if the example was deleted, False if not found
        """
        deleted = self._example_service.delete_example(example_id)
        logger.info(f"Example deletion attempted via app service: {example_id}, success: {deleted}")
        return deleted 