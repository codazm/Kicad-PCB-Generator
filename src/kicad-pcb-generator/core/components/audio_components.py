"""Audio-specific component types and validation for KiCad PCB Generator."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .manager import ComponentData, ComponentType
from ..compatibility.kicad9 import KiCad9Compatibility
from ..validation.base_validator import BaseValidator, ValidationResult, ValidationCategory, ValidationSeverity

class AudioComponentType(Enum):
    """Audio-specific component types."""
    # Active Components
    OPAMP = "opamp"
    AUDIO_IC = "audio_ic"
    TRANSISTOR = "transistor"
    TUBE = "tube"
    
    # Passive Components
    AUDIO_CAPACITOR = "audio_capacitor"
    AUDIO_RESISTOR = "audio_resistor"
    AUDIO_INDUCTOR = "audio_inductor"
    AUDIO_TRANSFORMER = "audio_transformer"
    
    # Controls
    POTENTIOMETER = "potentiometer"
    SWITCH = "switch"
    ROTARY_ENCODER = "rotary_encoder"
    
    # Connectors
    JACK = "jack"
    XLR = "xlr"
    MIDI = "midi"
    USB = "usb"
    
    # Indicators
    LED = "led"
    VU_METER = "vu_meter"
    
    # Power
    VOLTAGE_REGULATOR = "voltage_regulator"
    POWER_SUPPLY = "power_supply"
    
    # Other
    CRYSTAL = "crystal"
    OSCILLATOR = "oscillator"
    OTHER = "other"

class AudioComponentCategory(Enum):
    """Categories for audio components."""
    ACTIVE = "active"
    PASSIVE = "passive"
    CONTROL = "control"
    CONNECTOR = "connector"
    INDICATOR = "indicator"
    POWER = "power"
    OTHER = "other"

@dataclass
class AudioComponentData(ComponentData):
    """Audio-specific component data structure."""
    audio_type: AudioComponentType
    audio_category: AudioComponentCategory
    audio_properties: Dict[str, Any] = field(default_factory=dict)
    noise_characteristics: Dict[str, float] = field(default_factory=dict)
    frequency_response: Dict[str, float] = field(default_factory=dict)
    power_requirements: Dict[str, float] = field(default_factory=dict)
    signal_characteristics: Dict[str, float] = field(default_factory=dict)
    thermal_characteristics: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values and validate."""
        super().__post_init__()
        self._validate_audio_properties()

    def _validate_audio_properties(self) -> None:
        """Validate audio-specific properties.
        
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(self.audio_type, AudioComponentType):
            raise ValueError("Invalid audio component type")
        
        if not isinstance(self.audio_category, AudioComponentCategory):
            raise ValueError("Invalid audio component category")

        # Validate noise characteristics
        if "noise_floor" in self.noise_characteristics:
            if not isinstance(self.noise_characteristics["noise_floor"], (int, float)):
                raise ValueError("Noise floor must be numeric")
            if self.noise_characteristics["noise_floor"] < 0:
                raise ValueError("Noise floor cannot be negative")

        # Validate frequency response
        if "min_frequency" in self.frequency_response:
            if not isinstance(self.frequency_response["min_frequency"], (int, float)):
                raise ValueError("Minimum frequency must be numeric")
            if self.frequency_response["min_frequency"] < 0:
                raise ValueError("Minimum frequency cannot be negative")
        
        if "max_frequency" in self.frequency_response:
            if not isinstance(self.frequency_response["max_frequency"], (int, float)):
                raise ValueError("Maximum frequency must be numeric")
            if self.frequency_response["max_frequency"] < 0:
                raise ValueError("Maximum frequency cannot be negative")
            if "min_frequency" in self.frequency_response:
                if self.frequency_response["max_frequency"] < self.frequency_response["min_frequency"]:
                    raise ValueError("Maximum frequency must be greater than minimum frequency")

        # Validate power requirements
        if "voltage" in self.power_requirements:
            if not isinstance(self.power_requirements["voltage"], (int, float)):
                raise ValueError("Voltage must be numeric")
            if self.power_requirements["voltage"] < 0:
                raise ValueError("Voltage cannot be negative")
        
        if "current" in self.power_requirements:
            if not isinstance(self.power_requirements["current"], (int, float)):
                raise ValueError("Current must be numeric")
            if self.power_requirements["current"] < 0:
                raise ValueError("Current cannot be negative")

        # Validate signal characteristics
        if "impedance" in self.signal_characteristics:
            if not isinstance(self.signal_characteristics["impedance"], (int, float)):
                raise ValueError("Impedance must be numeric")
            if self.signal_characteristics["impedance"] < 0:
                raise ValueError("Impedance cannot be negative")
        
        if "gain" in self.signal_characteristics:
            if not isinstance(self.signal_characteristics["gain"], (int, float)):
                raise ValueError("Gain must be numeric")

        # Validate thermal characteristics
        if "max_temperature" in self.thermal_characteristics:
            if not isinstance(self.thermal_characteristics["max_temperature"], (int, float)):
                raise ValueError("Maximum temperature must be numeric")
            if self.thermal_characteristics["max_temperature"] < 0:
                raise ValueError("Maximum temperature cannot be negative")

class AudioComponentValidator(BaseValidator):
    """Validator for audio-specific components."""

    def __init__(self, kicad: KiCad9Compatibility, logger=None):
        """Initialize audio component validator.
        
        Args:
            kicad: KiCad compatibility layer
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.kicad = kicad

    def _validate_audio_specific(self) -> List[ValidationResult]:
        """Validate audio-specific rules.
        
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = self.kicad.get_board()
            if not board:
                return results

            for footprint in board.GetFootprints():
                # Get component data
                component_data = self._get_component_data(footprint)
                if not component_data:
                    continue

                # Validate audio-specific properties
                if isinstance(component_data, AudioComponentData):
                    results.extend(self._validate_audio_component(component_data, footprint))

        except Exception as e:
            self.logger.error(f"Error during audio validation: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.AUDIO,
                message=f"Error during audio validation: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _validate_audio_component(
        self,
        component: AudioComponentData,
        footprint: Any
    ) -> List[ValidationResult]:
        """Validate audio component.
        
        Args:
            component: Audio component data
            footprint: KiCad footprint
            
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []

        # Validate noise characteristics
        if "noise_floor" in component.noise_characteristics:
            if component.noise_characteristics["noise_floor"] > -60:  # -60 dB is typical for audio
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High noise floor for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    noise_level=component.noise_characteristics["noise_floor"]
                ))

        # Validate frequency response
        if "min_frequency" in component.frequency_response:
            if component.frequency_response["min_frequency"] > 20:  # 20 Hz is typical minimum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High minimum frequency for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    frequency=component.frequency_response["min_frequency"]
                ))
        
        if "max_frequency" in component.frequency_response:
            if component.frequency_response["max_frequency"] < 20000:  # 20 kHz is typical maximum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"Low maximum frequency for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    frequency=component.frequency_response["max_frequency"]
                ))

        # Validate power requirements
        if "voltage" in component.power_requirements:
            if component.power_requirements["voltage"] > 15:  # 15V is typical maximum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High voltage requirement for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    power_quality=component.power_requirements["voltage"]
                ))
        
        if "current" in component.power_requirements:
            if component.power_requirements["current"] > 0.1:  # 100mA is typical maximum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High current requirement for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    power_quality=component.power_requirements["current"]
                ))

        # Validate signal characteristics
        if "impedance" in component.signal_characteristics:
            if component.signal_characteristics["impedance"] < 100:  # 100 ohms is typical minimum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"Low impedance for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    impedance=component.signal_characteristics["impedance"]
                ))
        
        if "gain" in component.signal_characteristics:
            if component.signal_characteristics["gain"] > 40:  # 40 dB is typical maximum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High gain for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    impedance=component.signal_characteristics["gain"]
                ))

        # Validate thermal characteristics
        if "max_temperature" in component.thermal_characteristics:
            if component.thermal_characteristics["max_temperature"] > 85:  # 85°C is typical maximum
                results.append(self._create_audio_result(
                    category=ValidationCategory.AUDIO,
                    message=f"High maximum temperature for {component.id}",
                    severity=ValidationSeverity.WARNING,
                    location=self._get_footprint_position(footprint),
                    thermal_impact=component.thermal_characteristics["max_temperature"]
                ))

        return results

    def _get_component_data(self, footprint: Any) -> Optional[ComponentData]:
        """Get component data from footprint.
        
        Args:
            footprint: KiCad footprint
            
        Returns:
            Component data if available
        """
        try:
            # Get component reference
            ref = footprint.GetReference()
            
            # Get component value
            value = footprint.GetValue()
            
            # Get component type from value
            component_type = self._get_component_type(value)
            
            # Create component data
            return ComponentData(
                id=ref,
                type=component_type.value,
                value=value,
                footprint=footprint.GetFPID().GetLibItemName().wx_str(),
                position=self._get_footprint_position(footprint),
                orientation=footprint.GetOrientationDegrees(),
                layer=footprint.GetLayerName()
            )
        except Exception as e:
            self.logger.error(f"Error getting component data: {str(e)}")
            return None

    def _get_component_type(self, value: str) -> ComponentType:
        """Get component type from value.
        
        Args:
            value: Component value
            
        Returns:
            Component type
        """
        value = value.lower()
        if "op" in value or "amp" in value:
            return AudioComponentType.OPAMP
        elif "ic" in value:
            return AudioComponentType.AUDIO_IC
        elif "trans" in value:
            if "tube" in value:
                return AudioComponentType.TUBE
            elif "audio" in value:
                return AudioComponentType.AUDIO_TRANSFORMER
            else:
                return AudioComponentType.TRANSISTOR
        elif "cap" in value:
            return AudioComponentType.AUDIO_CAPACITOR
        elif "res" in value:
            return AudioComponentType.AUDIO_RESISTOR
        elif "ind" in value:
            return AudioComponentType.AUDIO_INDUCTOR
        elif "pot" in value:
            return AudioComponentType.POTENTIOMETER
        elif "sw" in value:
            return AudioComponentType.SWITCH
        elif "enc" in value:
            return AudioComponentType.ROTARY_ENCODER
        elif "jack" in value:
            return AudioComponentType.JACK
        elif "xlr" in value:
            return AudioComponentType.XLR
        elif "midi" in value:
            return AudioComponentType.MIDI
        elif "usb" in value:
            return AudioComponentType.USB
        elif "led" in value:
            return AudioComponentType.LED
        elif "vu" in value:
            return AudioComponentType.VU_METER
        elif "reg" in value:
            return AudioComponentType.VOLTAGE_REGULATOR
        elif "psu" in value or "power" in value:
            return AudioComponentType.POWER_SUPPLY
        elif "xtal" in value or "crystal" in value:
            return AudioComponentType.CRYSTAL
        elif "osc" in value:
            return AudioComponentType.OSCILLATOR
        else:
            return ComponentType.OTHER

    def _get_footprint_position(self, footprint: Any) -> Tuple[float, float]:
        """Get footprint position in millimeters.
        
        Args:
            footprint: KiCad footprint
            
        Returns:
            (x, y) position in millimeters
        """
        pos = footprint.GetPosition()
        return (pos.x/1e6, pos.y/1e6) 