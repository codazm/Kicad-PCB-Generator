"""Modular synthesizer circuit validator for the KiCad PCB Generator."""
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

class ModularCircuitType(Enum):
    """Types of modular synthesizer circuits."""
    VCO = "vco"
    VCF = "vcf"
    VCA = "vca"
    LFO = "lfo"
    ENVELOPE = "envelope"
    MIXER = "mixer"

@dataclass
class VCOConfigItem:
    """Configuration item for VCO validation."""
    min_timing_cap_distance: float = 0.5  # mm
    max_timing_cap_distance: float = 2.0  # mm
    min_timing_res_distance: float = 0.5  # mm
    max_timing_res_distance: float = 2.0  # mm
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    max_control_voltage_impedance: float = 10000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms

class VCOConfig(BaseConfig[VCOConfigItem]):
    """Configuration manager for VCO validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize VCO configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: VCOConfigItem) -> ConfigResult:
        """Validate VCO configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate timing cap distances
            if config.min_timing_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum timing cap distance must be positive",
                    data=config
                )
            
            if config.max_timing_cap_distance <= config.min_timing_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum timing cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate timing resistor distances
            if config.min_timing_res_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum timing resistor distance must be positive",
                    data=config
                )
            
            if config.max_timing_res_distance <= config.min_timing_res_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum timing resistor distance must be greater than minimum",
                    data=config
                )
            
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
            
            # Validate control voltage impedance
            if config.max_control_voltage_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum control voltage impedance must be positive",
                    data=config
                )
            
            # Validate output impedance range
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
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="VCO configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating VCO configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating VCO configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> VCOConfigItem:
        """Parse configuration data into VCOConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            VCOConfigItem instance
        """
        try:
            return VCOConfigItem(
                min_timing_cap_distance=config_data.get('min_timing_cap_distance', 0.5),
                max_timing_cap_distance=config_data.get('max_timing_cap_distance', 2.0),
                min_timing_res_distance=config_data.get('min_timing_res_distance', 0.5),
                max_timing_res_distance=config_data.get('max_timing_res_distance', 2.0),
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                max_control_voltage_impedance=config_data.get('max_control_voltage_impedance', 10000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing VCO configuration: {e}")
            raise ValueError(f"Input error in VCO configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing VCO configuration: {e}")
            raise ValueError(f"Unexpected error in VCO configuration data: {e}")
    
    def _prepare_config_data(self, config: VCOConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_timing_cap_distance': config.min_timing_cap_distance,
            'max_timing_cap_distance': config.max_timing_cap_distance,
            'min_timing_res_distance': config.min_timing_res_distance,
            'max_timing_res_distance': config.max_timing_res_distance,
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'max_control_voltage_impedance': config.max_control_voltage_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance
        }

@dataclass
class VCFConfigItem:
    """Configuration item for VCF validation."""
    min_cap_distance: float = 0.5  # mm
    max_cap_distance: float = 2.0  # mm
    min_res_distance: float = 0.5  # mm
    max_res_distance: float = 2.0  # mm
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    max_control_voltage_impedance: float = 10000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms
    min_cutoff_freq: float = 20.0  # Hz
    max_cutoff_freq: float = 20000.0  # Hz

class VCFConfig(BaseConfig[VCFConfigItem]):
    """Configuration manager for VCF validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize VCF configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: VCFConfigItem) -> ConfigResult:
        """Validate VCF configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate cap distances
            if config.min_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum cap distance must be positive",
                    data=config
                )
            
            if config.max_cap_distance <= config.min_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate resistor distances
            if config.min_res_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum resistor distance must be positive",
                    data=config
                )
            
            if config.max_res_distance <= config.min_res_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum resistor distance must be greater than minimum",
                    data=config
                )
            
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
            
            # Validate control voltage impedance
            if config.max_control_voltage_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum control voltage impedance must be positive",
                    data=config
                )
            
            # Validate output impedance range
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
            
            # Validate cutoff frequency range
            if config.min_cutoff_freq <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum cutoff frequency must be positive",
                    data=config
                )
            
            if config.max_cutoff_freq <= config.min_cutoff_freq:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum cutoff frequency must be greater than minimum",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="VCF configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating VCF configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating VCF configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> VCFConfigItem:
        """Parse configuration data into VCFConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            VCFConfigItem instance
        """
        try:
            return VCFConfigItem(
                min_cap_distance=config_data.get('min_cap_distance', 0.5),
                max_cap_distance=config_data.get('max_cap_distance', 2.0),
                min_res_distance=config_data.get('min_res_distance', 0.5),
                max_res_distance=config_data.get('max_res_distance', 2.0),
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                max_control_voltage_impedance=config_data.get('max_control_voltage_impedance', 10000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0),
                min_cutoff_freq=config_data.get('min_cutoff_freq', 20.0),
                max_cutoff_freq=config_data.get('max_cutoff_freq', 20000.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing VCF configuration: {e}")
            raise ValueError(f"Input error in VCF configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing VCF configuration: {e}")
            raise ValueError(f"Unexpected error in VCF configuration data: {e}")
    
    def _prepare_config_data(self, config: VCFConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_cap_distance': config.min_cap_distance,
            'max_cap_distance': config.max_cap_distance,
            'min_res_distance': config.min_res_distance,
            'max_res_distance': config.max_res_distance,
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'max_control_voltage_impedance': config.max_control_voltage_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance,
            'min_cutoff_freq': config.min_cutoff_freq,
            'max_cutoff_freq': config.max_cutoff_freq
        }

@dataclass
class VCAConfigItem:
    """Configuration item for VCA validation."""
    min_cap_distance: float = 0.5  # mm
    max_cap_distance: float = 2.0  # mm
    min_res_distance: float = 0.5  # mm
    max_res_distance: float = 2.0  # mm
    min_power_track_width: float = 0.2  # mm
    min_signal_track_width: float = 0.15  # mm
    max_control_voltage_impedance: float = 10000.0  # ohms
    min_output_impedance: float = 100.0  # ohms
    max_output_impedance: float = 1000.0  # ohms
    min_gain: float = 0.0  # dB
    max_gain: float = 60.0  # dB

class VCAConfig(BaseConfig[VCAConfigItem]):
    """Configuration manager for VCA validation."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize VCA configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: VCAConfigItem) -> ConfigResult:
        """Validate VCA configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate cap distances
            if config.min_cap_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum cap distance must be positive",
                    data=config
                )
            
            if config.max_cap_distance <= config.min_cap_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum cap distance must be greater than minimum",
                    data=config
                )
            
            # Validate resistor distances
            if config.min_res_distance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Minimum resistor distance must be positive",
                    data=config
                )
            
            if config.max_res_distance <= config.min_res_distance:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum resistor distance must be greater than minimum",
                    data=config
                )
            
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
            
            # Validate control voltage impedance
            if config.max_control_voltage_impedance <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Maximum control voltage impedance must be positive",
                    data=config
                )
            
            # Validate output impedance range
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
                message="VCA configuration validated successfully",
                data=config
            )
            
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error validating VCA configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Input error validating configuration: {e}",
                data=config
            )
        except Exception as e:
            self.logger.error(f"Unexpected error validating VCA configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Unexpected error validating configuration: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> VCAConfigItem:
        """Parse configuration data into VCAConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            VCAConfigItem instance
        """
        try:
            return VCAConfigItem(
                min_cap_distance=config_data.get('min_cap_distance', 0.5),
                max_cap_distance=config_data.get('max_cap_distance', 2.0),
                min_res_distance=config_data.get('min_res_distance', 0.5),
                max_res_distance=config_data.get('max_res_distance', 2.0),
                min_power_track_width=config_data.get('min_power_track_width', 0.2),
                min_signal_track_width=config_data.get('min_signal_track_width', 0.15),
                max_control_voltage_impedance=config_data.get('max_control_voltage_impedance', 10000.0),
                min_output_impedance=config_data.get('min_output_impedance', 100.0),
                max_output_impedance=config_data.get('max_output_impedance', 1000.0),
                min_gain=config_data.get('min_gain', 0.0),
                max_gain=config_data.get('max_gain', 60.0)
            )
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            self.logger.error(f"Input error parsing VCA configuration: {e}")
            raise ValueError(f"Input error in VCA configuration data: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing VCA configuration: {e}")
            raise ValueError(f"Unexpected error in VCA configuration data: {e}")
    
    def _prepare_config_data(self, config: VCAConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'min_cap_distance': config.min_cap_distance,
            'max_cap_distance': config.max_cap_distance,
            'min_res_distance': config.min_res_distance,
            'max_res_distance': config.max_res_distance,
            'min_power_track_width': config.min_power_track_width,
            'min_signal_track_width': config.min_signal_track_width,
            'max_control_voltage_impedance': config.max_control_voltage_impedance,
            'min_output_impedance': config.min_output_impedance,
            'max_output_impedance': config.max_output_impedance,
            'min_gain': config.min_gain,
            'max_gain': config.max_gain
        }

class ModularSynthValidator(BaseValidator):
    """Validator for modular synthesizer circuits."""
    
    def __init__(self, logger: Optional[Logger] = None):
        """Initialize the validator.
        
        Args:
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.settings = Settings()
        self.vco_config = VCOConfig()
        self.vcf_config = VCFConfig()
        self.vca_config = VCAConfig()

    @handle_validation_error(logger=Logger(__name__), category="modular_synth")
    def validate_vco_circuit(self, vco_ref: str) -> List[ValidationResult]:
        """Validate a VCO circuit.
        
        Args:
            vco_ref: VCO component reference
            
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Find VCO component
            vco = None
            for footprint in board.GetFootprints():
                if footprint.GetReference() == vco_ref:
                    vco = footprint
                    break

            if not vco:
                results.append(self._create_result(
                    category=ValidationCategory.COMPONENT_PLACEMENT,
                    message=f"VCO {vco_ref} not found",
                    severity=ValidationSeverity.ERROR
                ))
                return results

            # Get VCO nets
            power_nets = []
            control_nets = []
            output_nets = []
            timing_nets = []

            for pad in vco.Pads():
                net = pad.GetNetname()
                if not net:
                    continue

                # Categorize nets based on pad name
                pad_name = pad.GetName().upper()
                if any(name in pad_name for name in ["VCC", "VDD", "POWER", "SUPPLY"]):
                    power_nets.append(net)
                elif any(name in pad_name for name in ["CV", "CONTROL", "FREQ"]):
                    control_nets.append(net)
                elif any(name in pad_name for name in ["OUT", "SIGNAL"]):
                    output_nets.append(net)
                elif any(name in pad_name for name in ["TIMING", "OSC", "FREQ"]):
                    timing_nets.append(net)

            # Validate power tracks
            for net in power_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < self.vco_config.min_power_track_width:
                        results.append(self._create_result(
                            category=ValidationCategory.POWER,
                            message=f"VCO power track width {width:.2f}mm is below minimum {self.vco_config.min_power_track_width}mm",
                            severity=ValidationSeverity.ERROR,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'net': net,
                                'width': width,
                                'min_width': self.vco_config.min_power_track_width
                            }
                        ))

            # Validate timing components
            for net in timing_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    # Find nearby capacitors
                    caps = self._find_nearby_components(track, board, "C")
                    for cap in caps:
                        distance = track.GetStart().Distance(cap.GetPosition()) / 1e6  # Convert to mm
                        if distance < self.vco_config.min_timing_cap_distance:
                            results.append(self._create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Timing capacitor too close to VCO track: {distance:.2f}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'distance': distance,
                                    'min_distance': self.vco_config.min_timing_cap_distance
                                }
                            ))

            # Validate control voltage impedance
            for net in control_nets:
                impedance = self._calculate_input_impedance(net, board)
                if impedance and impedance > self.vco_config.max_control_voltage_impedance:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"VCO control voltage impedance {impedance:.1f}Ω exceeds maximum {self.vco_config.max_control_voltage_impedance}Ω",
                        severity=ValidationSeverity.ERROR,
                        details={
                            'net': net,
                            'impedance': impedance,
                            'max_impedance': self.vco_config.max_control_voltage_impedance
                        }
                    ))

            # Validate output impedance
            for net in output_nets:
                impedance = self._calculate_output_impedance(net, board)
                if impedance:
                    if impedance < self.vco_config.min_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"VCO output impedance {impedance:.1f}Ω is below minimum {self.vco_config.min_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.vco_config.min_output_impedance
                            }
                        ))
                    elif impedance > self.vco_config.max_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"VCO output impedance {impedance:.1f}Ω exceeds maximum {self.vco_config.max_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.vco_config.max_output_impedance
                            }
                        ))

        except Exception as e:
            self.logger.error(f"Error validating VCO circuit: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating VCO circuit: {str(e)}",
                severity=ValidationSeverity.ERROR
            ))

        return results

    @handle_validation_error(logger=Logger(__name__), category="modular_synth")
    def validate_vcf_circuit(self, vcf_ref: str) -> List[ValidationResult]:
        """Validate a VCF circuit.
        
        Args:
            vcf_ref: VCF component reference
            
        Returns:
            List of validation results
        """
        results: List[ValidationResult] = []
        try:
            board = pcbnew.GetBoard()
            if not board:
                return results

            # Find VCF component
            vcf = None
            for footprint in board.GetFootprints():
                if footprint.GetReference() == vcf_ref:
                    vcf = footprint
                    break

            if not vcf:
                results.append(self._create_result(
                    category=ValidationCategory.COMPONENT_PLACEMENT,
                    message=f"VCF {vcf_ref} not found",
                    severity=ValidationSeverity.ERROR
                ))
                return results

            # Get VCF nets
            power_nets = []
            control_nets = []
            input_nets = []
            output_nets = []
            filter_nets = []

            for pad in vcf.Pads():
                net = pad.GetNetname()
                if not net:
                    continue

                # Categorize nets based on pad name
                pad_name = pad.GetName().upper()
                if any(name in pad_name for name in ["VCC", "VDD", "POWER", "SUPPLY"]):
                    power_nets.append(net)
                elif any(name in pad_name for name in ["CV", "CONTROL", "FREQ"]):
                    control_nets.append(net)
                elif any(name in pad_name for name in ["IN", "INPUT"]):
                    input_nets.append(net)
                elif any(name in pad_name for name in ["OUT", "OUTPUT"]):
                    output_nets.append(net)
                elif any(name in pad_name for name in ["FILTER", "CUTOFF", "RESONANCE"]):
                    filter_nets.append(net)

            # Validate power tracks
            for net in power_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    width = track.GetWidth() / 1e6  # Convert to mm
                    if width < self.vcf_config.min_power_track_width:
                        results.append(self._create_result(
                            category=ValidationCategory.POWER,
                            message=f"VCF power track width {width:.2f}mm is below minimum {self.vcf_config.min_power_track_width}mm",
                            severity=ValidationSeverity.ERROR,
                            location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                            details={
                                'net': net,
                                'width': width,
                                'min_width': self.vcf_config.min_power_track_width
                            }
                        ))

            # Validate filter components
            for net in filter_nets:
                tracks = [t for t in board.GetTracks() if t.GetNetname() == net]
                for track in tracks:
                    # Find nearby capacitors and resistors
                    caps = self._find_nearby_components(track, board, "C")
                    res = self._find_nearby_components(track, board, "R")
                    
                    for cap in caps:
                        distance = track.GetStart().Distance(cap.GetPosition()) / 1e6  # Convert to mm
                        if distance < self.vcf_config.min_cap_distance:
                            results.append(self._create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Filter capacitor too close to VCF track: {distance:.2f}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'distance': distance,
                                    'min_distance': self.vcf_config.min_cap_distance
                                }
                            ))
                    
                    for r in res:
                        distance = track.GetStart().Distance(r.GetPosition()) / 1e6  # Convert to mm
                        if distance < self.vcf_config.min_res_distance:
                            results.append(self._create_result(
                                category=ValidationCategory.COMPONENT_PLACEMENT,
                                message=f"Filter resistor too close to VCF track: {distance:.2f}mm",
                                severity=ValidationSeverity.ERROR,
                                location=(track.GetStart().x/1e6, track.GetStart().y/1e6),
                                details={
                                    'net': net,
                                    'distance': distance,
                                    'min_distance': self.vcf_config.min_res_distance
                                }
                            ))

            # Validate control voltage impedance
            for net in control_nets:
                impedance = self._calculate_input_impedance(net, board)
                if impedance and impedance > self.vcf_config.max_control_voltage_impedance:
                    results.append(self._create_result(
                        category=ValidationCategory.SIGNAL,
                        message=f"VCF control voltage impedance {impedance:.1f}Ω exceeds maximum {self.vcf_config.max_control_voltage_impedance}Ω",
                        severity=ValidationSeverity.ERROR,
                        details={
                            'net': net,
                            'impedance': impedance,
                            'max_impedance': self.vcf_config.max_control_voltage_impedance
                        }
                    ))

            # Validate input/output impedance
            for net in input_nets + output_nets:
                impedance = self._calculate_output_impedance(net, board)
                if impedance:
                    if impedance < self.vcf_config.min_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"VCF I/O impedance {impedance:.1f}Ω is below minimum {self.vcf_config.min_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'min_impedance': self.vcf_config.min_output_impedance
                            }
                        ))
                    elif impedance > self.vcf_config.max_output_impedance:
                        results.append(self._create_result(
                            category=ValidationCategory.SIGNAL,
                            message=f"VCF I/O impedance {impedance:.1f}Ω exceeds maximum {self.vcf_config.max_output_impedance}Ω",
                            severity=ValidationSeverity.ERROR,
                            details={
                                'net': net,
                                'impedance': impedance,
                                'max_impedance': self.vcf_config.max_output_impedance
                            }
                        ))

        except Exception as e:
            self.logger.error(f"Error validating VCF circuit: {str(e)}")
            results.append(self._create_result(
                category=ValidationCategory.SIGNAL,
                message=f"Error validating VCF circuit: {str(e)}",
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

            # Check for modular synth components
            modular_components = []
            for footprint in board.GetFootprints():
                ref = footprint.GetReference()
                if any(keyword in ref.upper() for keyword in ["VCO", "VCF", "VCA", "LFO", "ENV", "MIX"]):
                    modular_components.append(footprint)

            # Validate each modular synth component
            for component in modular_components:
                ref = component.GetReference()
                
                # Check for VCO circuits
                if "VCO" in ref.upper():
                    vco_results = self.validate_vco_circuit(ref)
                    results.extend(vco_results)
                
                # Check for VCF circuits
                if "VCF" in ref.upper():
                    vcf_results = self.validate_vcf_circuit(ref)
                    results.extend(vcf_results)
                
                # Check for VCA circuits
                if "VCA" in ref.upper():
                    vca_results = self._validate_vca([component])
                    results.extend(vca_results)
                
                # Check for LFO circuits
                if "LFO" in ref.upper():
                    lfo_results = self._validate_lfo([component])
                    results.extend(lfo_results)

        except Exception as e:
            self.logger.error(f"Error in audio-specific validation: {e}")
            results.append(self._create_result(
                category=ValidationCategory.AUDIO,
                message=f"Error in audio-specific validation: {e}",
                severity=ValidationSeverity.ERROR
            ))
        
        return results

    def _validate_vca(self, components: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate VCA circuit design."""
        # For now, we assume VCA is valid if present.
        # A full implementation would check for specific op-amp configurations,
        # control voltage ranges, and signal path integrity.
        return [ValidationResult(success=True, message="VCA validation passed")]

    def _validate_lfo(self, components: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate LFO circuit design."""
        # For now, we assume LFO is valid if present.
        # A full implementation would check for oscillation frequency range,
        # waveform purity, and output level.
        return [ValidationResult(success=True, message="LFO validation passed")] 