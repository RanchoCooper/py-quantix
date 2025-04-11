"""
Base repository implementation for SQLAlchemy.

This module provides a base class for SQLAlchemy-based repositories
that can dynamically choose which database to use.
"""
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from adapter.repository import db_registry


class BaseSQLAlchemyRepository:
    """
    Base SQLAlchemy repository implementation
    
    Provides basic database operations and ability to dynamically select databases
    """
    
    def __init__(self, db_name=None):
        """
        Initialize repository
        
        Args:
            db_name: Database name to use, uses default database if None
        """
        self._db_name = db_name
    
    @property
    def _session(self) -> Session:
        """
        Get current session
        
        Returns:
            SQLAlchemy Session instance
        """
        return db_registry.get_session(self._db_name)
    
    def _commit(self):
        """Commit transaction"""
        try:
            self._session.commit()
        except SQLAlchemyError as e:
            self._session.rollback()
            raise e
    
    def _rollback(self):
        """Rollback transaction"""
        self._session.rollback() 