"""
Example HTTP resources.

This module provides RESTful resources for the Example entity.
"""
import logging
from typing import Dict, List, Optional

from flask import request
from flask_restful import Resource
from werkzeug.exceptions import BadRequest, Conflict, NotFound

from domain.model.errors import EntityNotFoundError
from application.service.example_app_service import ExampleAppService

logger = logging.getLogger(__name__)


class ExampleResource(Resource):
    """
    RESTful resource for a single Example entity.
    
    Provides GET, PUT, and DELETE operations for a specific Example.
    """
    
    def __init__(self, example_app_service: Optional[ExampleAppService] = None):
        """
        Initialize the resource.
        
        Args:
            example_app_service: The application service for examples
        """
        self._app_service = example_app_service
    
    def get(self, example_id: str):
        """
        Handle GET request to retrieve an example.
        
        Args:
            example_id: The ID of the example to retrieve
            
        Returns:
            The example as a JSON object
            
        Raises:
            NotFound: If the example does not exist
        """
        try:
            if not self._app_service:
                return {"error": "Service unavailable"}, 503
            
            example = self._app_service.get_example(example_id)
            return example, 200
        except EntityNotFoundError as e:
            logger.warning(f"Example not found: {example_id}")
            return {"error": "Not Found", "message": str(e)}, 404
        except Exception as e:
            logger.error(f"Error retrieving example: {str(e)}")
            return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500
    
    def put(self, example_id: str):
        """
        Handle PUT request to update an example.
        
        Args:
            example_id: The ID of the example to update
            
        Returns:
            The updated example as a JSON object
            
        Raises:
            NotFound: If the example does not exist
            BadRequest: If the request data is invalid
            Conflict: If the update violates a constraint
        """
        try:
            if not self._app_service:
                return {"error": "Service unavailable"}, 503
            
            data = request.get_json()
            if not data:
                return {"error": "Bad Request", "message": "No JSON data provided"}, 400
            
            name = data.get('name')
            description = data.get('description')
            
            example = self._app_service.update_example(
                example_id=example_id,
                name=name,
                description=description
            )
            
            return example, 200
        except EntityNotFoundError as e:
            logger.warning(f"Example not found: {example_id}")
            return {"error": "Not Found", "message": str(e)}, 404
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {"error": "Conflict", "message": str(e)}, 409
        except Exception as e:
            logger.error(f"Error updating example: {str(e)}")
            return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500
    
    def delete(self, example_id: str):
        """
        Handle DELETE request to delete an example.
        
        Args:
            example_id: The ID of the example to delete
            
        Returns:
            Empty response with appropriate status code
            
        Raises:
            NotFound: If the example does not exist
        """
        try:
            if not self._app_service:
                return {"error": "Service unavailable"}, 503
            
            deleted = self._app_service.delete_example(example_id)
            
            if deleted:
                return "", 204
            else:
                return {"error": "Not Found", "message": f"Example with ID '{example_id}' not found"}, 404
        except Exception as e:
            logger.error(f"Error deleting example: {str(e)}")
            return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500


class ExampleListResource(Resource):
    """
    RESTful resource for a collection of Example entities.
    
    Provides GET and POST operations for the Example collection.
    """
    
    def __init__(self, example_app_service: Optional[ExampleAppService] = None):
        """
        Initialize the resource.
        
        Args:
            example_app_service: The application service for examples
        """
        self._app_service = example_app_service
    
    def get(self):
        """
        Handle GET request to retrieve all examples.
        
        Returns:
            A list of examples as JSON
        """
        try:
            if not self._app_service:
                return {"error": "Service unavailable"}, 503
            
            examples = self._app_service.get_all_examples()
            return examples, 200
        except Exception as e:
            logger.error(f"Error retrieving examples: {str(e)}")
            return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500
    
    def post(self):
        """
        Handle POST request to create a new example.
        
        Returns:
            The created example as JSON
            
        Raises:
            BadRequest: If the request data is invalid
            Conflict: If the creation violates a constraint
        """
        try:
            if not self._app_service:
                return {"error": "Service unavailable"}, 503
            
            data = request.get_json()
            if not data:
                return {"error": "Bad Request", "message": "No JSON data provided"}, 400
            
            name = data.get('name')
            if not name:
                return {"error": "Bad Request", "message": "Name is required"}, 400
            
            description = data.get('description')
            
            example = self._app_service.create_example(
                name=name,
                description=description
            )
            
            return example, 201
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {"error": "Conflict", "message": str(e)}, 409
        except Exception as e:
            logger.error(f"Error creating example: {str(e)}")
            return {"error": "Internal Server Error", "message": "An unexpected error occurred"}, 500 