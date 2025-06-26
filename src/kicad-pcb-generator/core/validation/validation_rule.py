"""Validation rule definitions."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from .validation_results import ValidationCategory, ValidationSeverity

class RuleType(Enum):
    """Types of validation rules."""
    DESIGN_RULES = "design_rules"
    COMPONENT_PLACEMENT = "component_placement"
    ROUTING = "routing"
    MANUFACTURING = "manufacturing"
    POWER = "power"
    GROUND = "ground"
    SIGNAL = "signal"
    AUDIO = "audio"

@dataclass
class ValidationRule:
    """A validation rule with its parameters and thresholds."""
    
    rule_type: RuleType
    category: ValidationCategory
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.WARNING
    
    def __post_init__(self):
        """Set default parameters and thresholds based on rule type."""
        if self.rule_type == RuleType.DESIGN_RULES:
            self.parameters.update({
                "min_track_width": 0.1,  # mm
                "min_via_size": 0.2,  # mm
                "min_clearance": 0.1,  # mm
                "max_via_count": 1000
            })
        elif self.rule_type == RuleType.COMPONENT_PLACEMENT:
            self.parameters.update({
                "min_spacing": 0.5,  # mm
                "edge_clearance": 1.0,  # mm
                "max_rotation": 45.0  # degrees
            })
        elif self.rule_type == RuleType.ROUTING:
            self.parameters.update({
                "min_track_width": 0.1,  # mm
                "max_track_width": 5.0,  # mm
                "min_via_size": 0.2,  # mm
                "max_via_size": 1.0,  # mm
                "min_clearance": 0.1,  # mm
                "max_length": 100.0  # mm
            })
        elif self.rule_type == RuleType.MANUFACTURING:
            self.parameters.update({
                "min_feature_size": 0.1,  # mm
                "max_board_size": 300.0,  # mm
                "min_annular_ring": 0.1,  # mm
                "min_drill_size": 0.2  # mm
            })
        elif self.rule_type == RuleType.POWER:
            self.parameters.update({
                "max_voltage_drop": 0.1,  # V
                "max_current_density": 20.0,  # A/mm²
                "min_trace_width": 0.3,  # mm
                "max_trace_width": 5.0  # mm
            })
        elif self.rule_type == RuleType.GROUND:
            self.parameters.update({
                "max_loop_area": 100.0,  # mm²
                "min_ground_area": 0.5,  # ratio
                "max_impedance": 0.1  # ohms
            })
        elif self.rule_type == RuleType.SIGNAL:
            self.parameters.update({
                "max_crosstalk": 0.1,  # ratio
                "max_reflection": 0.1,  # ratio
                "min_impedance": 45.0,  # ohms
                "max_impedance": 55.0  # ohms
            })
        elif self.rule_type == RuleType.AUDIO:
            self.parameters.update({
                "min_trace_width": 0.3,  # mm
                "max_trace_width": 1.0,  # mm
                "min_spacing": 0.3,  # mm
                "max_length": 100.0,  # mm
                "target_impedance": 50.0  # ohms
            })
    
    def check_threshold(self, value: float, threshold_name: str) -> bool:
        """Check if a value exceeds a threshold.
        
        Args:
            value: Value to check
            threshold_name: Name of threshold parameter
            
        Returns:
            True if value exceeds threshold, False otherwise
        """
        if threshold_name not in self.thresholds:
            return False
        
        threshold = self.thresholds[threshold_name]
        return value > threshold
    
    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Get a parameter value.
        
        Args:
            name: Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default
        """
        return self.parameters.get(name, default)
    
    def set_parameter(self, name: str, value: Any) -> None:
        """Set a parameter value.
        
        Args:
            name: Parameter name
            value: Parameter value
        """
        self.parameters[name] = value
    
    def set_threshold(self, name: str, value: float) -> None:
        """Set a threshold value.
        
        Args:
            name: Threshold name
            value: Threshold value
        """
        self.thresholds[name] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary.
        
        Returns:
            Dictionary representation of rule
        """
        return {
            "rule_type": self.rule_type.value,
            "category": self.category.value,
            "enabled": self.enabled,
            "parameters": self.parameters,
            "thresholds": self.thresholds,
            "severity": self.severity.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationRule':
        """Create rule from dictionary.
        
        Args:
            data: Dictionary representation of rule
            
        Returns:
            ValidationRule instance
        """
        return cls(
            rule_type=RuleType(data["rule_type"]),
            category=ValidationCategory(data["category"]),
            enabled=data["enabled"],
            parameters=data["parameters"],
            thresholds=data["thresholds"],
            severity=ValidationSeverity(data["severity"])
        ) 