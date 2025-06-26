"""Validation result classes for the KiCad PCB Generator."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from ...utils.error_handling import (
    ValidationError,
    ComponentError,
    ConnectionError,
    PowerError,
    GroundError,
    SignalError,
    AudioError,
    ManufacturingError,
    create_validation_result
)

class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationCategory(str, Enum):
    """Validation categories."""
    DESIGN_RULES = "design_rules"
    COMPONENT_PLACEMENT = "component_placement"
    ROUTING = "routing"
    AUDIO_SPECIFIC = "audio_specific"
    MANUFACTURING = "manufacturing"
    POWER = "power"
    GROUND = "ground"
    SIGNAL = "signal"

@dataclass
class ValidationResult:
    """Base class for validation results."""
    category: ValidationCategory
    message: str
    severity: ValidationSeverity
    location: Optional[Tuple[float, float]] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        return create_validation_result(
            category=self.category.value,
            message=self.message,
            severity=self.severity.value,
            location=self.location,
            details=self.details
        )

    def to_error(self) -> ValidationError:
        """Convert to validation error.
        
        Returns:
            ValidationError instance
        """
        error_map = {
            ValidationCategory.DESIGN_RULES: ValidationError,
            ValidationCategory.COMPONENT_PLACEMENT: ComponentError,
            ValidationCategory.ROUTING: ConnectionError,
            ValidationCategory.AUDIO_SPECIFIC: AudioError,
            ValidationCategory.MANUFACTURING: ManufacturingError,
            ValidationCategory.POWER: PowerError,
            ValidationCategory.GROUND: GroundError,
            ValidationCategory.SIGNAL: SignalError
        }
        
        error_class = error_map.get(self.category, ValidationError)
        return error_class(
            message=self.message,
            category=self.category.value,
            details=self.details
        )

@dataclass
class AudioValidationResult(ValidationResult):
    """Audio-specific validation result."""
    frequency: Optional[float] = None
    impedance: Optional[float] = None
    crosstalk: Optional[float] = None
    noise_level: Optional[float] = None
    power_quality: Optional[float] = None
    thermal_impact: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        if self.frequency is not None:
            result[self.category.value][0]["frequency"] = self.frequency
        if self.impedance is not None:
            result[self.category.value][0]["impedance"] = self.impedance
        if self.crosstalk is not None:
            result[self.category.value][0]["crosstalk"] = self.crosstalk
        if self.noise_level is not None:
            result[self.category.value][0]["noise_level"] = self.noise_level
        if self.power_quality is not None:
            result[self.category.value][0]["power_quality"] = self.power_quality
        if self.thermal_impact is not None:
            result[self.category.value][0]["thermal_impact"] = self.thermal_impact
        return result

@dataclass
class SafetyValidationResult(ValidationResult):
    """Safety-related validation result."""
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    temperature: Optional[float] = None
    clearance: Optional[float] = None
    creepage: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        if self.voltage is not None:
            result[self.category.value][0]["voltage"] = self.voltage
        if self.current is not None:
            result[self.category.value][0]["current"] = self.current
        if self.power is not None:
            result[self.category.value][0]["power"] = self.power
        if self.temperature is not None:
            result[self.category.value][0]["temperature"] = self.temperature
        if self.clearance is not None:
            result[self.category.value][0]["clearance"] = self.clearance
        if self.creepage is not None:
            result[self.category.value][0]["creepage"] = self.creepage
        return result

@dataclass
class ManufacturingValidationResult(ValidationResult):
    """Manufacturing-related validation result."""
    min_feature_size: Optional[float] = None
    max_feature_size: Optional[float] = None
    recommended_size: Optional[float] = None
    manufacturing_cost: Optional[float] = None
    yield_impact: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = super().to_dict()
        if self.min_feature_size is not None:
            result[self.category.value][0]["min_feature_size"] = self.min_feature_size
        if self.max_feature_size is not None:
            result[self.category.value][0]["max_feature_size"] = self.max_feature_size
        if self.recommended_size is not None:
            result[self.category.value][0]["recommended_size"] = self.recommended_size
        if self.manufacturing_cost is not None:
            result[self.category.value][0]["manufacturing_cost"] = self.manufacturing_cost
        if self.yield_impact is not None:
            result[self.category.value][0]["yield_impact"] = self.yield_impact
        return result 