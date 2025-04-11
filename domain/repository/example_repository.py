"""
Example repository interface.

This module defines the repository interface for Example entities.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.model.example import Example


class ExampleRepository(ABC):
    """
    Repository interface for Example entities.
    
    This abstract class defines the operations for Example persistence.
    """
    
    @abstractmethod
    def save(self, example: Example) -> Example:
        """
        Save an example.
        
        Args:
            example: The example to save
            
        Returns:
            The saved example
        """
        pass
    
    @abstractmethod
    def find_by_id(self, example_id: str) -> Optional[Example]:
        """
        Find an example by ID.
        
        Args:
            example_id: The ID of the example to find
            
        Returns:
            The found example or None if not found
        """
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Example]:
        """
        Find an example by name.
        
        Args:
            name: The name of the example to find
            
        Returns:
            The found example or None if not found
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[Example]:
        """
        Find all examples.
        
        Returns:
            A list of all examples
        """
        pass
    
    @abstractmethod
    def delete(self, example_id: str) -> bool:
        """
        Delete an example by ID.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            True if the example was deleted, False if not found
        """
        pass 