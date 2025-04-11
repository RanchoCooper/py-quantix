"""
Flask middleware.

This module provides middleware for the Flask application.
"""
import logging
import time
from typing import Callable

from flask import Flask, request

logger = logging.getLogger(__name__)


def logging_middleware(app: Flask) -> None:
    """
    Middleware for logging requests and responses.
    
    Args:
        app: The Flask application
    """
    @app.before_request
    def before_request() -> None:
        """Store the start time for the request."""
        request.start_time = time.time()
        logger.debug(f"Request: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        """Log the response time."""
        duration = time.time() - request.start_time
        logger.debug(f"Response: {response.status_code}, Duration: {duration:.6f}s")
        return response


def register_middlewares(app: Flask) -> None:
    """
    Register all middleware with the Flask application.
    
    Args:
        app: The Flask application
    """
    logging_middleware(app)
    
    logger.info("Middlewares registered") 