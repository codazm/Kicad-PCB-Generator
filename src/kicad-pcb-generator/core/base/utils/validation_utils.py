"""
Shared validation utility functions.
"""
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ValidationUtils:
    """Shared validation utility functions."""
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
        """Validate that required fields are present.
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Required field '{field}' is missing or null")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> Tuple[bool, List[str]]:
        """Validate field types.
        
        Args:
            data: Data to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_numeric_range(value: float, min_value: Optional[float] = None, 
                              max_value: Optional[float] = None, field_name: str = "value") -> Tuple[bool, List[str]]:
        """Validate numeric value is within range.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if min_value is not None and value < min_value:
            errors.append(f"Field '{field_name}' must be >= {min_value}, got {value}")
        
        if max_value is not None and value > max_value:
            errors.append(f"Field '{field_name}' must be <= {max_value}, got {value}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_string_length(value: str, min_length: Optional[int] = None, 
                              max_length: Optional[int] = None, field_name: str = "value") -> Tuple[bool, List[str]]:
        """Validate string length.
        
        Args:
            value: String to validate
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        length = len(value)
        
        if min_length is not None and length < min_length:
            errors.append(f"Field '{field_name}' must be at least {min_length} characters, got {length}")
        
        if max_length is not None and length > max_length:
            errors.append(f"Field '{field_name}' must be at most {max_length} characters, got {length}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_enum_value(value: Any, allowed_values: List[Any], field_name: str = "value") -> Tuple[bool, List[str]]:
        """Validate enum-like value.
        
        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of the field for error messages
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if value not in allowed_values:
            errors.append(f"Field '{field_name}' must be one of {allowed_values}, got {value}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_file_path(file_path: str, must_exist: bool = True, 
                          allowed_extensions: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """Validate file path.
        
        Args:
            file_path: File path to validate
            must_exist: Whether file must exist
            allowed_extensions: List of allowed file extensions
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not file_path:
            errors.append("File path cannot be empty")
            return False, errors
        
        if must_exist:
            import os
            if not os.path.exists(file_path):
                errors.append(f"File does not exist: {file_path}")
        
        if allowed_extensions:
            import os
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in [e.lower() for e in allowed_extensions]:
                errors.append(f"File extension must be one of {allowed_extensions}, got {ext}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, List[str]]:
        """Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not url:
            errors.append("URL cannot be empty")
            return False, errors
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('ftp://')):
            errors.append("URL must start with http://, https://, or ftp://")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, List[str]]:
        """Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not email:
            errors.append("Email cannot be empty")
            return False, errors
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> Tuple[bool, List[str]]:
        """Validate date format.
        
        Args:
            date_str: Date string to validate
            format_str: Expected date format
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not date_str:
            errors.append("Date cannot be empty")
            return False, errors
        
        try:
            datetime.strptime(date_str, format_str)
        except ValueError:
            errors.append(f"Date must be in format {format_str}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate data against JSON schema.
        
        Args:
            data: Data to validate
            schema: JSON schema to validate against
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            from jsonschema import validate, ValidationError
            validate(instance=data, schema=schema)
            return True, []
        except ImportError:
            logger.warning("jsonschema not available, skipping schema validation")
            return True, []
        except ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Schema validation error: {e}"] 
