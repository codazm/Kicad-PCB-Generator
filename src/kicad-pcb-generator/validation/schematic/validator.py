"""Unified Audio Schematic Validator for the KiCad PCB Generator."""
import logging
from typing import List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pcbnew
from ...utils.config.settings import Settings
from ...utils.logging.logger import Logger
from ...core.validation.base_validator import BaseValidator, ValidationCategory, ValidationResult

logger = logging.getLogger(__name__)

class AudioSchematicValidator(BaseValidator):
    """Unified validator for audio schematic structures.
    Uses config-driven rules and returns List[ValidationResult].
    """
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[Logger] = None):
        super().__init__(settings, logger)
        self.settings = settings or Settings()
        self.logger = logger or Logger(__name__)

    def validate_schematic(self, schematic: Any, board: Optional[Any] = None) -> List[ValidationResult]:
        """Validate an audio schematic.
        Args:
            schematic: Schematic to validate
            board: Optional board for cross-reference validation
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            # Config-driven rule checks
            if self.settings.is_rule_enabled('general', 'components'):
                results.extend(self._validate_components(schematic))
            if self.settings.is_rule_enabled('general', 'connections'):
                results.extend(self._validate_connections(schematic))
            if self.settings.is_rule_enabled('general', 'power'):
                results.extend(self._validate_power(schematic))
            if self.settings.is_rule_enabled('general', 'ground'):
                results.extend(self._validate_ground(schematic))
            if self.settings.is_rule_enabled('general', 'signal'):
                results.extend(self._validate_signal(schematic))
            if self.settings.is_rule_enabled('general', 'audio'):
                results.extend(self._validate_audio(schematic))
            if self.settings.is_rule_enabled('general', 'manufacturing'):
                results.extend(self._validate_manufacturing(schematic))
            # Optionally, add board cross-reference checks here
            return results
        except (AttributeError, TypeError) as e:
            self.logger.error("Invalid schematic object: %s", str(e))
            results.append(ValidationResult(
                category=ValidationCategory.GENERAL,
                message=f"Invalid schematic object: {str(e)}",
                severity="error"
            ))
            return results
        except Exception as e:
            self.logger.error("Unexpected error during schematic validation: %s", str(e))
            results.append(ValidationResult(
                category=ValidationCategory.GENERAL,
                message=f"Unexpected error during validation: {str(e)}",
                severity="error"
            ))
            return results

    def _validate_components(self, schematic: Any) -> List[ValidationResult]:
        results = []
        try:
            validation_rules = self.settings.get_validation_rules()
            component_rules = validation_rules.get('components', {})
            for component in schematic.GetComponents():
                ref = component.GetReference()
                value = component.GetValue()
                footprint = component.GetFootprint()
                if not value:
                    results.append(ValidationResult(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Component {ref} has no value",
                        severity="warning",
                        location=(component.GetPosition().x, component.GetPosition().y)
                    ))
                if not footprint:
                    results.append(ValidationResult(
                        category=ValidationCategory.COMPONENTS,
                        message=f"Component {ref} has no footprint",
                        severity="error",
                        location=(component.GetPosition().x, component.GetPosition().y)
                    ))
                if any(keyword in ref.upper() for keyword in ["AUDIO", "AMP", "DAC"]):
                    audio_rules = validation_rules.get('audio', {})
                    required_properties = audio_rules.get('required_properties', [])
                    for prop in required_properties:
                        if not component.HasProperty(prop):
                            results.append(ValidationResult(
                                category=ValidationCategory.COMPONENTS,
                                message=f"Audio component {ref} missing required property: {prop}",
                                severity="error",
                                location=(component.GetPosition().x, component.GetPosition().y)
                            ))
        except (AttributeError, TypeError) as e:
            results.append(ValidationResult(
                category=ValidationCategory.COMPONENTS,
                message=f"Invalid component data: {str(e)}",
                severity="error"
            ))
        except Exception as e:
            results.append(ValidationResult(
                category=ValidationCategory.COMPONENTS,
                message=f"Unexpected error validating components: {str(e)}",
                severity="error"
            ))
        return results

    def _validate_connections(self, schematic: Any) -> List[ValidationResult]:
        results = []
        try:
            validation_rules = self.settings.get_validation_rules()
            connection_rules = validation_rules.get('connections', {})
            for wire in schematic.GetWires():
                start = wire.GetStart()
                end = wire.GetEnd()
                length = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
                max_length = connection_rules.get('max_length', 1000)
                if length > max_length:
                    results.append(ValidationResult(
                        category=ValidationCategory.CONNECTIONS,
                        message=f"Wire length {length:.1f} exceeds maximum {max_length}",
                        severity="warning",
                        location=(start.x, start.y)
                    ))
                if not wire.IsConnected():
                    results.append(ValidationResult(
                        category=ValidationCategory.CONNECTIONS,
                        message="Unconnected wire found",
                        severity="error",
                        location=(start.x, start.y)
                    ))
        except (AttributeError, TypeError) as e:
            results.append(ValidationResult(
                category=ValidationCategory.CONNECTIONS,
                message=f"Invalid connection data: {str(e)}",
                severity="error"
            ))
        except Exception as e:
            results.append(ValidationResult(
                category=ValidationCategory.CONNECTIONS,
                message=f"Unexpected error validating connections: {str(e)}",
                severity="error"
            ))
        return results

    def _validate_power(self, schematic: Any) -> List[ValidationResult]:
        results = []
        try:
            validation_rules = self.settings.get_validation_rules()
            power_rules = validation_rules.get('power', {})
            power_nets = []
            for net in schematic.GetNets():
                if any(keyword in net.GetName().upper() for keyword in ["VCC", "VDD", "POWER"]):
                    power_nets.append(net)
            if not power_nets:
                results.append(ValidationResult(
                    category=ValidationCategory.POWER,
                    message="No power nets found",
                    severity="error"
                ))
            for net in power_nets:
                name = net.GetName()
                connections = net.GetConnections()
                has_power_supply = False
                for conn in connections:
                    if any(keyword in conn.GetReference().upper() for keyword in ["POWER", "REG", "SUPPLY"]):
                        has_power_supply = True
                        break
                if not has_power_supply:
                    results.append(ValidationResult(
                        category=ValidationCategory.POWER,
                        message=f"Power net {name} has no power supply component",
                        severity="error"
                    ))
        except (AttributeError, TypeError) as e:
            results.append(ValidationResult(
                category=ValidationCategory.POWER,
                message=f"Invalid power data: {str(e)}",
                severity="error"
            ))
        except Exception as e:
            results.append(ValidationResult(
                category=ValidationCategory.POWER,
                message=f"Unexpected error validating power: {str(e)}",
                severity="error"
            ))
        return results

    def _validate_ground(self, schematic: Any) -> List[ValidationResult]:
        # Implement ground validation logic as needed
        return []

    def _validate_signal(self, schematic: Any) -> List[ValidationResult]:
        # Implement signal validation logic as needed
        return []

    def _validate_audio(self, schematic: Any) -> List[ValidationResult]:
        # Implement audio-specific validation logic as needed
        return []

    def _validate_manufacturing(self, schematic: Any) -> List[ValidationResult]:
        # Implement manufacturing validation logic as needed
        return [] 
