"""
Example service interface.

This module defines the interface for example services.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.model.example import Example


class ExampleService(ABC):
    """
    Interface for example services.
    
    This abstract class defines the operations for managing examples.
    """
    
    @abstractmethod
    def create_example(self, name: str, description: Optional[str] = None) -> Example:
        """
        Create a new example.
        
        Args:
            name: The name of the example
            description: The description of the example
            
        Returns:
            The created example
        """
        pass
    
    @abstractmethod
    def get_example(self, example_id: str) -> Example:
        """
        Get an example by ID.
        
        Args:
            example_id: The ID of the example to get
            
        Returns:
            The found example
        """
        pass
    
    @abstractmethod
    def get_all_examples(self) -> List[Example]:
        """
        Get all examples.
        
        Returns:
            A list of all examples
        """
        pass
    
    @abstractmethod
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
        """
        pass
    
    @abstractmethod
    def delete_example(self, example_id: str) -> bool:
        """
        Delete an example.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            True if the example was deleted, False if not found
        """
        pass 