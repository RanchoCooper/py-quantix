"""
Flask application resources.

This module provides functions to register resources with a Flask-RESTful API.
"""
import logging
from typing import Optional

from flask_restful import Api

logger = logging.getLogger(__name__)


def register_resources(api: Api):
    """
    Register RESTful resources with the Flask API.

    Args:
        api: The Flask-RESTful API instance
    """
    # Register resources to API
    # Add all required API resources here

    logger.info("API resources registered successfully")
