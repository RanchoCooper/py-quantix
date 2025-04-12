"""
Domain model errors.

This module defines custom error classes for the domain model.
"""


class DomainError(Exception):
    """Base class for domain-specific errors."""

    pass


class EntityNotFoundError(DomainError):
    """Error raised when an entity is not found."""

    def __init__(self, entity_type, entity_id):
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with ID '{entity_id}' not found")


class ValidationError(DomainError):
    """Error raised when entity validation fails."""

    pass
