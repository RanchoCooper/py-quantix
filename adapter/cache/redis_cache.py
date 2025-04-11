"""
Redis cache adapter.

This module provides a Redis-based cache implementation.
"""
import json
import logging
import pickle
from typing import Any, Dict, List, Optional, Union

import redis

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based cache implementation.
    
    This class provides a simple caching interface using Redis as the backend.
    """
    
    def __init__(self, redis_client: redis.Redis, prefix: str = ""):
        """
        Initialize the Redis cache.
        
        Args:
            redis_client: Redis client instance
            prefix: Key prefix to namespace cache entries
        """
        self._redis = redis_client
        self._prefix = prefix
    
    def _format_key(self, key: str) -> str:
        """
        Format a key with the namespace prefix.
        
        Args:
            key: The original key
            
        Returns:
            The prefixed key
        """
        return f"{self._prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found
        """
        try:
            prefixed_key = self._format_key(key)
            data = self._redis.get(prefixed_key)
            
            if data is None:
                return None
            
            try:
                # Try to deserialize with pickle first (for complex objects)
                return pickle.loads(data)
            except:
                # Fall back to JSON for simple types
                try:
                    return json.loads(data)
                except:
                    # Return raw data if all else fails
                    return data
        except Exception as e:
            logger.error(f"Error getting value from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prefixed_key = self._format_key(key)
            
            # Try to serialize with pickle first
            try:
                data = pickle.dumps(value)
            except:
                # Fall back to JSON for simple types
                try:
                    data = json.dumps(value)
                except:
                    # Store raw value if all else fails
                    data = value
            
            self._redis.set(prefixed_key, data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error setting value in cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the key was deleted, False otherwise
        """
        try:
            prefixed_key = self._format_key(key)
            result = self._redis.delete(prefixed_key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting value from cache: {str(e)}")
            return False
    
    def clear(self, pattern: str = "*") -> bool:
        """
        Clear all cache entries matching a pattern.
        
        Args:
            pattern: The pattern to match keys against
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prefixed_pattern = self._format_key(pattern)
            keys = self._redis.keys(prefixed_pattern)
            
            if keys:
                self._redis.delete(*keys)
            
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
