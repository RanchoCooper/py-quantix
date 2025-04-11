"""
SQLAlchemy Example repository implementation.

This module provides the SQLAlchemy-based implementation of the Example repository.
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy.exc import IntegrityError, NoResultFound

from domain.model.example import Example
from domain.repository.example_repository import ExampleRepository
from adapter.repository.sqlalchemy.base_repository import BaseSQLAlchemyRepository
from adapter.repository.sqlalchemy.models import ExampleModel

logger = logging.getLogger(__name__)


class SQLAlchemyExampleRepository(BaseSQLAlchemyRepository, ExampleRepository):
    """
    SQLAlchemy implementation of the Example repository.
    
    This class provides a SQLAlchemy-based implementation of the Example repository
    interface defined in the domain layer.
    """
    
    def save(self, example: Example) -> Example:
        """
        Save an example to the database.
        
        Args:
            example: The example to save
            
        Returns:
            The saved example
            
        Raises:
            ValueError: If an example with the same name already exists
        """
        try:
            # Convert domain entity to ORM model
            example_model = self._to_model(example)
            
            # Add to session
            self._session.add(example_model)
            
            # Commit transaction
            self._commit()
            
            logger.info(f"Example saved: {example.id}")
            return example
        except IntegrityError as e:
            self._rollback()
            logger.error(f"Error saving example: {str(e)}")
            if "Duplicate entry" in str(e) and "name" in str(e):
                raise ValueError(f"Example with name '{example.name}' already exists")
            raise
    
    def find_by_id(self, example_id: str) -> Optional[Example]:
        """
        Find an example by ID.
        
        Args:
            example_id: The ID of the example to find
            
        Returns:
            The found example or None if not found
        """
        try:
            example_model = self._session.query(ExampleModel).filter(
                ExampleModel.id == example_id
            ).one()
            return self._to_entity(example_model)
        except NoResultFound:
            logger.info(f"Example not found: {example_id}")
            return None
    
    def find_by_name(self, name: str) -> Optional[Example]:
        """
        Find an example by name.
        
        Args:
            name: The name of the example to find
            
        Returns:
            The found example or None if not found
        """
        try:
            example_model = self._session.query(ExampleModel).filter(
                ExampleModel.name == name
            ).one()
            return self._to_entity(example_model)
        except NoResultFound:
            logger.info(f"Example not found with name: {name}")
            return None
    
    def find_all(self) -> List[Example]:
        """
        Find all examples.
        
        Returns:
            A list of all examples
        """
        example_models = self._session.query(ExampleModel).all()
        return [self._to_entity(model) for model in example_models]
    
    def delete(self, example_id: str) -> bool:
        """
        Delete an example by ID.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            True if the example was deleted, False if not found
        """
        try:
            result = self._session.query(ExampleModel).filter(
                ExampleModel.id == example_id
            ).delete()
            self._commit()
            
            deleted = result > 0
            if deleted:
                logger.info(f"Example deleted: {example_id}")
            else:
                logger.info(f"Example not found for deletion: {example_id}")
            return deleted
        except Exception as e:
            self._rollback()
            logger.error(f"Error deleting example: {str(e)}")
            raise
    
    def _to_model(self, example: Example) -> ExampleModel:
        """
        Convert a domain entity to an ORM model.
        
        Args:
            example: The domain entity to convert
            
        Returns:
            The ORM model
        """
        return ExampleModel(
            id=example.id,
            name=example.name,
            description=example.description
        )
    
    def _to_entity(self, model: ExampleModel) -> Example:
        """
        Convert an ORM model to a domain entity.
        
        Args:
            model: The ORM model to convert
            
        Returns:
            The domain entity
        """
        return Example(
            id=model.id,
            name=model.name,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        ) 