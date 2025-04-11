"""
SQLAlchemy-specific repository adapters utilities.

This module provides functions for creating database connections and sessions.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def create_mysql_engine(url, echo=False):
    """
    Create a MySQL database engine
    
    Args:
        url: MySQL database connection URL
        echo: Whether to output SQL statements (for debugging)
        
    Returns:
        SQLAlchemy Engine instance
    """
    return create_engine(url, echo=echo)


def create_postgresql_engine(url, echo=False):
    """
    Create a PostgreSQL database engine
    
    Args:
        url: PostgreSQL database connection URL
        echo: Whether to output SQL statements (for debugging)
        
    Returns:
        SQLAlchemy Engine instance
    """
    return create_engine(url, echo=echo)


def create_session_factory(engine):
    """
    Create a database session factory
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        SQLAlchemy session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_scoped_session(session_factory):
    """
    Create a thread-safe database session
    
    Args:
        session_factory: SQLAlchemy session factory
        
    Returns:
        Thread-safe SQLAlchemy session
    """
    return scoped_session(session_factory)


def initialize_database(engine):
    """
    Initialize database schema
    
    Args:
        engine: SQLAlchemy engine instance
    """
    from adapter.repository.sqlalchemy.models import Base
    Base.metadata.create_all(bind=engine) 