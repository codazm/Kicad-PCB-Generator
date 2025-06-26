"""
Advanced DRC Configuration Manager

This module provides configuration management for advanced DRC parameters,
focusing on track width, clearance, component placement, routing, power, ground, signal, audio, and thermal validation.
Manufacturing validation is now handled by the unified ManufacturingConfig.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class TrackWidthConfigItem:
    """Data structure for track width validation parameters."""
    min_signal_track_width: float
    min_power_track_width: float
    min_high_speed_track_width: float
    max_track_width: float
    default_track_width: float
    description: str


@dataclass
class ClearanceConfigItem:
    """Data structure for clearance validation parameters."""
    min_clearance: float
    min_power_clearance: float
    min_high_voltage_clearance: float
    min_audio_clearance: float
    min_thermal_clearance: float
    description: str


@dataclass
class ComponentPlacementConfigItem:
    """Data structure for component placement validation parameters."""
    min_component_spacing: float
    min_edge_distance: float
    max_component_density: float
    prefer_orthogonal_orientation: bool
    max_orientation_angle: float
    description: str


@dataclass
class RoutingConfigItem:
    """Data structure for routing validation parameters."""
    max_track_length: float
    max_via_count: int
    min_via_size: float
    max_via_size: float
    prefer_direct_routes: bool
    max_parallel_length: float
    description: str


@dataclass
class PowerConfigItem:
    """Data structure for power validation parameters."""
    min_power_plane_coverage: float
    max_voltage_drop: float
    min_power_track_width: float
    max_current_density: float
    power_net_prefixes: List[str]
    description: str


@dataclass
class GroundConfigItem:
    """Data structure for ground validation parameters."""
    min_ground_coverage: float
    max_ground_loop_area: float
    min_ground_connection_count: int
    prefer_star_grounding: bool
    description: str


@dataclass
class SignalConfigItem:
    """Data structure for signal validation parameters."""
    max_impedance_mismatch: float
    max_crosstalk: float
    max_reflection: float
    min_signal_integrity: float
    high_speed_keywords: List[str]
    description: str


@dataclass
class AudioConfigItem:
    """Data structure for audio validation parameters."""
    min_snr: float
    max_noise_floor: float
    max_distortion: float
    min_bandwidth: float
    max_bandwidth: float
    min_impedance: float
    max_impedance: float
    description: str


@dataclass
class ThermalConfigItem:
    """Data structure for thermal validation parameters."""
    max_temperature_rise: float
    min_thermal_pad_size: float
    max_component_density: float
    thermal_resistance_factor: float
    min_thermal_via_count: int
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for DRC validation settings."""
    check_track_width: bool
    check_clearance: bool
    check_component_placement: bool
    check_routing: bool
    check_power: bool
    check_ground: bool
    check_signal: bool
    check_audio: bool
    check_thermal: bool
    description: str


@dataclass
class ThresholdsConfigItem:
    """Data structure for DRC severity thresholds."""
    warning_severity: float
    error_severity: float
    info_severity: float
    critical_severity: float
    description: str


@dataclass
class UnitsConfigItem:
    """Data structure for DRC units."""
    distance: str
    area: str
    voltage: str
    current: str
    power: str
    temperature: str
    impedance: str
    frequency: str
    description: str


@dataclass
class AdvancedDRCConfigItem:
    """Data structure for advanced DRC configuration."""
    track_width: TrackWidthConfigItem
    clearance: ClearanceConfigItem
    component_placement: ComponentPlacementConfigItem
    routing: RoutingConfigItem
    power: PowerConfigItem
    ground: GroundConfigItem
    signal: SignalConfigItem
    audio: AudioConfigItem
    thermal: ThermalConfigItem
    validation: ValidationConfigItem
    thresholds: ThresholdsConfigItem
    units: UnitsConfigItem
    description: str


class AdvancedDRCConfig(BaseConfig[AdvancedDRCConfigItem]):
    """Configuration manager for advanced DRC parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the advanced DRC configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "advanced_drc_config.json"
        
        super().__init__(config_path)
        self.logger = logging.getLogger(__name__)
    
    def _validate_config(self, config_data: dict) -> bool:
        """Validate configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            True if configuration is valid
        """
        try:
            if "advanced_drc" not in config_data:
                self.logger.error("Missing 'advanced_drc' section in configuration")
                return False
            
            config = config_data["advanced_drc"]
            
            # Validate track width
            if "track_width" not in config:
                self.logger.error("Missing 'track_width' section in advanced_drc")
                return False
            
            track_width = config["track_width"]
            if track_width["min_signal_track_width"] <= 0:
                self.logger.error("Minimum signal track width must be positive")
                return False
            
            if track_width["min_power_track_width"] <= 0:
                self.logger.error("Minimum power track width must be positive")
                return False
            
            if track_width["max_track_width"] <= track_width["min_signal_track_width"]:
                self.logger.error("Maximum track width must be greater than minimum")
                return False
            
            # Validate clearance
            if "clearance" not in config:
                self.logger.error("Missing 'clearance' section in advanced_drc")
                return False
            
            clearance = config["clearance"]
            if clearance["min_clearance"] <= 0:
                self.logger.error("Minimum clearance must be positive")
                return False
            
            if clearance["min_high_voltage_clearance"] <= clearance["min_clearance"]:
                self.logger.error("High voltage clearance must be greater than minimum")
                return False
            
            # Validate component placement
            if "component_placement" not in config:
                self.logger.error("Missing 'component_placement' section in advanced_drc")
                return False
            
            placement = config["component_placement"]
            if placement["min_component_spacing"] <= 0:
                self.logger.error("Minimum component spacing must be positive")
                return False
            
            if placement["min_edge_distance"] <= 0:
                self.logger.error("Minimum edge distance must be positive")
                return False
            
            if placement["max_component_density"] <= 0:
                self.logger.error("Maximum component density must be positive")
                return False
            
            # Validate routing
            if "routing" not in config:
                self.logger.error("Missing 'routing' section in advanced_drc")
                return False
            
            routing = config["routing"]
            if routing["max_track_length"] <= 0:
                self.logger.error("Maximum track length must be positive")
                return False
            
            if routing["max_via_count"] <= 0:
                self.logger.error("Maximum via count must be positive")
                return False
            
            if routing["min_via_size"] <= 0:
                self.logger.error("Minimum via size must be positive")
                return False
            
            if routing["max_via_size"] <= routing["min_via_size"]:
                self.logger.error("Maximum via size must be greater than minimum")
                return False
            
            # Validate power
            if "power" not in config:
                self.logger.error("Missing 'power' section in advanced_drc")
                return False
            
            power = config["power"]
            if power["min_power_plane_coverage"] < 0 or power["min_power_plane_coverage"] > 1:
                self.logger.error("Minimum power plane coverage must be between 0 and 1")
                return False
            
            if power["max_voltage_drop"] <= 0:
                self.logger.error("Maximum voltage drop must be positive")
                return False
            
            if power["min_power_track_width"] <= 0:
                self.logger.error("Minimum power track width must be positive")
                return False
            
            if power["max_current_density"] <= 0:
                self.logger.error("Maximum current density must be positive")
                return False
            
            if not power["power_net_prefixes"]:
                self.logger.error("Power net prefixes cannot be empty")
                return False
            
            # Validate ground
            if "ground" not in config:
                self.logger.error("Missing 'ground' section in advanced_drc")
                return False
            
            ground = config["ground"]
            if ground["min_ground_coverage"] < 0 or ground["min_ground_coverage"] > 1:
                self.logger.error("Minimum ground coverage must be between 0 and 1")
                return False
            
            if ground["max_ground_loop_area"] <= 0:
                self.logger.error("Maximum ground loop area must be positive")
                return False
            
            if ground["min_ground_connection_count"] <= 0:
                self.logger.error("Minimum ground connection count must be positive")
                return False
            
            # Validate signal
            if "signal" not in config:
                self.logger.error("Missing 'signal' section in advanced_drc")
                return False
            
            signal = config["signal"]
            if signal["max_impedance_mismatch"] < 0 or signal["max_impedance_mismatch"] > 1:
                self.logger.error("Maximum impedance mismatch must be between 0 and 1")
                return False
            
            if signal["max_crosstalk"] < 0 or signal["max_crosstalk"] > 1:
                self.logger.error("Maximum crosstalk must be between 0 and 1")
                return False
            
            if signal["max_reflection"] < 0 or signal["max_reflection"] > 1:
                self.logger.error("Maximum reflection must be between 0 and 1")
                return False
            
            if signal["min_signal_integrity"] < 0 or signal["min_signal_integrity"] > 1:
                self.logger.error("Minimum signal integrity must be between 0 and 1")
                return False
            
            if not signal["high_speed_keywords"]:
                self.logger.error("High-speed keywords cannot be empty")
                return False
            
            # Validate audio
            if "audio" not in config:
                self.logger.error("Missing 'audio' section in advanced_drc")
                return False
            
            audio = config["audio"]
            if audio["min_snr"] <= 0:
                self.logger.error("Minimum SNR must be positive")
                return False
            
            if audio["max_noise_floor"] >= 0:
                self.logger.error("Maximum noise floor must be negative")
                return False
            
            if audio["max_distortion"] < 0 or audio["max_distortion"] > 1:
                self.logger.error("Maximum distortion must be between 0 and 1")
                return False
            
            if audio["min_bandwidth"] <= 0:
                self.logger.error("Minimum bandwidth must be positive")
                return False
            
            if audio["max_bandwidth"] <= audio["min_bandwidth"]:
                self.logger.error("Maximum bandwidth must be greater than minimum")
                return False
            
            if audio["min_impedance"] <= 0:
                self.logger.error("Minimum impedance must be positive")
                return False
            
            if audio["max_impedance"] <= audio["min_impedance"]:
                self.logger.error("Maximum impedance must be greater than minimum")
                return False
            
            # Validate thermal
            if "thermal" not in config:
                self.logger.error("Missing 'thermal' section in advanced_drc")
                return False
            
            thermal = config["thermal"]
            if thermal["max_temperature_rise"] <= 0:
                self.logger.error("Maximum temperature rise must be positive")
                return False
            
            if thermal["min_thermal_pad_size"] <= 0:
                self.logger.error("Minimum thermal pad size must be positive")
                return False
            
            if thermal["max_component_density"] <= 0:
                self.logger.error("Maximum component density must be positive")
                return False
            
            if thermal["min_thermal_via_count"] <= 0:
                self.logger.error("Minimum thermal via count must be positive")
                return False
            
            # Validate validation settings
            if "validation" not in config:
                self.logger.error("Missing 'validation' section in advanced_drc")
                return False
            
            # Validate thresholds
            if "thresholds" not in config:
                self.logger.error("Missing 'thresholds' section in advanced_drc")
                return False
            
            thresholds = config["thresholds"]
            if thresholds["warning_severity"] < 0 or thresholds["warning_severity"] > 1:
                self.logger.error("Warning severity must be between 0 and 1")
                return False
            
            if thresholds["error_severity"] < 0 or thresholds["error_severity"] > 1:
                self.logger.error("Error severity must be between 0 and 1")
                return False
            
            if thresholds["info_severity"] < 0 or thresholds["info_severity"] > 1:
                self.logger.error("Info severity must be between 0 and 1")
                return False
            
            if thresholds["critical_severity"] < 0 or thresholds["critical_severity"] > 1:
                self.logger.error("Critical severity must be between 0 and 1")
                return False
            
            # Validate units
            if "units" not in config:
                self.logger.error("Missing 'units' section in advanced_drc")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating advanced DRC configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> AdvancedDRCConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            config = config_data["advanced_drc"]
            
            # Parse track width
            track_width_config = config["track_width"]
            track_width = TrackWidthConfigItem(
                min_signal_track_width=track_width_config["min_signal_track_width"],
                min_power_track_width=track_width_config["min_power_track_width"],
                min_high_speed_track_width=track_width_config["min_high_speed_track_width"],
                max_track_width=track_width_config["max_track_width"],
                default_track_width=track_width_config["default_track_width"],
                description=track_width_config["description"]
            )
            
            # Parse clearance
            clearance_config = config["clearance"]
            clearance = ClearanceConfigItem(
                min_clearance=clearance_config["min_clearance"],
                min_power_clearance=clearance_config["min_power_clearance"],
                min_high_voltage_clearance=clearance_config["min_high_voltage_clearance"],
                min_audio_clearance=clearance_config["min_audio_clearance"],
                min_thermal_clearance=clearance_config["min_thermal_clearance"],
                description=clearance_config["description"]
            )
            
            # Parse component placement
            placement_config = config["component_placement"]
            component_placement = ComponentPlacementConfigItem(
                min_component_spacing=placement_config["min_component_spacing"],
                min_edge_distance=placement_config["min_edge_distance"],
                max_component_density=placement_config["max_component_density"],
                prefer_orthogonal_orientation=placement_config["prefer_orthogonal_orientation"],
                max_orientation_angle=placement_config["max_orientation_angle"],
                description=placement_config["description"]
            )
            
            # Parse routing
            routing_config = config["routing"]
            routing = RoutingConfigItem(
                max_track_length=routing_config["max_track_length"],
                max_via_count=routing_config["max_via_count"],
                min_via_size=routing_config["min_via_size"],
                max_via_size=routing_config["max_via_size"],
                prefer_direct_routes=routing_config["prefer_direct_routes"],
                max_parallel_length=routing_config["max_parallel_length"],
                description=routing_config["description"]
            )
            
            # Parse power
            power_config = config["power"]
            power = PowerConfigItem(
                min_power_plane_coverage=power_config["min_power_plane_coverage"],
                max_voltage_drop=power_config["max_voltage_drop"],
                min_power_track_width=power_config["min_power_track_width"],
                max_current_density=power_config["max_current_density"],
                power_net_prefixes=power_config["power_net_prefixes"],
                description=power_config["description"]
            )
            
            # Parse ground
            ground_config = config["ground"]
            ground = GroundConfigItem(
                min_ground_coverage=ground_config["min_ground_coverage"],
                max_ground_loop_area=ground_config["max_ground_loop_area"],
                min_ground_connection_count=ground_config["min_ground_connection_count"],
                prefer_star_grounding=ground_config["prefer_star_grounding"],
                description=ground_config["description"]
            )
            
            # Parse signal
            signal_config = config["signal"]
            signal = SignalConfigItem(
                max_impedance_mismatch=signal_config["max_impedance_mismatch"],
                max_crosstalk=signal_config["max_crosstalk"],
                max_reflection=signal_config["max_reflection"],
                min_signal_integrity=signal_config["min_signal_integrity"],
                high_speed_keywords=signal_config["high_speed_keywords"],
                description=signal_config["description"]
            )
            
            # Parse audio
            audio_config = config["audio"]
            audio = AudioConfigItem(
                min_snr=audio_config["min_snr"],
                max_noise_floor=audio_config["max_noise_floor"],
                max_distortion=audio_config["max_distortion"],
                min_bandwidth=audio_config["min_bandwidth"],
                max_bandwidth=audio_config["max_bandwidth"],
                min_impedance=audio_config["min_impedance"],
                max_impedance=audio_config["max_impedance"],
                description=audio_config["description"]
            )
            
            # Parse thermal
            thermal_config = config["thermal"]
            thermal = ThermalConfigItem(
                max_temperature_rise=thermal_config["max_temperature_rise"],
                min_thermal_pad_size=thermal_config["min_thermal_pad_size"],
                max_component_density=thermal_config["max_component_density"],
                thermal_resistance_factor=thermal_config["thermal_resistance_factor"],
                min_thermal_via_count=thermal_config["min_thermal_via_count"],
                description=thermal_config["description"]
            )
            
            # Parse validation
            validation_config = config["validation"]
            validation = ValidationConfigItem(
                check_track_width=validation_config["check_track_width"],
                check_clearance=validation_config["check_clearance"],
                check_component_placement=validation_config["check_component_placement"],
                check_routing=validation_config["check_routing"],
                check_power=validation_config["check_power"],
                check_ground=validation_config["check_ground"],
                check_signal=validation_config["check_signal"],
                check_audio=validation_config["check_audio"],
                check_thermal=validation_config["check_thermal"],
                description=validation_config["description"]
            )
            
            # Parse thresholds
            thresholds_config = config["thresholds"]
            thresholds = ThresholdsConfigItem(
                warning_severity=thresholds_config["warning_severity"],
                error_severity=thresholds_config["error_severity"],
                info_severity=thresholds_config["info_severity"],
                critical_severity=thresholds_config["critical_severity"],
                description=thresholds_config["description"]
            )
            
            # Parse units
            units_config = config["units"]
            units = UnitsConfigItem(
                distance=units_config["distance"],
                area=units_config["area"],
                voltage=units_config["voltage"],
                current=units_config["current"],
                power=units_config["power"],
                temperature=units_config["temperature"],
                impedance=units_config["impedance"],
                frequency=units_config["frequency"],
                description=units_config["description"]
            )
            
            return AdvancedDRCConfigItem(
                track_width=track_width,
                clearance=clearance,
                component_placement=component_placement,
                routing=routing,
                power=power,
                ground=ground,
                signal=signal,
                audio=audio,
                thermal=thermal,
                validation=validation,
                thresholds=thresholds,
                units=units,
                description=config.get("description", "Advanced DRC configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing advanced DRC configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: AdvancedDRCConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert track width
            track_width = {
                "min_signal_track_width": config_item.track_width.min_signal_track_width,
                "min_power_track_width": config_item.track_width.min_power_track_width,
                "min_high_speed_track_width": config_item.track_width.min_high_speed_track_width,
                "max_track_width": config_item.track_width.max_track_width,
                "default_track_width": config_item.track_width.default_track_width,
                "description": config_item.track_width.description
            }
            
            # Convert clearance
            clearance = {
                "min_clearance": config_item.clearance.min_clearance,
                "min_power_clearance": config_item.clearance.min_power_clearance,
                "min_high_voltage_clearance": config_item.clearance.min_high_voltage_clearance,
                "min_audio_clearance": config_item.clearance.min_audio_clearance,
                "min_thermal_clearance": config_item.clearance.min_thermal_clearance,
                "description": config_item.clearance.description
            }
            
            # Convert component placement
            component_placement = {
                "min_component_spacing": config_item.component_placement.min_component_spacing,
                "min_edge_distance": config_item.component_placement.min_edge_distance,
                "max_component_density": config_item.component_placement.max_component_density,
                "prefer_orthogonal_orientation": config_item.component_placement.prefer_orthogonal_orientation,
                "max_orientation_angle": config_item.component_placement.max_orientation_angle,
                "description": config_item.component_placement.description
            }
            
            # Convert routing
            routing = {
                "max_track_length": config_item.routing.max_track_length,
                "max_via_count": config_item.routing.max_via_count,
                "min_via_size": config_item.routing.min_via_size,
                "max_via_size": config_item.routing.max_via_size,
                "prefer_direct_routes": config_item.routing.prefer_direct_routes,
                "max_parallel_length": config_item.routing.max_parallel_length,
                "description": config_item.routing.description
            }
            
            # Convert power
            power = {
                "min_power_plane_coverage": config_item.power.min_power_plane_coverage,
                "max_voltage_drop": config_item.power.max_voltage_drop,
                "min_power_track_width": config_item.power.min_power_track_width,
                "max_current_density": config_item.power.max_current_density,
                "power_net_prefixes": config_item.power.power_net_prefixes,
                "description": config_item.power.description
            }
            
            # Convert ground
            ground = {
                "min_ground_coverage": config_item.ground.min_ground_coverage,
                "max_ground_loop_area": config_item.ground.max_ground_loop_area,
                "min_ground_connection_count": config_item.ground.min_ground_connection_count,
                "prefer_star_grounding": config_item.ground.prefer_star_grounding,
                "description": config_item.ground.description
            }
            
            # Convert signal
            signal = {
                "max_impedance_mismatch": config_item.signal.max_impedance_mismatch,
                "max_crosstalk": config_item.signal.max_crosstalk,
                "max_reflection": config_item.signal.max_reflection,
                "min_signal_integrity": config_item.signal.min_signal_integrity,
                "high_speed_keywords": config_item.signal.high_speed_keywords,
                "description": config_item.signal.description
            }
            
            # Convert audio
            audio = {
                "min_snr": config_item.audio.min_snr,
                "max_noise_floor": config_item.audio.max_noise_floor,
                "max_distortion": config_item.audio.max_distortion,
                "min_bandwidth": config_item.audio.min_bandwidth,
                "max_bandwidth": config_item.audio.max_bandwidth,
                "min_impedance": config_item.audio.min_impedance,
                "max_impedance": config_item.audio.max_impedance,
                "description": config_item.audio.description
            }
            
            # Convert thermal
            thermal = {
                "max_temperature_rise": config_item.thermal.max_temperature_rise,
                "min_thermal_pad_size": config_item.thermal.min_thermal_pad_size,
                "max_component_density": config_item.thermal.max_component_density,
                "thermal_resistance_factor": config_item.thermal.thermal_resistance_factor,
                "min_thermal_via_count": config_item.thermal.min_thermal_via_count,
                "description": config_item.thermal.description
            }
            
            # Convert validation
            validation = {
                "check_track_width": config_item.validation.check_track_width,
                "check_clearance": config_item.validation.check_clearance,
                "check_component_placement": config_item.validation.check_component_placement,
                "check_routing": config_item.validation.check_routing,
                "check_power": config_item.validation.check_power,
                "check_ground": config_item.validation.check_ground,
                "check_signal": config_item.validation.check_signal,
                "check_audio": config_item.validation.check_audio,
                "check_thermal": config_item.validation.check_thermal,
                "description": config_item.validation.description
            }
            
            # Convert thresholds
            thresholds = {
                "warning_severity": config_item.thresholds.warning_severity,
                "error_severity": config_item.thresholds.error_severity,
                "info_severity": config_item.thresholds.info_severity,
                "critical_severity": config_item.thresholds.critical_severity,
                "description": config_item.thresholds.description
            }
            
            # Convert units
            units = {
                "distance": config_item.units.distance,
                "area": config_item.units.area,
                "voltage": config_item.units.voltage,
                "current": config_item.units.current,
                "power": config_item.units.power,
                "temperature": config_item.units.temperature,
                "impedance": config_item.units.impedance,
                "frequency": config_item.units.frequency,
                "description": config_item.units.description
            }
            
            return {
                "advanced_drc": {
                    "track_width": track_width,
                    "clearance": clearance,
                    "component_placement": component_placement,
                    "routing": routing,
                    "power": power,
                    "ground": ground,
                    "signal": signal,
                    "audio": audio,
                    "thermal": thermal,
                    "validation": validation,
                    "thresholds": thresholds,
                    "units": units,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing advanced DRC configuration: {str(e)}")
            raise
    
    def get_track_width_config(self) -> Optional[TrackWidthConfigItem]:
        """Get track width configuration.
        
        Returns:
            Track width configuration
        """
        try:
            config = self.get_config()
            return config.track_width
        except Exception as e:
            self.logger.error(f"Error getting track width configuration: {str(e)}")
            return None
    
    def get_clearance_config(self) -> Optional[ClearanceConfigItem]:
        """Get clearance configuration.
        
        Returns:
            Clearance configuration
        """
        try:
            config = self.get_config()
            return config.clearance
        except Exception as e:
            self.logger.error(f"Error getting clearance configuration: {str(e)}")
            return None
    
    def get_component_placement_config(self) -> Optional[ComponentPlacementConfigItem]:
        """Get component placement configuration.
        
        Returns:
            Component placement configuration
        """
        try:
            config = self.get_config()
            return config.component_placement
        except Exception as e:
            self.logger.error(f"Error getting component placement configuration: {str(e)}")
            return None
    
    def get_routing_config(self) -> Optional[RoutingConfigItem]:
        """Get routing configuration.
        
        Returns:
            Routing configuration
        """
        try:
            config = self.get_config()
            return config.routing
        except Exception as e:
            self.logger.error(f"Error getting routing configuration: {str(e)}")
            return None
    
    def get_power_config(self) -> Optional[PowerConfigItem]:
        """Get power configuration.
        
        Returns:
            Power configuration
        """
        try:
            config = self.get_config()
            return config.power
        except Exception as e:
            self.logger.error(f"Error getting power configuration: {str(e)}")
            return None
    
    def get_ground_config(self) -> Optional[GroundConfigItem]:
        """Get ground configuration.
        
        Returns:
            Ground configuration
        """
        try:
            config = self.get_config()
            return config.ground
        except Exception as e:
            self.logger.error(f"Error getting ground configuration: {str(e)}")
            return None
    
    def get_signal_config(self) -> Optional[SignalConfigItem]:
        """Get signal configuration.
        
        Returns:
            Signal configuration
        """
        try:
            config = self.get_config()
            return config.signal
        except Exception as e:
            self.logger.error(f"Error getting signal configuration: {str(e)}")
            return None
    
    def get_audio_config(self) -> Optional[AudioConfigItem]:
        """Get audio configuration.
        
        Returns:
            Audio configuration
        """
        try:
            config = self.get_config()
            return config.audio
        except Exception as e:
            self.logger.error(f"Error getting audio configuration: {str(e)}")
            return None
    
    def get_thermal_config(self) -> Optional[ThermalConfigItem]:
        """Get thermal configuration.
        
        Returns:
            Thermal configuration
        """
        try:
            config = self.get_config()
            return config.thermal
        except Exception as e:
            self.logger.error(f"Error getting thermal configuration: {str(e)}")
            return None
    
    def get_validation_config(self) -> Optional[ValidationConfigItem]:
        """Get validation configuration.
        
        Returns:
            Validation configuration
        """
        try:
            config = self.get_config()
            return config.validation
        except Exception as e:
            self.logger.error(f"Error getting validation configuration: {str(e)}")
            return None
    
    def get_thresholds_config(self) -> Optional[ThresholdsConfigItem]:
        """Get thresholds configuration.
        
        Returns:
            Thresholds configuration
        """
        try:
            config = self.get_config()
            return config.thresholds
        except Exception as e:
            self.logger.error(f"Error getting thresholds configuration: {str(e)}")
            return None
    
    def get_units_config(self) -> Optional[UnitsConfigItem]:
        """Get units configuration.
        
        Returns:
            Units configuration
        """
        try:
            config = self.get_config()
            return config.units
        except Exception as e:
            self.logger.error(f"Error getting units configuration: {str(e)}")
            return None 