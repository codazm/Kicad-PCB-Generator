"""
Enhanced Validator Configuration Manager

This module provides configuration management for enhanced validator parameters,
focusing on thermal, cross-layer, signal integrity, and power distribution validation.
Manufacturing optimization is now handled by the unified ManufacturingConfig.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class ThermalConfigItem:
    """Data structure for thermal validation parameters."""
    max_power_dissipation: float
    thermal_relief_required: bool
    min_thermal_pad_size: float
    max_temperature_rise: float
    thermal_resistance_factor: float
    description: str


@dataclass
class CrossLayerConfigItem:
    """Data structure for cross-layer validation parameters."""
    require_via_transitions: bool
    check_layer_consistency: bool
    max_layer_transitions: int
    via_clearance: float
    description: str


@dataclass
class SignalIntegrityConfigItem:
    """Data structure for signal integrity validation parameters."""
    high_speed_keywords: List[str]
    min_high_speed_width: float
    max_impedance_mismatch: float
    max_crosstalk: float
    max_reflection: float
    min_clearance: float
    description: str


@dataclass
class PowerDistributionConfigItem:
    """Data structure for power distribution validation parameters."""
    power_net_keywords: List[str]
    min_power_track_width: float
    max_voltage_drop: float
    min_power_plane_coverage: float
    require_power_connections: bool
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for enhanced validation settings."""
    check_thermal: bool
    check_cross_layer: bool
    check_signal_integrity: bool
    check_power_distribution: bool
    description: str


@dataclass
class ThresholdsConfigItem:
    """Data structure for enhanced validation severity thresholds."""
    warning_severity: float
    error_severity: float
    info_severity: float
    critical_severity: float
    description: str


@dataclass
class UnitsConfigItem:
    """Data structure for enhanced validation units."""
    distance: str
    power: str
    temperature: str
    voltage: str
    current: str
    impedance: str
    description: str


@dataclass
class EnhancedValidatorConfigItem:
    """Data structure for enhanced validator configuration."""
    thermal: ThermalConfigItem
    cross_layer: CrossLayerConfigItem
    signal_integrity: SignalIntegrityConfigItem
    power_distribution: PowerDistributionConfigItem
    validation: ValidationConfigItem
    thresholds: ThresholdsConfigItem
    units: UnitsConfigItem
    description: str


class EnhancedValidatorConfig(BaseConfig[EnhancedValidatorConfigItem]):
    """Configuration manager for enhanced validator parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the enhanced validator configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "enhanced_validator_config.json"
        
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
            if "enhanced_validator" not in config_data:
                self.logger.error("Missing 'enhanced_validator' section in configuration")
                return False
            
            config = config_data["enhanced_validator"]
            
            # Validate thermal
            if "thermal" not in config:
                self.logger.error("Missing 'thermal' section in enhanced_validator")
                return False
            
            thermal = config["thermal"]
            if thermal["max_power_dissipation"] <= 0:
                self.logger.error("Maximum power dissipation must be positive")
                return False
            
            if thermal["min_thermal_pad_size"] <= 0:
                self.logger.error("Minimum thermal pad size must be positive")
                return False
            
            if thermal["max_temperature_rise"] <= 0:
                self.logger.error("Maximum temperature rise must be positive")
                return False
            
            # Validate cross layer
            if "cross_layer" not in config:
                self.logger.error("Missing 'cross_layer' section in enhanced_validator")
                return False
            
            cross_layer = config["cross_layer"]
            if cross_layer["max_layer_transitions"] <= 0:
                self.logger.error("Maximum layer transitions must be positive")
                return False
            
            if cross_layer["via_clearance"] <= 0:
                self.logger.error("Via clearance must be positive")
                return False
            
            # Validate signal integrity
            if "signal_integrity" not in config:
                self.logger.error("Missing 'signal_integrity' section in enhanced_validator")
                return False
            
            si = config["signal_integrity"]
            if not si["high_speed_keywords"]:
                self.logger.error("High-speed keywords cannot be empty")
                return False
            
            if si["min_high_speed_width"] <= 0:
                self.logger.error("Minimum high-speed width must be positive")
                return False
            
            if si["max_impedance_mismatch"] < 0 or si["max_impedance_mismatch"] > 1:
                self.logger.error("Maximum impedance mismatch must be between 0 and 1")
                return False
            
            if si["max_crosstalk"] < 0 or si["max_crosstalk"] > 1:
                self.logger.error("Maximum crosstalk must be between 0 and 1")
                return False
            
            # Validate power distribution
            if "power_distribution" not in config:
                self.logger.error("Missing 'power_distribution' section in enhanced_validator")
                return False
            
            power = config["power_distribution"]
            if not power["power_net_keywords"]:
                self.logger.error("Power net keywords cannot be empty")
                return False
            
            if power["min_power_track_width"] <= 0:
                self.logger.error("Minimum power track width must be positive")
                return False
            
            if power["max_voltage_drop"] <= 0:
                self.logger.error("Maximum voltage drop must be positive")
                return False
            
            if power["min_power_plane_coverage"] < 0 or power["min_power_plane_coverage"] > 1:
                self.logger.error("Minimum power plane coverage must be between 0 and 1")
                return False
            
            # Validate thresholds
            if "thresholds" not in config:
                self.logger.error("Missing 'thresholds' section in enhanced_validator")
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
                self.logger.error("Missing 'units' section in enhanced_validator")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating enhanced validator configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> EnhancedValidatorConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            config = config_data["enhanced_validator"]
            
            # Parse thermal
            thermal_config = config["thermal"]
            thermal = ThermalConfigItem(
                max_power_dissipation=thermal_config["max_power_dissipation"],
                thermal_relief_required=thermal_config["thermal_relief_required"],
                min_thermal_pad_size=thermal_config["min_thermal_pad_size"],
                max_temperature_rise=thermal_config["max_temperature_rise"],
                thermal_resistance_factor=thermal_config["thermal_resistance_factor"],
                description=thermal_config["description"]
            )
            
            # Parse cross layer
            cross_layer_config = config["cross_layer"]
            cross_layer = CrossLayerConfigItem(
                require_via_transitions=cross_layer_config["require_via_transitions"],
                check_layer_consistency=cross_layer_config["check_layer_consistency"],
                max_layer_transitions=cross_layer_config["max_layer_transitions"],
                via_clearance=cross_layer_config["via_clearance"],
                description=cross_layer_config["description"]
            )
            
            # Parse signal integrity
            si_config = config["signal_integrity"]
            signal_integrity = SignalIntegrityConfigItem(
                high_speed_keywords=si_config["high_speed_keywords"],
                min_high_speed_width=si_config["min_high_speed_width"],
                max_impedance_mismatch=si_config["max_impedance_mismatch"],
                max_crosstalk=si_config["max_crosstalk"],
                max_reflection=si_config["max_reflection"],
                min_clearance=si_config["min_clearance"],
                description=si_config["description"]
            )
            
            # Parse power distribution
            power_config = config["power_distribution"]
            power_distribution = PowerDistributionConfigItem(
                power_net_keywords=power_config["power_net_keywords"],
                min_power_track_width=power_config["min_power_track_width"],
                max_voltage_drop=power_config["max_voltage_drop"],
                min_power_plane_coverage=power_config["min_power_plane_coverage"],
                require_power_connections=power_config["require_power_connections"],
                description=power_config["description"]
            )
            
            # Parse validation
            validation_config = config["validation"]
            validation = ValidationConfigItem(
                check_thermal=validation_config["check_thermal"],
                check_cross_layer=validation_config["check_cross_layer"],
                check_signal_integrity=validation_config["check_signal_integrity"],
                check_power_distribution=validation_config["check_power_distribution"],
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
                power=units_config["power"],
                temperature=units_config["temperature"],
                voltage=units_config["voltage"],
                current=units_config["current"],
                impedance=units_config["impedance"],
                description=units_config["description"]
            )
            
            return EnhancedValidatorConfigItem(
                thermal=thermal,
                cross_layer=cross_layer,
                signal_integrity=signal_integrity,
                power_distribution=power_distribution,
                validation=validation,
                thresholds=thresholds,
                units=units,
                description=config.get("description", "Enhanced validator configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing enhanced validator configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: EnhancedValidatorConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert thermal
            thermal = {
                "max_power_dissipation": config_item.thermal.max_power_dissipation,
                "thermal_relief_required": config_item.thermal.thermal_relief_required,
                "min_thermal_pad_size": config_item.thermal.min_thermal_pad_size,
                "max_temperature_rise": config_item.thermal.max_temperature_rise,
                "thermal_resistance_factor": config_item.thermal.thermal_resistance_factor,
                "description": config_item.thermal.description
            }
            
            # Convert cross layer
            cross_layer = {
                "require_via_transitions": config_item.cross_layer.require_via_transitions,
                "check_layer_consistency": config_item.cross_layer.check_layer_consistency,
                "max_layer_transitions": config_item.cross_layer.max_layer_transitions,
                "via_clearance": config_item.cross_layer.via_clearance,
                "description": config_item.cross_layer.description
            }
            
            # Convert signal integrity
            signal_integrity = {
                "high_speed_keywords": config_item.signal_integrity.high_speed_keywords,
                "min_high_speed_width": config_item.signal_integrity.min_high_speed_width,
                "max_impedance_mismatch": config_item.signal_integrity.max_impedance_mismatch,
                "max_crosstalk": config_item.signal_integrity.max_crosstalk,
                "max_reflection": config_item.signal_integrity.max_reflection,
                "min_clearance": config_item.signal_integrity.min_clearance,
                "description": config_item.signal_integrity.description
            }
            
            # Convert power distribution
            power_distribution = {
                "power_net_keywords": config_item.power_distribution.power_net_keywords,
                "min_power_track_width": config_item.power_distribution.min_power_track_width,
                "max_voltage_drop": config_item.power_distribution.max_voltage_drop,
                "min_power_plane_coverage": config_item.power_distribution.min_power_plane_coverage,
                "require_power_connections": config_item.power_distribution.require_power_connections,
                "description": config_item.power_distribution.description
            }
            
            # Convert validation
            validation = {
                "check_thermal": config_item.validation.check_thermal,
                "check_cross_layer": config_item.validation.check_cross_layer,
                "check_signal_integrity": config_item.validation.check_signal_integrity,
                "check_power_distribution": config_item.validation.check_power_distribution,
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
                "power": config_item.units.power,
                "temperature": config_item.units.temperature,
                "voltage": config_item.units.voltage,
                "current": config_item.units.current,
                "impedance": config_item.units.impedance,
                "description": config_item.units.description
            }
            
            return {
                "enhanced_validator": {
                    "thermal": thermal,
                    "cross_layer": cross_layer,
                    "signal_integrity": signal_integrity,
                    "power_distribution": power_distribution,
                    "validation": validation,
                    "thresholds": thresholds,
                    "units": units,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing enhanced validator configuration: {str(e)}")
            raise
    
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
    
    def get_cross_layer_config(self) -> Optional[CrossLayerConfigItem]:
        """Get cross-layer configuration.
        
        Returns:
            Cross-layer configuration
        """
        try:
            config = self.get_config()
            return config.cross_layer
        except Exception as e:
            self.logger.error(f"Error getting cross-layer configuration: {str(e)}")
            return None
    
    def get_signal_integrity_config(self) -> Optional[SignalIntegrityConfigItem]:
        """Get signal integrity configuration.
        
        Returns:
            Signal integrity configuration
        """
        try:
            config = self.get_config()
            return config.signal_integrity
        except Exception as e:
            self.logger.error(f"Error getting signal integrity configuration: {str(e)}")
            return None
    
    def get_power_distribution_config(self) -> Optional[PowerDistributionConfigItem]:
        """Get power distribution configuration.
        
        Returns:
            Power distribution configuration
        """
        try:
            config = self.get_config()
            return config.power_distribution
        except Exception as e:
            self.logger.error(f"Error getting power distribution configuration: {str(e)}")
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