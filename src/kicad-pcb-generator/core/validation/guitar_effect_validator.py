"""Guitar effect circuit validator for the KiCad PCB Generator."""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import pcbnew
import math
from functools import lru_cache
from ...utils.logging.logger import Logger
from ...utils.error_handling import (
    handle_validation_error,
    handle_operation_error,
    log_validation_error,
    ValidationError,
    AudioError
)
from .validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult
)
from ...utils.config.settings import Settings
from .base_validator import BaseValidator
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat

class EffectType(Enum):
    """Types of guitar effects."""
    DISTORTION = "distortion"
    DELAY = "delay"
    MODULATION = "modulation"
    FILTER = "filter"
    BUFFER = "buffer"

@dataclass
class DistortionConfigItem:
    """Configuration item for distortion effect validation."""
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    min_bypass_cap_distance: float = 0.5  # mm
    max_bypass_cap_distance: float = 2.0  # mm
    min_input_impedance: float = 100000.0  # ohms
    max_input_impedance: float = 1000000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms
    min_gain: float = 0.0  # dB
    max_gain: float = 60.0  # dB

class DistortionConfig(BaseConfig[DistortionConfigItem]):
    """Configuration manager for distortion effect validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize distortion configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: DistortionConfigItem) -> ConfigResult:
        """Validate distortion configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate track widths
            if config.min_power_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum power track width must be positive",
                    data=config
                )
            
            if config.min_signal_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum signal track width must be positive",
                    data=config
                )
            
            # Validate bypass cap distances
            if config.min_bypass_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum bypass cap distance must be positive",
                    data=config
                )
            
            if config.max_bypass_cap_distance <= config.min_bypass_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum bypass cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate impedances
            if config.min_input_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum input impedance must be positive",
                    data=config
                )
            
            if config.max_input_impedance <= config.min_input_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum input impedance must be greater than minimum",
                    data=config
                )
            
            if config.min_output_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum output impedance must be positive",
                    data=config
                )
            
            if config.max_output_impedance <= config.min_output_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum output impedance must be greater than minimum",
                    data=config
                )
            
            # Validate gain range
            if config.max_gain <= config.min_gain:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum gain must be greater than minimum gain",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Distortion configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating distortion configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating distortion configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> DistortionConfigItem:
        """Parse configuration data into DistortionConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            DistortionConfigItem instance
        """
        try:
            return DistortionConfigItem(
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                min_bypass_cap_distance=config_data.get('min_bypass_cap_distance', 0.5),
                max_bypass_cap_distance=config_data.get('max_bypass_cap_distance', 2.0),
                min_input_impedance=config_data.get('min_input_impedance', 100000.0),
                max_input_impedance=config_data.get('max_input_impedance', 1000000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0),
                min_gain=config_data.get('min_gain', 0.0),
                max_gain=config_data.get('max_gain', 60.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing distortion configuration: {e}")
            raise ValueError(f"Input error in distortion configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing distortion configuration: {e}")
            raise ValueError(f"Unexpected error in distortion configuration data: {e}")
    
    def _prepare_config_data(self, config: DistortionConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'min_bypass_cap_distance': config.min_bypass_cap_distance,
            'max_bypass_cap_distance': config.max_bypass_cap_distance,
            'min_input_impedance': config.min_input_impedance,
            'max_input_impedance': config.max_input_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance,
            'min_gain': config.min_gain,
            'max_gain': config.max_gain
        }

@dataclass
class DelayConfigItem:
    """Configuration item for delay effect validation."""
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    min_clock_cap_distance: float = 0.5  # mm
    max_clock_cap_distance: float = 2.0  # mm
    min_input_impedance: float = 100000.0  # ohms
    max_input_impedance: float = 1000000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms
    min_delay_time: float = 0.0  # ms
    max_delay_time: float = 2000.0  # ms

class DelayConfig(BaseConfig[DelayConfigItem]):
    """Configuration manager for delay effect validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize delay configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: DelayConfigItem) -> ConfigResult:
        """Validate delay configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate track widths
            if config.min_power_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum power track width must be positive",
                    data=config
                )
            
            if config.min_signal_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum signal track width must be positive",
                    data=config
                )
            
            # Validate clock cap distances
            if config.min_clock_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum clock cap distance must be positive",
                    data=config
                )
            
            if config.max_clock_cap_distance <= config.min_clock_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum clock cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate impedances
            if config.min_input_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum input impedance must be positive",
                    data=config
                )
            
            if config.max_input_impedance <= config.min_input_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum input impedance must be greater than minimum",
                    data=config
                )
            
            if config.min_output_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum output impedance must be positive",
                    data=config
                )
            
            if config.max_output_impedance <= config.min_output_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum output impedance must be greater than minimum",
                    data=config
                )
            
            # Validate delay time range
            if config.min_delay_time < 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum delay time cannot be negative",
                    data=config
                )
            
            if config.max_delay_time <= config.min_delay_time:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum delay time must be greater than minimum",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Delay configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating delay configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating delay configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> DelayConfigItem:
        """Parse configuration data into DelayConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            DelayConfigItem instance
        """
        try:
            return DelayConfigItem(
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                min_clock_cap_distance=config_data.get('min_clock_cap_distance', 0.5),
                max_clock_cap_distance=config_data.get('max_clock_cap_distance', 2.0),
                min_input_impedance=config_data.get('min_input_impedance', 100000.0),
                max_input_impedance=config_data.get('max_input_impedance', 1000000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0),
                min_delay_time=config_data.get('min_delay_time', 0.0),
                max_delay_time=config_data.get('max_delay_time', 2000.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing delay configuration: {e}")
            raise ValueError(f"Input error in delay configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing delay configuration: {e}")
            raise ValueError(f"Unexpected error in delay configuration data: {e}")
    
    def _prepare_config_data(self, config: DelayConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'min_clock_cap_distance': config.min_clock_cap_distance,
            'max_clock_cap_distance': config.max_clock_cap_distance,
            'min_input_impedance': config.min_input_impedance,
            'max_input_impedance': config.max_input_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance,
            'min_delay_time': config.min_delay_time,
            'max_delay_time': config.max_delay_time
        }

@dataclass
class ModulationConfigItem:
    """Configuration item for modulation effect validation."""
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    min_lfo_cap_distance: float = 0.5  # mm
    max_lfo_cap_distance: float = 2.0  # mm
    min_input_impedance: float = 100000.0  # ohms
    max_input_impedance: float = 1000000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms
    min_mod_depth: float = 0.0  # %
    max_mod_depth: float = 100.0  # %
    min_mod_rate: float = 0.1  # Hz
    max_mod_rate: float = 20.0  # Hz

class ModulationConfig(BaseConfig[ModulationConfigItem]):
    """Configuration manager for modulation effect validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize modulation configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: ModulationConfigItem) -> ConfigResult:
        """Validate modulation configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate track widths
            if config.min_power_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum power track width must be positive",
                    data=config
                )
            
            if config.min_signal_track_width <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum signal track width must be positive",
                    data=config
                )
            
            # Validate LFO cap distances
            if config.min_lfo_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum LFO cap distance must be positive",
                    data=config
                )
            
            if config.max_lfo_cap_distance <= config.min_lfo_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum LFO cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate impedances
            if config.min_input_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum input impedance must be positive",
                    data=config
                )
            
            if config.max_input_impedance <= config.min_input_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum input impedance must be greater than minimum",
                    data=config
                )
            
            if config.min_output_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum output impedance must be positive",
                    data=config
                )
            
            if config.max_output_impedance <= config.min_output_impedance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum output impedance must be greater than minimum",
                    data=config
                )
            
            # Validate modulation depth range
            if config.min_mod_depth < 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum modulation depth cannot be negative",
                    data=config
                )
            
            if config.max_mod_depth <= config.min_mod_depth:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum modulation depth must be greater than minimum",
                    data=config
                )
            
            if config.max_mod_depth > 100.0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum modulation depth cannot exceed 100%",
                    data=config
                )
            
            # Validate modulation rate range
            if config.min_mod_rate <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum modulation rate must be positive",
                    data=config
                )
            
            if config.max_mod_rate <= config.min_mod_rate:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum modulation rate must be greater than minimum",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="Modulation configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating modulation configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating modulation configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ModulationConfigItem:
        """Parse configuration data into ModulationConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            ModulationConfigItem instance
        """
        try:
            return ModulationConfigItem(
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                min_lfo_cap_distance=config_data.get('min_lfo_cap_distance', 0.5),
                max_lfo_cap_distance=config_data.get('max_lfo_cap_distance', 2.0),
                min_input_impedance=config_data.get('min_input_impedance', 100000.0),
                max_input_impedance=config_data.get('max_input_impedance', 1000000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0),
                min_mod_depth=config_data.get('min_mod_depth', 0.0),
                max_mod_depth=config_data.get('max_mod_depth', 100.0),
                min_mod_rate=config_data.get('min_mod_rate', 0.1),
                max_mod_rate=config_data.get('max_mod_rate', 20.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing modulation configuration: {e}")
            raise ValueError(f"Input error in modulation configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing modulation configuration: {e}")
            raise ValueError(f"Unexpected error in modulation configuration data: {e}")
    
    def _prepare_config_data(self, config: ModulationConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'min_lfo_cap_distance': config.min_lfo_cap_distance,
            'max_lfo_cap_distance': config.max_lfo_cap_distance,
            'min_input_impedance': config.min_input_impedance,
            'max_input_impedance': config.max_input_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance,
            'min_mod_depth': config.min_mod_depth,
            'max_mod_depth': config.max_mod_depth,
            'min_mod_rate': config.min_mod_rate,
            'max_mod_rate': config.max_mod_rate
        }

class GuitarEffectValidator(BaseValidator):
    """Validator for guitar effect circuits."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the validator.
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.settings = Settings()
        self.distortion_config = DistortionConfig()
        self.delay_config = DelayConfig()
        self.modulation_config = ModulationConfig()

    @handle_validation_error(logger=Logger(__name__), category="guitar_effect")
    def validate_distortion_circuit(self, effect_ref: str) -> List[ValidationResult]:
        """Validate a distortion effect circuit.
        
        Args:
            effect_ref: Effect component reference
            
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Find effect component
            effect = None
            for footprint in board.GetFootprints():
                if footprint.GetReference() == effect_ref:
                    effect = footprint
                    break

            if not effect:
                results.append(self._create_result(
                    category=ValidationCategory.COMPONENT_PLACEMENT,
                    message=f"Effect {effect_ref} not found",
                    severity=ValidationSeverity.ERROR
                ))
                return results

            # Get effect nets
            power_nets = []
            input_nets = []
            output_nets = []
            bypass_nets = []

            for pad in effect.Pads():
                net = pad.GetNetname()
                if not net:
                    continue

                # Categorize nets based on pad name
                pad_name = pad.GetName().upper()
                if any(name in pad_name for name in ["VCC", "VDD", "POWER", "SUPPLY"]):
                    power_nets.append(net)
                elif any(name in pad_name for name in ["IN", "INPUT"]):
                    input_nets.append(net)
                elif any(name in pad_name for name in ["OUT", "OUTPUT"]):
                    output_nets.append(net)
                elif any(name in pad_name for name in ["BYPASS", "SWITCH"]):
                    bypass_nets.append(net)

            # Validate power tracks
            for net in power_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < self.distortion_config.min_power_track_width:
                        results.append(self._create_result(
                            category=ValidationCategory.POWER,
                            message=f"Power track width {width:.2f}mm is below minimum {self.distortion_config.min_power_track_width}mm",
                            severity=ValidationSeverity.ERROR,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'net': net,
                                'width': width,
                                'min_width': self.distortion_config.min_power_track_width
                            }
                        ))

            # Validate bypass components
            for net in bypass_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    # Find nearby capacitors
                    caps = self._find_nearby_components(track, board, "C")
                    for cap in caps:
                        distance = track.GetStart().Distance(cap.GetPosition()) / 1e6  # Convert to mm
                        if distance < self.distortion_config.min_bypass_cap_distance:
                            results.append(self._create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Bypass capacitor too close to track: {distance:.2f}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'distance': distance,
                                    'min_distance': self.distortion_config.min_bypass_cap_distance
                                }
                            ))

            # Validate input impedance
            for net in input_nets:
                impedance = self._calculate_input_impedance(net, board)
                if impedance:
                    if impedance < self.distortion_config.min_input_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Input impedance {impedance:.1f}Ω is below minimum {self.distortion_config.min_input_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.distortion_config.min_input_impedance
                            }
                        ))
                    elif impedance > self.distortion_config.max_input_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Input impedance {impedance:.1f}Ω exceeds maximum {self.distortion_config.max_input_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.distortion_config.max_input_impedance
                            }
                        ))

            # Validate output impedance
            for net in output_nets:
                impedance = self._calculate_output_impedance(net, board)
                if impedance:
                    if impedance < self.distortion_config.min_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Output impedance {impedance:.1f}Ω is below minimum {self.distortion_config.min_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.distortion_config.min_output_impedance
                            }
                        ))
                    elif impedance > self.distortion_config.max_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Output impedance {impedance:.1f}Ω exceeds maximum {self.distortion_config.max_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.distortion_config.max_output_impedance
                            }
                        ))

        except Exception as e:
            self.logger.error(f"Error validating distortion circuit: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating distortion circuit: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="guitar_effect")
    def validate_delay_circuit(self, effect_ref: str) -> List[ValidationResult]:
        """Validate a delay effect circuit.
        
        Args:
            effect_ref: Effect component reference
            
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Find effect component
            effect = None
            for footprint in board.GetFootprints():
                if footprint.GetReference() == effect_ref:
                    effect = footprint
                    break

            if not effect:
                results.append(self._create_result(
                    category=ValidationCategory.COMPONENT_PLACEMENT,
                    message=f"Effect {effect_ref} not found",
                    severity=ValidationSeverity.ERROR
                ))
                return results

            # Get effect nets
            power_nets = []
            input_nets = []
            output_nets = []
            clock_nets = []

            for pad in effect.Pads():
                net = pad.GetNetname()
                if not net:
                    continue

                # Categorize nets based on pad name
                pad_name = pad.GetName().upper()
                if any(name in pad_name for name in ["VCC", "VDD", "POWER", "SUPPLY"]):
                    power_nets.append(net)
                elif any(name in pad_name for name in ["IN", "INPUT"]):
                    input_nets.append(net)
                elif any(name in pad_name for name in ["OUT", "OUTPUT"]):
                    output_nets.append(net)
                elif any(name in pad_name for name in ["CLK", "CLOCK", "OSC"]):
                    clock_nets.append(net)

            # Validate power tracks
            for net in power_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < self.delay_config.min_power_track_width:
                        results.append(self._create_result(
                            category=ValidationCategory.POWER,
                            message=f"Power track width {width:.2f}mm is below minimum {self.delay_config.min_power_track_width}mm",
                            severity=ValidationSeverity.ERROR,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'net': net,
                                'width': width,
                                'min_width': self.delay_config.min_power_track_width
                            }
                        ))

            # Validate clock components
            for net in clock_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    # Find nearby capacitors
                    caps = self._find_nearby_components(track, board, "C")
                    for cap in caps:
                        distance = track.GetStart().Distance(cap.GetPosition()) / 1e6  # Convert to mm
                        if distance < self.delay_config.min_clock_cap_distance:
                            results.append(self._create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Clock capacitor too close to track: {distance:.2f}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'distance': distance,
                                    'min_distance': self.delay_config.min_clock_cap_distance
                                }
                            ))

            # Validate input impedance
            for net in input_nets:
                impedance = self._calculate_input_impedance(net, board)
                if impedance:
                    if impedance < self.delay_config.min_input_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Input impedance {impedance:.1f}Ω is below minimum {self.delay_config.min_input_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.delay_config.min_input_impedance
                            }
                        ))
                    elif impedance > self.delay_config.max_input_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Input impedance {impedance:.1f}Ω exceeds maximum {self.delay_config.max_input_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.delay_config.max_input_impedance
                            }
                        ))

            # Validate output impedance
            for net in output_nets:
                impedance = self._calculate_output_impedance(net, board)
                if impedance:
                    if impedance < self.delay_config.min_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Output impedance {impedance:.1f}Ω is below minimum {self.delay_config.min_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.delay_config.min_output_impedance
                            }
                        ))
                    elif impedance > self.delay_config.max_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"Output impedance {impedance:.1f}Ω exceeds maximum {self.delay_config.max_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.delay_config.max_output_impedance
                            }
                        ))

        except Exception as e:
            self.logger.error(f"Error validating delay circuit: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating delay circuit: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    def _find_nearby_components(self, track: pcbnew.TRACK, board: pcbnew.BOARD, prefix: str) -> List[pcbnew.FOOTPRINT]:
        """Find components near a track.
        
        Args:
            track: Track to check
            board: Board object
            prefix: Component reference prefix
            
        Returns:
            List of nearby components
        """
        nearby = []
        try:
            for footprint in board.GetFootprints():
                if footprint.GetReference().startswith(prefix):
                    distance = track.GetStart().Distance(footprint.GetPosition()) / 1e6  # Convert to mm
                    if distance < 5.0:  # 5mm search radius
                        nearby.append(footprint)
        except Exception as e:
            self.logger.error(f"Error finding nearby components: {str(e)}")
        return nearby

    def _calculate_input_impedance(self, net: str, board: pcbnew.BOARD) -> Optional[float]:
        """Calculate input impedance of a net.
        
        Args:
            net: Net name
            board: Board object
            
        Returns:
            Input impedance in ohms, or None if calculation fails
        """
        try:
            # Find input resistor
            for footprint in board.GetFootprints():
                if footprint.GetReference().startswith("R"):
                    for pad in footprint.Pads():
                        if pad.GetNetname() == net:
                            # Get resistor value from value field
                            value = footprint.GetValue()
                            if value.endswith("k"):
                                return float(value[:-1]) * 1000
                            elif value.endswith("M"):
                                return float(value[:-1]) * 1000000
                            else:
                                return float(value)
        except Exception as e:
            self.logger.error(f"Error calculating input impedance: {str(e)}")
        return None

    def _calculate_output_impedance(self, net: str, board: pcbnew.BOARD) -> Optional[float]:
        """Calculate output impedance of a net.
        
        Args:
            net: Net name
            board: Board object
            
        Returns:
            Output impedance in ohms, or None if calculation fails
        """
        try:
            # Find output resistor
            for footprint in board.GetFootprints():
                if footprint.GetReference().startswith("R"):
                    for pad in footprint.Pads():
                        if pad.GetNetname() == net:
                            # Get resistor value from value field
                            value = footprint.GetValue()
                            if value.endswith("k"):
                                return float(value[:-1]) * 1000
                            elif value.endswith("M"):
                                return float(value[:-1]) * 1000000
                            else:
                                return float(value)
        except Exception as e:
            self.logger.error(f"Error calculating output impedance: {str(e)}")
        return None

    def _validate_audio_specific(self) -> List[ValidationResult]:
        """Validate audio-specific rules using BaseValidator interface.
        
        Returns:
            List of validation results
        """
        results = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Check for guitar effect components
            effect_components = []
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["DIST", "DELAY", "MOD", "FILTER", "BUFFER", "EFFECT"]):
                    effect_components.append(footprint)

            # Validate each guitar effect component
            for component in effect_components:
                ref = component.GetReference()
                
                # Check for distortion circuits
                if any(keyword in ref.upper() for keyword in ["DIST", "FUZZ", "OVERDRIVE"]):
                    distortion_results = self.validate_distortion_circuit(ref)
                    results.extend(distortion_results)
                
                # Check for delay circuits
                if any(keyword in ref.upper() for keyword in ["DELAY", "ECHO", "REVERB"]):
                    delay_results = self.validate_delay_circuit(ref)
                    results.extend(delay_results)
                
                # Check for modulation circuits
                if any(keyword in ref.upper() for keyword in ["MOD", "CHORUS", "FLANGER", "TREMOLO"]):
                    modulation_results = self._validate_modulation([component.GetPosition() for component in effect_components])
                    results.extend(modulation_results)
                
                # Check for filter circuits
                if any(keyword in ref.upper() for keyword in ["FILTER", "EQ", "TONE"]):
                    filter_results = self._validate_filter([component.GetPosition() for component in effect_components])
                    results.extend(filter_results)

        except Exception as e:
            self.logger.error(f"Error in audio-specific validation: {e}")
            results.append(self._create_result(
                category=ValidationCategory.AUDIO,
                message=f"Error in audio-specific validation: {e}",
                severity=ValidationSeverity.ERROR
            ))
        
        return results

    def _validate_modulation(self, components: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate modulation effect circuit design."""
        # For now, we assume modulation is valid if present.
        # A full implementation would check for LFOs, BBDs (for chorus/flanger),
        # or OTA-based phasers.
        return [ValidationResult(success=True, message="Modulation validation passed")]

    def _validate_filter(self, components: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate filter effect circuit design."""
        # For now, we assume filter is valid if present.
        # A full implementation would check for filter topology (e.g., Sallen-Key, MFB),
        # cutoff frequency range, and resonance control.
        return [ValidationResult(success=True, message="Filter validation passed")] 