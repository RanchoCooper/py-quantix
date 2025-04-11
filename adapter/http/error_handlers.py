"""
Flask error handlers.

This module provides error handlers for the Flask application.
"""
import logging
from typing import Tuple, Dict, Any

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def handle_http_exception(e: HTTPException) -> Tuple[Dict[str, Any], int]:
    """
    Handle HTTP exceptions.
    
    Args:
        e: The HTTP exception
        
    Returns:
        A tuple of (response_body, status_code)
    """
    response = {
        "error": e.__class__.__name__,
        "message": e.description
    }
    return response, e.code


def handle_validation_error(e: ValueError) -> Tuple[Dict[str, Any], int]:
    """
    Handle validation errors.
    
    Args:
        e: The validation error
        
    Returns:
        A tuple of (response_body, status_code)
    """
    response = {
        "error": "ValidationError",
        "message": str(e)
    }
    return response, 400


def handle_generic_error(e: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Handle generic exceptions.
    
    Args:
        e: The exception
        
    Returns:
        A tuple of (response_body, status_code)
    """
    logger.exception("Unhandled exception: %s", str(e))
    response = {
        "error": "InternalServerError",
        "message": "An unexpected error occurred"
    }
    return response, 500


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers with the Flask application.
    
    Args:
        app: The Flask application
    """
    app.register_error_handler(HTTPException, handle_http_exception)
    app.register_error_handler(ValueError, handle_validation_error)
    app.register_error_handler(Exception, handle_generic_error)
    
    logger.info("Error handlers registered") 