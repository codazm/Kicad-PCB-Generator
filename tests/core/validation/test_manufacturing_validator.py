"""
Tests for manufacturing validator.
"""
import pytest
from typing import Dict, Any

from ....src.core.validation.manufacturing_validator import ManufacturingValidator
from ....src.core.validation.validation_rule import ValidationRule, TestCase
from ....src.core.validation.validation_results import (
    ValidationCategory,
    ValidationSeverity
)

@pytest.fixture
def validator() -> ManufacturingValidator:
    """Create manufacturing validator.
    
    Returns:
        Manufacturing validator instance
    """
    return ManufacturingValidator()
    
@pytest.fixture
def board_data() -> Dict[str, Any]:
    """Create test board data.
    
    Returns:
        Dictionary containing board data
    """
    return {
        "board_size": {
            "width": 100,
            "height": 100
        },
        "drill_sizes": [0.3, 0.4, 0.5],
        "trace_widths": [0.2, 0.3, 0.4],
        "min_spacing": 0.2,
        "min_annular_ring": 0.15
    }
    
def test_board_size_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test board size validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 150},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_drill_size_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test drill size validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Min Drill Size",
        description="Check minimum drill size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Min Drill Check",
                description="Check drill sizes against minimum",
                input_data={"min_drill": 0.25},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_trace_width_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test trace width validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Min Trace Width",
        description="Check minimum trace width",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Min Trace Check",
                description="Check trace widths against minimum",
                input_data={"min_trace": 0.15},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_spacing_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test spacing validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Min Spacing",
        description="Check minimum spacing",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Min Spacing Check",
                description="Check spacing against minimum",
                input_data={"min_spacing": 0.15},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_annular_ring_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test annular ring validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Min Annular Ring",
        description="Check minimum annular ring",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Min Annular Check",
                description="Check annular ring against minimum",
                input_data={"min_annular": 0.1},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_multiple_rules(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test multiple rules.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rules
    rules = [
        ValidationRule(
            name="Max Board Size",
            description="Check maximum board size",
            category=ValidationCategory.MANUFACTURING,
            severity=ValidationSeverity.ERROR,
            test_cases=[
                TestCase(
                    name="Max Size Check",
                    description="Check board size against maximum",
                    input_data={"max_size": 150},
                    expected_result=True
                )
            ]
        ),
        ValidationRule(
            name="Min Drill Size",
            description="Check minimum drill size",
            category=ValidationCategory.MANUFACTURING,
            severity=ValidationSeverity.ERROR,
            test_cases=[
                TestCase(
                    name="Min Drill Check",
                    description="Check drill sizes against minimum",
                    input_data={"min_drill": 0.25},
                    expected_result=True
                )
            ]
        )
    ]
    
    # Add rules
    for rule in rules:
        validator.add_rule(rule)
        
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_failing_validation(validator: ManufacturingValidator, board_data: Dict[str, Any]) -> None:
    """Test failing validation.
    
    Args:
        validator: Manufacturing validator
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 50},
                expected_result=False
            )
        ]
    )
    
    # Add rule
    validator.add_rule(rule)
    
    # Validate
    result = validator.validate(board_data)
    
    # Check result
    assert not result.passed
    assert result.has_errors
    assert not result.has_warnings
    assert result.error_count == 1 