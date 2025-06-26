"""
Stability Configuration Manager

This module provides configuration management for stability parameters,
replacing hardcoded values with configurable settings.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class FerriteBeadConfigItem:
    """Data structure for ferrite bead parameters."""
    default_impedance: float
    default_current_rating: float
    default_dc_resistance: float
    frequency_range: str
    impedance_unit: str
    frequency_reference: str
    description: str


@dataclass
class EMCFilterConfigItem:
    """Data structure for EMC filter parameters."""
    default_insertion_loss: float
    default_voltage_rating: float
    default_current_rating: float
    temperature_range: str
    description: str


@dataclass
class PowerFilterConfigItem:
    """Data structure for power filter parameters."""
    default_cutoff_freq: float
    default_order: int
    default_esr: float
    temperature_coefficient: str
    description: str


@dataclass
class AudioFilterConfigItem:
    """Data structure for audio filter parameters."""
    default_insertion_loss: float
    default_impedance: float
    default_distortion: float
    temperature_range: str
    description: str


@dataclass
class FilterTypeConfigItem:
    """Data structure for filter type parameters."""
    default_cutoff_freq: float
    default_order: int
    default_ripple: float
    default_bandwidth: Optional[float] = None
    default_attenuation: Optional[float] = None
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for validation parameters."""
    min_impedance: float
    max_impedance: float
    min_current_rating: float
    max_current_rating: float
    min_voltage_rating: float
    max_voltage_rating: float
    min_capacitance: float
    max_capacitance: float
    min_cutoff_freq: float
    max_cutoff_freq: float
    min_order: int
    max_order: int
    description: str


@dataclass
class StabilityConfigItem:
    """Data structure for stability configuration."""
    ferrite_bead: FerriteBeadConfigItem
    emc_filter: EMCFilterConfigItem
    power_filter: PowerFilterConfigItem
    audio_filter: AudioFilterConfigItem
    filter_types: Dict[str, FilterTypeConfigItem]
    validation: ValidationConfigItem
    description: str


class StabilityConfig(BaseConfig[StabilityConfigItem]):
    """Configuration manager for stability parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the stability configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "stability_config.json"
        
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
            if "stability" not in config_data:
                self.logger.error("Missing 'stability' section in configuration")
                return False
            
            stability_config = config_data["stability"]
            
            # Validate ferrite bead settings
            if "ferrite_bead" not in stability_config:
                self.logger.error("Missing 'ferrite_bead' section in stability")
                return False
            
            ferrite = stability_config["ferrite_bead"]
            if ferrite["default_impedance"] <= 0:
                self.logger.error("Default impedance must be positive")
                return False
            
            if ferrite["default_current_rating"] <= 0:
                self.logger.error("Default current rating must be positive")
                return False
            
            # Validate EMC filter settings
            if "emc_filter" not in stability_config:
                self.logger.error("Missing 'emc_filter' section in stability")
                return False
            
            emc = stability_config["emc_filter"]
            if emc["default_voltage_rating"] <= 0:
                self.logger.error("Default voltage rating must be positive")
                return False
            
            if emc["default_current_rating"] <= 0:
                self.logger.error("Default current rating must be positive")
                return False
            
            # Validate power filter settings
            if "power_filter" not in stability_config:
                self.logger.error("Missing 'power_filter' section in stability")
                return False
            
            power = stability_config["power_filter"]
            if power["default_cutoff_freq"] <= 0:
                self.logger.error("Default cutoff frequency must be positive")
                return False
            
            if power["default_order"] <= 0:
                self.logger.error("Default order must be positive")
                return False
            
            # Validate audio filter settings
            if "audio_filter" not in stability_config:
                self.logger.error("Missing 'audio_filter' section in stability")
                return False
            
            audio = stability_config["audio_filter"]
            if audio["default_impedance"] <= 0:
                self.logger.error("Default impedance must be positive")
                return False
            
            # Validate filter types
            if "filter_types" not in stability_config:
                self.logger.error("Missing 'filter_types' section in stability")
                return False
            
            filter_types = stability_config["filter_types"]
            required_types = ["low_pass", "high_pass", "band_pass", "notch", "emi"]
            for filter_type in required_types:
                if filter_type not in filter_types:
                    self.logger.error(f"Missing filter type '{filter_type}'")
                    return False
                
                ft_config = filter_types[filter_type]
                if ft_config["default_cutoff_freq"] <= 0:
                    self.logger.error(f"Default cutoff frequency must be positive for {filter_type}")
                    return False
                
                if ft_config["default_order"] <= 0:
                    self.logger.error(f"Default order must be positive for {filter_type}")
                    return False
            
            # Validate validation settings
            if "validation" not in stability_config:
                self.logger.error("Missing 'validation' section in stability")
                return False
            
            validation = stability_config["validation"]
            if validation["min_impedance"] <= 0 or validation["max_impedance"] <= validation["min_impedance"]:
                self.logger.error("Invalid impedance range")
                return False
            
            if validation["min_current_rating"] <= 0 or validation["max_current_rating"] <= validation["min_current_rating"]:
                self.logger.error("Invalid current rating range")
                return False
            
            if validation["min_voltage_rating"] <= 0 or validation["max_voltage_rating"] <= validation["min_voltage_rating"]:
                self.logger.error("Invalid voltage rating range")
                return False
            
            if validation["min_capacitance"] <= 0 or validation["max_capacitance"] <= validation["min_capacitance"]:
                self.logger.error("Invalid capacitance range")
                return False
            
            if validation["min_cutoff_freq"] <= 0 or validation["max_cutoff_freq"] <= validation["min_cutoff_freq"]:
                self.logger.error("Invalid cutoff frequency range")
                return False
            
            if validation["min_order"] <= 0 or validation["max_order"] <= validation["min_order"]:
                self.logger.error("Invalid order range")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating stability configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> StabilityConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            stability_config = config_data["stability"]
            
            # Parse ferrite bead settings
            ferrite_config = stability_config["ferrite_bead"]
            ferrite_bead = FerriteBeadConfigItem(
                default_impedance=ferrite_config["default_impedance"],
                default_current_rating=ferrite_config["default_current_rating"],
                default_dc_resistance=ferrite_config["default_dc_resistance"],
                frequency_range=ferrite_config["frequency_range"],
                impedance_unit=ferrite_config["impedance_unit"],
                frequency_reference=ferrite_config["frequency_reference"],
                description=ferrite_config["description"]
            )
            
            # Parse EMC filter settings
            emc_config = stability_config["emc_filter"]
            emc_filter = EMCFilterConfigItem(
                default_insertion_loss=emc_config["default_insertion_loss"],
                default_voltage_rating=emc_config["default_voltage_rating"],
                default_current_rating=emc_config["default_current_rating"],
                temperature_range=emc_config["temperature_range"],
                description=emc_config["description"]
            )
            
            # Parse power filter settings
            power_config = stability_config["power_filter"]
            power_filter = PowerFilterConfigItem(
                default_cutoff_freq=power_config["default_cutoff_freq"],
                default_order=power_config["default_order"],
                default_esr=power_config["default_esr"],
                temperature_coefficient=power_config["temperature_coefficient"],
                description=power_config["description"]
            )
            
            # Parse audio filter settings
            audio_config = stability_config["audio_filter"]
            audio_filter = AudioFilterConfigItem(
                default_insertion_loss=audio_config["default_insertion_loss"],
                default_impedance=audio_config["default_impedance"],
                default_distortion=audio_config["default_distortion"],
                temperature_range=audio_config["temperature_range"],
                description=audio_config["description"]
            )
            
            # Parse filter types
            filter_types_config = stability_config["filter_types"]
            filter_types = {}
            for filter_name, ft_config in filter_types_config.items():
                filter_types[filter_name] = FilterTypeConfigItem(
                    default_cutoff_freq=ft_config["default_cutoff_freq"],
                    default_order=ft_config["default_order"],
                    default_ripple=ft_config["default_ripple"],
                    default_bandwidth=ft_config.get("default_bandwidth"),
                    default_attenuation=ft_config.get("default_attenuation"),
                    description=ft_config["description"]
                )
            
            # Parse validation settings
            validation_config = stability_config["validation"]
            validation = ValidationConfigItem(
                min_impedance=validation_config["min_impedance"],
                max_impedance=validation_config["max_impedance"],
                min_current_rating=validation_config["min_current_rating"],
                max_current_rating=validation_config["max_current_rating"],
                min_voltage_rating=validation_config["min_voltage_rating"],
                max_voltage_rating=validation_config["max_voltage_rating"],
                min_capacitance=validation_config["min_capacitance"],
                max_capacitance=validation_config["max_capacitance"],
                min_cutoff_freq=validation_config["min_cutoff_freq"],
                max_cutoff_freq=validation_config["max_cutoff_freq"],
                min_order=validation_config["min_order"],
                max_order=validation_config["max_order"],
                description=validation_config["description"]
            )
            
            return StabilityConfigItem(
                ferrite_bead=ferrite_bead,
                emc_filter=emc_filter,
                power_filter=power_filter,
                audio_filter=audio_filter,
                filter_types=filter_types,
                validation=validation,
                description=stability_config.get("description", "Stability configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing stability configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: StabilityConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert ferrite bead settings
            ferrite_bead = {
                "default_impedance": config_item.ferrite_bead.default_impedance,
                "default_current_rating": config_item.ferrite_bead.default_current_rating,
                "default_dc_resistance": config_item.ferrite_bead.default_dc_resistance,
                "frequency_range": config_item.ferrite_bead.frequency_range,
                "impedance_unit": config_item.ferrite_bead.impedance_unit,
                "frequency_reference": config_item.ferrite_bead.frequency_reference,
                "description": config_item.ferrite_bead.description
            }
            
            # Convert EMC filter settings
            emc_filter = {
                "default_insertion_loss": config_item.emc_filter.default_insertion_loss,
                "default_voltage_rating": config_item.emc_filter.default_voltage_rating,
                "default_current_rating": config_item.emc_filter.default_current_rating,
                "temperature_range": config_item.emc_filter.temperature_range,
                "description": config_item.emc_filter.description
            }
            
            # Convert power filter settings
            power_filter = {
                "default_cutoff_freq": config_item.power_filter.default_cutoff_freq,
                "default_order": config_item.power_filter.default_order,
                "default_esr": config_item.power_filter.default_esr,
                "temperature_coefficient": config_item.power_filter.temperature_coefficient,
                "description": config_item.power_filter.description
            }
            
            # Convert audio filter settings
            audio_filter = {
                "default_insertion_loss": config_item.audio_filter.default_insertion_loss,
                "default_impedance": config_item.audio_filter.default_impedance,
                "default_distortion": config_item.audio_filter.default_distortion,
                "temperature_range": config_item.audio_filter.temperature_range,
                "description": config_item.audio_filter.description
            }
            
            # Convert filter types
            filter_types = {}
            for filter_name, ft_config in config_item.filter_types.items():
                filter_types[filter_name] = {
                    "default_cutoff_freq": ft_config.default_cutoff_freq,
                    "default_order": ft_config.default_order,
                    "default_ripple": ft_config.default_ripple,
                    "description": ft_config.description
                }
                if ft_config.default_bandwidth is not None:
                    filter_types[filter_name]["default_bandwidth"] = ft_config.default_bandwidth
                if ft_config.default_attenuation is not None:
                    filter_types[filter_name]["default_attenuation"] = ft_config.default_attenuation
            
            # Convert validation settings
            validation = {
                "min_impedance": config_item.validation.min_impedance,
                "max_impedance": config_item.validation.max_impedance,
                "min_current_rating": config_item.validation.min_current_rating,
                "max_current_rating": config_item.validation.max_current_rating,
                "min_voltage_rating": config_item.validation.min_voltage_rating,
                "max_voltage_rating": config_item.validation.max_voltage_rating,
                "min_capacitance": config_item.validation.min_capacitance,
                "max_capacitance": config_item.validation.max_capacitance,
                "min_cutoff_freq": config_item.validation.min_cutoff_freq,
                "max_cutoff_freq": config_item.validation.max_cutoff_freq,
                "min_order": config_item.validation.min_order,
                "max_order": config_item.validation.max_order,
                "description": config_item.validation.description
            }
            
            return {
                "stability": {
                    "ferrite_bead": ferrite_bead,
                    "emc_filter": emc_filter,
                    "power_filter": power_filter,
                    "audio_filter": audio_filter,
                    "filter_types": filter_types,
                    "validation": validation,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing stability configuration: {str(e)}")
            raise
    
    def get_ferrite_bead_config(self) -> Optional[FerriteBeadConfigItem]:
        """Get ferrite bead configuration.
        
        Returns:
            Ferrite bead configuration
        """
        try:
            config = self.get_config()
            return config.ferrite_bead
        except Exception as e:
            self.logger.error(f"Error getting ferrite bead configuration: {str(e)}")
            return None
    
    def get_emc_filter_config(self) -> Optional[EMCFilterConfigItem]:
        """Get EMC filter configuration.
        
        Returns:
            EMC filter configuration
        """
        try:
            config = self.get_config()
            return config.emc_filter
        except Exception as e:
            self.logger.error(f"Error getting EMC filter configuration: {str(e)}")
            return None
    
    def get_power_filter_config(self) -> Optional[PowerFilterConfigItem]:
        """Get power filter configuration.
        
        Returns:
            Power filter configuration
        """
        try:
            config = self.get_config()
            return config.power_filter
        except Exception as e:
            self.logger.error(f"Error getting power filter configuration: {str(e)}")
            return None
    
    def get_audio_filter_config(self) -> Optional[AudioFilterConfigItem]:
        """Get audio filter configuration.
        
        Returns:
            Audio filter configuration
        """
        try:
            config = self.get_config()
            return config.audio_filter
        except Exception as e:
            self.logger.error(f"Error getting audio filter configuration: {str(e)}")
            return None
    
    def get_filter_type_config(self, filter_type: str) -> Optional[FilterTypeConfigItem]:
        """Get filter type configuration.
        
        Args:
            filter_type: Type of filter (low_pass, high_pass, band_pass, notch, emi)
            
        Returns:
            Filter type configuration
        """
        try:
            config = self.get_config()
            return config.filter_types.get(filter_type)
        except Exception as e:
            self.logger.error(f"Error getting filter type configuration for {filter_type}: {str(e)}")
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