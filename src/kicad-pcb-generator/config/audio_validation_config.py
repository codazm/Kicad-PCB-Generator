"""
Unified Audio Validation Configuration Manager

This module provides comprehensive configuration management for all audio validation parameters,
combining validation, routing, and manufacturing settings.

All previous audio config files (audio_analysis_config.py, audio_design_config.py, audio_routing_config.py) are merged here.
Audio analysis is now handled by the unified AnalysisManagerConfig.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class FrequencyResponseConfigItem:
    """Data structure for frequency response validation parameters."""
    min_frequency: float
    max_frequency: float
    min_response_flatness: float
    max_phase_variation: float
    description: str


@dataclass
class SignalPathConfigItem:
    """Data structure for signal path validation parameters."""
    min_signal_path_length: float
    max_signal_path_length: float
    min_signal_path_width: float
    max_signal_path_width: float
    prefer_direct_paths: bool
    max_path_angle: float
    min_path_clearance: float
    max_path_impedance: float
    min_path_impedance: float
    description: str


@dataclass
class PowerSupplyConfigItem:
    """Data structure for power supply validation parameters."""
    min_voltage_regulation: float
    max_voltage_ripple: float
    min_power_supply_rejection: float
    max_load_regulation: float
    min_line_regulation: float
    max_transient_response: float
    min_efficiency: float
    description: str


@dataclass
class GroundingConfigItem:
    """Data structure for grounding validation parameters."""
    min_ground_connection_count: int
    max_ground_loop_area: float
    min_ground_plane_coverage: float
    prefer_star_grounding: bool
    max_ground_impedance: float
    min_ground_clearance: float
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
class EMIConfigItem:
    """Data structure for EMI/EMC validation parameters."""
    max_emission_level: float
    max_susceptibility: float
    min_shielding_effectiveness: float
    max_crosstalk: float
    min_isolation_distance: float
    description: str


@dataclass
class ManufacturingConfigItem:
    """Data structure for manufacturing validation parameters."""
    min_hole_size: float
    cost_threshold: float
    yield_impact_threshold: float
    sensitive_area_radius: float
    min_component_spacing: float
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for audio validation settings."""
    check_frequency_response: bool
    check_signal_paths: bool
    check_power_supply: bool
    check_grounding: bool
    check_thermal: bool
    check_emi: bool
    check_manufacturing: bool
    description: str


@dataclass
class ThresholdsConfigItem:
    """Data structure for audio validation severity thresholds."""
    warning_severity: float
    error_severity: float
    info_severity: float
    critical_severity: float
    description: str


@dataclass
class UnitsConfigItem:
    """Data structure for audio validation units."""
    distance: str
    frequency: str
    voltage: str
    current: str
    power: str
    temperature: str
    impedance: str
    cost: str
    description: str


@dataclass
class AudioValidationConfigItem:
    """Data structure for unified audio validation configuration."""
    frequency_response: FrequencyResponseConfigItem
    signal_paths: SignalPathConfigItem
    power_supply: PowerSupplyConfigItem
    grounding: GroundingConfigItem
    thermal: ThermalConfigItem
    emi: EMIConfigItem
    manufacturing: ManufacturingConfigItem
    validation: ValidationConfigItem
    thresholds: ThresholdsConfigItem
    units: UnitsConfigItem
    description: str


class AudioValidationConfig(BaseConfig[AudioValidationConfigItem]):
    """Unified configuration manager for all audio validation parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the unified audio validation configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "audio_validation_config.json"
        
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
            if "audio_validation" not in config_data:
                self.logger.error("Missing 'audio_validation' section in configuration")
                return False
            
            validation_config = config_data["audio_validation"]
            
            # Validate frequency response settings
            if "frequency_response" not in validation_config:
                self.logger.error("Missing 'frequency_response' section in audio_validation")
                return False
            
            freq = validation_config["frequency_response"]
            if freq["min_frequency"] <= 0:
                self.logger.error("Invalid frequency response parameters")
                return False
            
            if freq["max_frequency"] <= freq["min_frequency"]:
                self.logger.error("Maximum frequency must be greater than minimum")
                return False
            
            if freq["min_response_flatness"] < 0 or freq["min_response_flatness"] > 1:
                self.logger.error("Minimum response flatness must be between 0 and 1")
                return False
            
            # Validate signal path settings
            if "signal_paths" not in validation_config:
                self.logger.error("Missing 'signal_paths' section in audio_validation")
                return False
            
            paths = validation_config["signal_paths"]
            if paths["min_signal_path_length"] <= 0:
                self.logger.error("Minimum signal path length must be positive")
                return False
            
            if paths["max_signal_path_length"] <= paths["min_signal_path_length"]:
                self.logger.error("Maximum signal path length must be greater than minimum")
                return False
            
            if paths["min_signal_path_width"] <= 0:
                self.logger.error("Minimum signal path width must be positive")
                return False
            
            if paths["max_signal_path_width"] <= paths["min_signal_path_width"]:
                self.logger.error("Maximum signal path width must be greater than minimum")
                return False
            
            # Validate power supply settings
            if "power_supply" not in validation_config:
                self.logger.error("Missing 'power_supply' section in audio_validation")
                return False
            
            power = validation_config["power_supply"]
            if power["min_voltage_regulation"] <= 0:
                self.logger.error("Minimum voltage regulation must be positive")
                return False
            
            if power["max_voltage_ripple"] <= 0:
                self.logger.error("Maximum voltage ripple must be positive")
                return False
            
            if power["min_efficiency"] < 0 or power["min_efficiency"] > 1:
                self.logger.error("Minimum efficiency must be between 0 and 1")
                return False
            
            # Validate grounding settings
            if "grounding" not in validation_config:
                self.logger.error("Missing 'grounding' section in audio_validation")
                return False
            
            ground = validation_config["grounding"]
            if ground["min_ground_connection_count"] <= 0:
                self.logger.error("Minimum ground connection count must be positive")
                return False
            
            if ground["max_ground_loop_area"] <= 0:
                self.logger.error("Maximum ground loop area must be positive")
                return False
            
            if ground["min_ground_plane_coverage"] < 0 or ground["min_ground_plane_coverage"] > 1:
                self.logger.error("Minimum ground plane coverage must be between 0 and 1")
                return False
            
            # Validate thermal settings
            if "thermal" not in validation_config:
                self.logger.error("Missing 'thermal' section in audio_validation")
                return False
            
            thermal = validation_config["thermal"]
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
            
            # Validate EMI settings
            if "emi" not in validation_config:
                self.logger.error("Missing 'emi' section in audio_validation")
                return False
            
            emi = validation_config["emi"]
            if emi["max_emission_level"] <= 0:
                self.logger.error("Maximum emission level must be positive")
                return False
            
            if emi["max_susceptibility"] <= 0:
                self.logger.error("Maximum susceptibility must be positive")
                return False
            
            if emi["min_shielding_effectiveness"] < 0 or emi["min_shielding_effectiveness"] > 1:
                self.logger.error("Minimum shielding effectiveness must be between 0 and 1")
                return False
            
            if emi["max_crosstalk"] <= 0:
                self.logger.error("Maximum crosstalk must be positive")
                return False
            
            if emi["min_isolation_distance"] <= 0:
                self.logger.error("Minimum isolation distance must be positive")
                return False
            
            # Validate manufacturing settings
            if "manufacturing" not in validation_config:
                self.logger.error("Missing 'manufacturing' section in audio_validation")
                return False
            
            manufacturing = validation_config["manufacturing"]
            if manufacturing["min_hole_size"] <= 0:
                self.logger.error("Invalid manufacturing parameters")
                return False
            
            if manufacturing["cost_threshold"] <= 0:
                self.logger.error("Cost threshold must be positive")
                return False
            
            if manufacturing["yield_impact_threshold"] <= 0:
                self.logger.error("Yield impact threshold must be positive")
                return False
            
            if manufacturing["sensitive_area_radius"] <= 0:
                self.logger.error("Sensitive area radius must be positive")
                return False
            
            if manufacturing["min_component_spacing"] <= 0:
                self.logger.error("Minimum component spacing must be positive")
                return False
            
            # Validate validation settings
            if "validation" not in validation_config:
                self.logger.error("Missing 'validation' section in audio_validation")
                return False
            
            # Validate thresholds
            if "thresholds" not in validation_config:
                self.logger.error("Missing 'thresholds' section in audio_validation")
                return False
            
            thresholds = validation_config["thresholds"]
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
            if "units" not in validation_config:
                self.logger.error("Missing 'units' section in audio_validation")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating audio validation configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> AudioValidationConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            validation_config = config_data["audio_validation"]
            
            # Parse frequency response settings
            freq_config = validation_config["frequency_response"]
            frequency_response = FrequencyResponseConfigItem(
                min_frequency=freq_config["min_frequency"],
                max_frequency=freq_config["max_frequency"],
                min_response_flatness=freq_config["min_response_flatness"],
                max_phase_variation=freq_config["max_phase_variation"],
                description=freq_config["description"]
            )
            
            # Parse signal path settings
            signal_config = validation_config["signal_paths"]
            signal_paths = SignalPathConfigItem(
                min_signal_path_length=signal_config["min_signal_path_length"],
                max_signal_path_length=signal_config["max_signal_path_length"],
                min_signal_path_width=signal_config["min_signal_path_width"],
                max_signal_path_width=signal_config["max_signal_path_width"],
                prefer_direct_paths=signal_config["prefer_direct_paths"],
                max_path_angle=signal_config["max_path_angle"],
                min_path_clearance=signal_config["min_path_clearance"],
                max_path_impedance=signal_config["max_path_impedance"],
                min_path_impedance=signal_config["min_path_impedance"],
                description=signal_config["description"]
            )
            
            # Parse power supply settings
            power_config = validation_config["power_supply"]
            power_supply = PowerSupplyConfigItem(
                min_voltage_regulation=power_config["min_voltage_regulation"],
                max_voltage_ripple=power_config["max_voltage_ripple"],
                min_power_supply_rejection=power_config["min_power_supply_rejection"],
                max_load_regulation=power_config["max_load_regulation"],
                min_line_regulation=power_config["min_line_regulation"],
                max_transient_response=power_config["max_transient_response"],
                min_efficiency=power_config["min_efficiency"],
                description=power_config["description"]
            )
            
            # Parse grounding settings
            ground_config = validation_config["grounding"]
            grounding = GroundingConfigItem(
                min_ground_connection_count=ground_config["min_ground_connection_count"],
                max_ground_loop_area=ground_config["max_ground_loop_area"],
                min_ground_plane_coverage=ground_config["min_ground_plane_coverage"],
                prefer_star_grounding=ground_config["prefer_star_grounding"],
                max_ground_impedance=ground_config["max_ground_impedance"],
                min_ground_clearance=ground_config["min_ground_clearance"],
                description=ground_config["description"]
            )
            
            # Parse thermal settings
            thermal_config = validation_config["thermal"]
            thermal = ThermalConfigItem(
                max_temperature_rise=thermal_config["max_temperature_rise"],
                min_thermal_pad_size=thermal_config["min_thermal_pad_size"],
                max_component_density=thermal_config["max_component_density"],
                thermal_resistance_factor=thermal_config["thermal_resistance_factor"],
                min_thermal_via_count=thermal_config["min_thermal_via_count"],
                description=thermal_config["description"]
            )
            
            # Parse EMI settings
            emi_config = validation_config["emi"]
            emi = EMIConfigItem(
                max_emission_level=emi_config["max_emission_level"],
                max_susceptibility=emi_config["max_susceptibility"],
                min_shielding_effectiveness=emi_config["min_shielding_effectiveness"],
                max_crosstalk=emi_config["max_crosstalk"],
                min_isolation_distance=emi_config["min_isolation_distance"],
                description=emi_config["description"]
            )
            
            # Parse manufacturing settings
            manufacturing_config = validation_config["manufacturing"]
            manufacturing = ManufacturingConfigItem(
                min_hole_size=manufacturing_config["min_hole_size"],
                cost_threshold=manufacturing_config["cost_threshold"],
                yield_impact_threshold=manufacturing_config["yield_impact_threshold"],
                sensitive_area_radius=manufacturing_config["sensitive_area_radius"],
                min_component_spacing=manufacturing_config["min_component_spacing"],
                description=manufacturing_config["description"]
            )
            
            # Parse validation settings
            validation = ValidationConfigItem(
                check_frequency_response=validation_config["check_frequency_response"],
                check_signal_paths=validation_config["check_signal_paths"],
                check_power_supply=validation_config["check_power_supply"],
                check_grounding=validation_config["check_grounding"],
                check_thermal=validation_config["check_thermal"],
                check_emi=validation_config["check_emi"],
                check_manufacturing=validation_config["check_manufacturing"],
                description=validation_config["description"]
            )
            
            # Parse thresholds
            thresholds_config = validation_config["thresholds"]
            thresholds = ThresholdsConfigItem(
                warning_severity=thresholds_config["warning_severity"],
                error_severity=thresholds_config["error_severity"],
                info_severity=thresholds_config["info_severity"],
                critical_severity=thresholds_config["critical_severity"],
                description=thresholds_config["description"]
            )
            
            # Parse units
            units_config = validation_config["units"]
            units = UnitsConfigItem(
                distance=units_config["distance"],
                frequency=units_config["frequency"],
                voltage=units_config["voltage"],
                current=units_config["current"],
                power=units_config["power"],
                temperature=units_config["temperature"],
                impedance=units_config["impedance"],
                cost=units_config["cost"],
                description=units_config["description"]
            )
            
            return AudioValidationConfigItem(
                frequency_response=frequency_response,
                signal_paths=signal_paths,
                power_supply=power_supply,
                grounding=grounding,
                thermal=thermal,
                emi=emi,
                manufacturing=manufacturing,
                validation=validation,
                thresholds=thresholds,
                units=units,
                description=validation_config.get("description", "Audio validation configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing audio validation configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: AudioValidationConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert frequency response settings
            frequency_response = {
                "min_frequency": config_item.frequency_response.min_frequency,
                "max_frequency": config_item.frequency_response.max_frequency,
                "min_response_flatness": config_item.frequency_response.min_response_flatness,
                "max_phase_variation": config_item.frequency_response.max_phase_variation,
                "description": config_item.frequency_response.description
            }
            
            # Convert signal path settings
            signal_paths = {
                "min_signal_path_length": config_item.signal_paths.min_signal_path_length,
                "max_signal_path_length": config_item.signal_paths.max_signal_path_length,
                "min_signal_path_width": config_item.signal_paths.min_signal_path_width,
                "max_signal_path_width": config_item.signal_paths.max_signal_path_width,
                "prefer_direct_paths": config_item.signal_paths.prefer_direct_paths,
                "max_path_angle": config_item.signal_paths.max_path_angle,
                "min_path_clearance": config_item.signal_paths.min_path_clearance,
                "max_path_impedance": config_item.signal_paths.max_path_impedance,
                "min_path_impedance": config_item.signal_paths.min_path_impedance,
                "description": config_item.signal_paths.description
            }
            
            # Convert power supply settings
            power_supply = {
                "min_voltage_regulation": config_item.power_supply.min_voltage_regulation,
                "max_voltage_ripple": config_item.power_supply.max_voltage_ripple,
                "min_power_supply_rejection": config_item.power_supply.min_power_supply_rejection,
                "max_load_regulation": config_item.power_supply.max_load_regulation,
                "min_line_regulation": config_item.power_supply.min_line_regulation,
                "max_transient_response": config_item.power_supply.max_transient_response,
                "min_efficiency": config_item.power_supply.min_efficiency,
                "description": config_item.power_supply.description
            }
            
            # Convert grounding settings
            grounding = {
                "min_ground_connection_count": config_item.grounding.min_ground_connection_count,
                "max_ground_loop_area": config_item.grounding.max_ground_loop_area,
                "min_ground_plane_coverage": config_item.grounding.min_ground_plane_coverage,
                "prefer_star_grounding": config_item.grounding.prefer_star_grounding,
                "max_ground_impedance": config_item.grounding.max_ground_impedance,
                "min_ground_clearance": config_item.grounding.min_ground_clearance,
                "description": config_item.grounding.description
            }
            
            # Convert thermal settings
            thermal = {
                "max_temperature_rise": config_item.thermal.max_temperature_rise,
                "min_thermal_pad_size": config_item.thermal.min_thermal_pad_size,
                "max_component_density": config_item.thermal.max_component_density,
                "thermal_resistance_factor": config_item.thermal.thermal_resistance_factor,
                "min_thermal_via_count": config_item.thermal.min_thermal_via_count,
                "description": config_item.thermal.description
            }
            
            # Convert EMI settings
            emi = {
                "max_emission_level": config_item.emi.max_emission_level,
                "max_susceptibility": config_item.emi.max_susceptibility,
                "min_shielding_effectiveness": config_item.emi.min_shielding_effectiveness,
                "max_crosstalk": config_item.emi.max_crosstalk,
                "min_isolation_distance": config_item.emi.min_isolation_distance,
                "description": config_item.emi.description
            }
            
            # Convert manufacturing settings
            manufacturing = {
                "min_hole_size": config_item.manufacturing.min_hole_size,
                "cost_threshold": config_item.manufacturing.cost_threshold,
                "yield_impact_threshold": config_item.manufacturing.yield_impact_threshold,
                "sensitive_area_radius": config_item.manufacturing.sensitive_area_radius,
                "min_component_spacing": config_item.manufacturing.min_component_spacing,
                "description": config_item.manufacturing.description
            }
            
            # Convert validation settings
            validation = {
                "check_frequency_response": config_item.validation.check_frequency_response,
                "check_signal_paths": config_item.validation.check_signal_paths,
                "check_power_supply": config_item.validation.check_power_supply,
                "check_grounding": config_item.validation.check_grounding,
                "check_thermal": config_item.validation.check_thermal,
                "check_emi": config_item.validation.check_emi,
                "check_manufacturing": config_item.validation.check_manufacturing,
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
                "frequency": config_item.units.frequency,
                "voltage": config_item.units.voltage,
                "current": config_item.units.current,
                "power": config_item.units.power,
                "temperature": config_item.units.temperature,
                "impedance": config_item.units.impedance,
                "cost": config_item.units.cost,
                "description": config_item.units.description
            }
            
            return {
                "audio_validation": {
                    "frequency_response": frequency_response,
                    "signal_paths": signal_paths,
                    "power_supply": power_supply,
                    "grounding": grounding,
                    "thermal": thermal,
                    "emi": emi,
                    "manufacturing": manufacturing,
                    "validation": validation,
                    "thresholds": thresholds,
                    "units": units,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing audio validation configuration: {str(e)}")
            raise
    
    def get_frequency_response_config(self) -> Optional[FrequencyResponseConfigItem]:
        """Get frequency response configuration.
        
        Returns:
            Frequency response configuration
        """
        try:
            config = self.get_config()
            return config.frequency_response
        except Exception as e:
            self.logger.error(f"Error getting frequency response configuration: {str(e)}")
            return None
    
    def get_signal_path_config(self) -> Optional[SignalPathConfigItem]:
        """Get signal path configuration.
        
        Returns:
            Signal path configuration
        """
        try:
            config = self.get_config()
            return config.signal_paths
        except Exception as e:
            self.logger.error(f"Error getting signal path configuration: {str(e)}")
            return None
    
    def get_power_supply_config(self) -> Optional[PowerSupplyConfigItem]:
        """Get power supply configuration.
        
        Returns:
            Power supply configuration
        """
        try:
            config = self.get_config()
            return config.power_supply
        except Exception as e:
            self.logger.error(f"Error getting power supply configuration: {str(e)}")
            return None
    
    def get_grounding_config(self) -> Optional[GroundingConfigItem]:
        """Get grounding configuration.
        
        Returns:
            Grounding configuration
        """
        try:
            config = self.get_config()
            return config.grounding
        except Exception as e:
            self.logger.error(f"Error getting grounding configuration: {str(e)}")
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
    
    def get_emi_config(self) -> Optional[EMIConfigItem]:
        """Get EMI configuration.
        
        Returns:
            EMI configuration
        """
        try:
            config = self.get_config()
            return config.emi
        except Exception as e:
            self.logger.error(f"Error getting EMI configuration: {str(e)}")
            return None
    
    def get_manufacturing_config(self) -> Optional[ManufacturingConfigItem]:
        """Get manufacturing configuration.
        
        Returns:
            Manufacturing configuration
        """
        try:
            config = self.get_config()
            return config.manufacturing
        except Exception as e:
            self.logger.error(f"Error getting manufacturing configuration: {str(e)}")
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