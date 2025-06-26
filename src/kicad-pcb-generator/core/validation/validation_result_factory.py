"""Factory for creating validation results."""
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from ..validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    SafetyValidationResult,
    ManufacturingValidationResult
)

@dataclass
class ValidationResultFactory:
    """Factory for creating validation results."""
    
    @staticmethod
    def create_result(category: ValidationCategory, message: str,
                     severity: ValidationSeverity,
                     location: Optional[Tuple[float, float]] = None,
                     details: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """Create a basic validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            
        Returns:
            ValidationResult instance
        """
        return ValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details
        )
    
    @staticmethod
    def create_safety_result(category: ValidationCategory, message: str,
                           severity: ValidationSeverity,
                           location: Optional[Tuple[float, float]] = None,
                           details: Optional[Dict[str, Any]] = None,
                           voltage: Optional[float] = None,
                           current: Optional[float] = None,
                           power: Optional[float] = None,
                           temperature: Optional[float] = None,
                           clearance: Optional[float] = None,
                           creepage: Optional[float] = None) -> SafetyValidationResult:
        """Create a safety validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            voltage: Optional voltage value
            current: Optional current value
            power: Optional power value
            temperature: Optional temperature value
            clearance: Optional clearance value
            creepage: Optional creepage value
            
        Returns:
            SafetyValidationResult instance
        """
        return SafetyValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details,
            voltage=voltage,
            current=current,
            power=power,
            temperature=temperature,
            clearance=clearance,
            creepage=creepage
        )
    
    @staticmethod
    def create_manufacturing_result(category: ValidationCategory, message: str,
                                 severity: ValidationSeverity,
                                 location: Optional[Tuple[float, float]] = None,
                                 details: Optional[Dict[str, Any]] = None,
                                 min_feature_size: Optional[float] = None,
                                 max_feature_size: Optional[float] = None,
                                 recommended_size: Optional[float] = None,
                                 manufacturing_cost: Optional[float] = None,
                                 yield_impact: Optional[float] = None) -> ManufacturingValidationResult:
        """Create a manufacturing validation result.
        
        Args:
            category: Validation category
            message: Validation message
            severity: Validation severity
            location: Optional location tuple (x, y)
            details: Optional details dictionary
            min_feature_size: Optional minimum feature size
            max_feature_size: Optional maximum feature size
            recommended_size: Optional recommended size
            manufacturing_cost: Optional manufacturing cost
            yield_impact: Optional yield impact
            
        Returns:
            ManufacturingValidationResult instance
        """
        return ManufacturingValidationResult(
            category=category,
            message=message,
            severity=severity,
            location=location,
            details=details,
            min_feature_size=min_feature_size,
            max_feature_size=max_feature_size,
            recommended_size=recommended_size,
            manufacturing_cost=manufacturing_cost,
            yield_impact=yield_impact
        ) 