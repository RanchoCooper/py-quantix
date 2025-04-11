"""
Example domain model.

This module defines the Example entity for the domain.
"""
from dataclasses import dataclass
from datetime import datetime
import uuid
from typing import Optional


@dataclass
class Example:
    """
    Example entity in the domain model.
    
    Represents an example object with basic properties.
    """
    name: str
    description: Optional[str] = None
    id: str = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        """Initialize ID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())
            
        if self.created_at is None:
            self.created_at = datetime.utcnow()
            
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update(self, name: str = None, description: str = None) -> None:
        """
        Update the example properties.
        
        Args:
            name: New name for the example
            description: New description for the example
        """
        if name is not None:
            self.name = name
            
        if description is not None:
            self.description = description
            
        self.updated_at = datetime.utcnow()
        
    def to_dict(self) -> dict:
        """
        Convert the example to a dictionary.
        
        Returns:
            Dictionary representation of the example
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 