"""
Unit tests for domain error models.
"""
import unittest

from domain.model.errors import DomainError, EntityNotFoundError, ValidationError


class TestDomainErrors(unittest.TestCase):
    """Test cases for domain error classes"""

    def test_domain_error(self):
        """Test basic domain error."""
        error_message = "General domain error"
        error = DomainError(error_message)

        self.assertEqual(str(error), error_message)
        self.assertIsInstance(error, Exception)

    def test_entity_not_found_error(self):
        """Test entity not found error."""
        entity_type = "User"
        entity_id = "123"

        error = EntityNotFoundError(entity_type, entity_id)

        self.assertEqual(error.entity_type, entity_type)
        self.assertEqual(error.entity_id, entity_id)
        self.assertEqual(str(error), f"{entity_type} with ID '{entity_id}' not found")
        self.assertIsInstance(error, DomainError)

    def test_validation_error(self):
        """Test validation error."""
        error_message = "Validation failed"
        error = ValidationError(error_message)

        self.assertEqual(str(error), error_message)
        self.assertIsInstance(error, DomainError)


if __name__ == "__main__":
    unittest.main()
