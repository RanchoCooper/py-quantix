"""
Dependency injection container.

This module provides the dependency injection container for the application,
which manages the instantiation and wiring of application components.
"""
import logging

import redis
from dependency_injector import containers, providers

from adapter.cache.redis_cache import RedisCache
from adapter.event.memory_event_bus import MemoryEventBus
from adapter.http.app_factory import create_app
from adapter.http.flask_app import register_resources
from adapter.repository import db_registry
from adapter.repository.sqlalchemy import (
    create_mysql_engine,
    create_postgresql_engine,
    create_scoped_session,
    create_session_factory,
)
from adapter.repository.sqlalchemy import initialize_database as init_db_schema

logger = logging.getLogger(__name__)


def register_resources_with_deps(api):
    """
    Register API resources with the Flask-RESTful API, injecting dependencies.
    
    Args:
        api: Flask-RESTful API instance
    """
    container = _get_container_instance()
    
    if container is not None:
        register_resources(api)
    else:
        logger.warning("Container instance not available, resources will not have dependencies injected")
        register_resources(api)


# Global variable for storing container instance reference
_container_instance = None


def _get_container_instance():
    return _container_instance


def _set_container_instance(container):
    global _container_instance
    _container_instance = container


def register_databases(mysql_engine, postgresql_engine, mysql_session, postgresql_session, default_db):
    """
    Register databases in the global registry
    
    Args:
        mysql_engine: MySQL engine instance
        postgresql_engine: PostgreSQL engine instance
        mysql_session: MySQL session instance
        postgresql_session: PostgreSQL session instance
        default_db: Default database name
    """
    db_registry.register('mysql', mysql_engine, mysql_session)
    db_registry.register('postgresql', postgresql_engine, postgresql_session)
    if default_db in ('mysql', 'postgresql'):
        db_registry.set_default(default_db)
    logger.info(f"Databases registered: mysql, postgresql. Default: {db_registry._default}")


class AppContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for the application.
    
    This container manages the instantiation and wiring of application
    components, following the dependency injection pattern.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Logging
    logging = providers.Resource(
        logging.basicConfig,
        level=config.logging.level,
        format=config.logging.format
    )
    
    # Database
    mysql_engine = providers.Singleton(
        create_mysql_engine,
        config.db.mysql.url,
        echo=config.db.mysql.echo,
    )
    
    postgresql_engine = providers.Singleton(
        create_postgresql_engine,
        config.db.postgresql.url,
        echo=config.db.postgresql.echo,
    )
    
    mysql_session_factory = providers.Singleton(
        create_session_factory,
        engine=mysql_engine
    )
    
    postgresql_session_factory = providers.Singleton(
        create_session_factory,
        engine=postgresql_engine
    )
    
    mysql_session = providers.Singleton(
        create_scoped_session,
        mysql_session_factory
    )
    
    postgresql_session = providers.Singleton(
        create_scoped_session,
        postgresql_session_factory
    )
    
    # Database Registry
    db_registry_configurator = providers.Resource(
        register_databases,
        mysql_engine=mysql_engine,
        postgresql_engine=postgresql_engine,
        mysql_session=mysql_session,
        postgresql_session=postgresql_session,
        default_db=config.db.default
    )
    
    # Redis
    redis_client = providers.Singleton(
        redis.Redis,
        host=config.redis.host,
        port=config.redis.port,
        db=config.redis.db,
        decode_responses=False
    )
    
    # Cache
    redis_cache = providers.Singleton(
        RedisCache,
        redis_client=redis_client,
        prefix=config.redis.prefix
    )
    
    # Event Bus
    event_bus = providers.Singleton(
        MemoryEventBus
    )
    
    # Flask App
    flask_app = providers.Singleton(
        create_app,
        config=config.flask,
        register_resources_func=register_resources_with_deps
    )


def initialize_event_handlers(container):
    """
    Initialize event handlers by subscribing them to the event bus.
    
    Args:
        container: The dependency injection container
    """
    event_bus = container.event_bus()
    logger.info("Event handlers initialized and subscribed to event bus")


def initialize_database(container):
    """
    Initialize the database by creating tables.
    
    Args:
        container: The dependency injection container
    """
    try:
        # Ensure database registration is completed
        container.db_registry_configurator()
        
        # Initialize MySQL database
        mysql_engine = container.mysql_engine()
        init_db_schema(mysql_engine)
        logger.info("MySQL database tables created")
        
        # Initialize PostgreSQL database
        postgresql_engine = container.postgresql_engine()
        init_db_schema(postgresql_engine)
        logger.info("PostgreSQL database tables created")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise 