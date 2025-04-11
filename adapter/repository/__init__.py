"""
Repository adapters package.

This package contains adapter implementations for the domain repositories.
"""
import os

class DatabaseRegistry:
    """Database registry that manages different database connections"""

    def __init__(self):
        self._engines = {}
        self._sessions = {}
        self._default = None

    def register(self, name, engine, session):
        """
        Register a database connection
        
        Args:
            name: Database connection name
            engine: SQLAlchemy Engine instance
            session: SQLAlchemy Session instance
        """
        self._engines[name] = engine
        self._sessions[name] = session
        if self._default is None:
            self._default = name

    def set_default(self, name):
        """
        Set the default database connection
        
        Args:
            name: Database connection name
        """
        if name not in self._engines:
            raise ValueError(f"No database registered with name '{name}'")
        self._default = name

    def get_engine(self, name=None):
        """
        Get the database engine
        
        Args:
            name: Database connection name, returns the default connection if None
            
        Returns:
            SQLAlchemy Engine instance
        """
        if name is None:
            name = self._default
        if name not in self._engines:
            raise ValueError(f"No database registered with name '{name}'")
        return self._engines[name]

    def get_session(self, name=None):
        """
        Get the database session
        
        Args:
            name: Database connection name, returns the default connection if None
            
        Returns:
            SQLAlchemy Session instance
        """
        if name is None:
            name = self._default
        if name not in self._sessions:
            raise ValueError(f"No database registered with name '{name}'")
        return self._sessions[name]


# Create a global database registry instance
db_registry = DatabaseRegistry()

# Create directory structure for SQLAlchemy models and repositories if needed
def ensure_directories():
    """Ensure that all required directories exist."""
    dirs = [
        'adapter/repository/sqlalchemy',
        'adapter/http/resources',
        'domain/model',
        'domain/repository',
        'domain/service',
        'domain/event',
        'application/service',
        'application/event',
    ]
    
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(directory, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('"""' + directory.replace('/', '.') + ' package."""\n')

# Run directory creation on import
ensure_directories()
