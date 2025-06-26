"""
Settings configuration for KiCad PCB Generator.

This module provides a comprehensive settings system that inherits from BaseConfig
for standardized configuration operations.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from enum import Enum

from ...core.base.base_config import BaseConfig
from ...core.base.results.config_result import ConfigResult, ConfigStatus, ConfigSection


class ValidationSeverity(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SettingsItem:
    """Data structure for application settings."""
    id: str
    # General settings
    output_directory: str
    default_project_name: str
    auto_save_interval: int
    log_level: str
    theme: str
    
    # Audio settings
    audio_layers: List[str]
    min_track_width: float
    min_clearance: float
    ground_clearance: float
    target_impedance: float
    frequency_range: Tuple[float, float]
    
    # Manufacturing settings
    max_board_size: float
    min_hole_size: float
    min_via_size: float
    min_drill_size: float
    copper_thickness: float
    substrate_thickness: float
    
    # Validation settings
    validation_enabled: bool
    real_time_validation: bool
    validation_interval: float
    severity_threshold: ValidationSeverity
    
    # UI settings
    window_size: Tuple[int, int]
    show_toolbar: bool
    show_statusbar: bool
    show_grid: bool
    grid_size: float
    
    # Performance settings
    max_memory_usage: int
    parallel_processing: bool
    cache_enabled: bool
    cache_size: int
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Settings(BaseConfig[SettingsItem]):
    """Application settings configuration.
    
    Inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "Settings", config_path: Optional[str] = None):
        """Initialize settings configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        # General settings
        self.set_default("output_directory", str(Path.home() / "kicad_projects"))
        self.set_default("default_project_name", "new_project")
        self.set_default("auto_save_interval", 300)  # 5 minutes
        self.set_default("log_level", "INFO")
        self.set_default("theme", "default")
        
        # Audio settings
        self.set_default("audio_layers", ["F.Cu", "B.Cu", "F.SilkS", "B.SilkS"])
        self.set_default("min_track_width", 0.1)  # mm
        self.set_default("min_clearance", 0.1)  # mm
        self.set_default("ground_clearance", 0.2)  # mm
        self.set_default("target_impedance", 50.0)  # ohms
        self.set_default("frequency_range", (20.0, 20000.0))  # Hz
        
        # Manufacturing settings
        self.set_default("max_board_size", 100.0)  # mm
        self.set_default("min_hole_size", 0.2)  # mm
        self.set_default("min_via_size", 0.3)  # mm
        self.set_default("min_drill_size", 0.1)  # mm
        self.set_default("copper_thickness", 35.0)  # um
        self.set_default("substrate_thickness", 1.6)  # mm
        
        # Validation settings
        self.set_default("validation_enabled", True)
        self.set_default("real_time_validation", True)
        self.set_default("validation_interval", 1.0)  # seconds
        self.set_default("severity_threshold", ValidationSeverity.WARNING)
        
        # UI settings
        self.set_default("window_size", (1200, 800))
        self.set_default("show_toolbar", True)
        self.set_default("show_statusbar", True)
        self.set_default("show_grid", True)
        self.set_default("grid_size", 1.0)  # mm
        
        # Performance settings
        self.set_default("max_memory_usage", 1024)  # MB
        self.set_default("parallel_processing", True)
        self.set_default("cache_enabled", True)
        self.set_default("cache_size", 100)  # MB
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        # General settings validation
        self.add_validation_rule("output_directory", {
            "type": "str",
            "required": True,
            "min_length": 1
        })
        self.add_validation_rule("default_project_name", {
            "type": "str",
            "required": True,
            "min_length": 1,
            "max_length": 50
        })
        self.add_validation_rule("auto_save_interval", {
            "type": "int",
            "required": True,
            "min": 30,
            "max": 3600
        })
        self.add_validation_rule("log_level", {
            "type": "str",
            "required": True,
            "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        })
        
        # Audio settings validation
        self.add_validation_rule("audio_layers", {
            "type": "list",
            "required": True,
            "min_length": 1,
            "element_type": "str"
        })
        self.add_validation_rule("min_track_width", {
            "type": "float",
            "required": True,
            "min": 0.05,
            "max": 10.0
        })
        self.add_validation_rule("min_clearance", {
            "type": "float",
            "required": True,
            "min": 0.05,
            "max": 5.0
        })
        self.add_validation_rule("target_impedance", {
            "type": "float",
            "required": True,
            "min": 10.0,
            "max": 200.0
        })
        
        # Manufacturing settings validation
        self.add_validation_rule("max_board_size", {
            "type": "float",
            "required": True,
            "min": 10.0,
            "max": 500.0
        })
        self.add_validation_rule("min_hole_size", {
            "type": "float",
            "required": True,
            "min": 0.1,
            "max": 5.0
        })
        self.add_validation_rule("copper_thickness", {
            "type": "float",
            "required": True,
            "min": 17.0,
            "max": 105.0
        })
        
        # Validation settings validation
        self.add_validation_rule("validation_interval", {
            "type": "float",
            "required": True,
            "min": 0.1,
            "max": 60.0
        })
        
        # UI settings validation
        self.add_validation_rule("window_size", {
            "type": "tuple",
            "required": True,
            "length": 2,
            "element_type": "int",
            "min": 800,
            "max": 3000
        })
        self.add_validation_rule("grid_size", {
            "type": "float",
            "required": True,
            "min": 0.1,
            "max": 10.0
        })
        
        # Performance settings validation
        self.add_validation_rule("max_memory_usage", {
            "type": "int",
            "required": True,
            "min": 256,
            "max": 8192
        })
        self.add_validation_rule("cache_size", {
            "type": "int",
            "required": True,
            "min": 10,
            "max": 1000
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate settings configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "output_directory", "default_project_name", "auto_save_interval",
                "log_level", "theme", "audio_layers", "min_track_width",
                "min_clearance", "ground_clearance", "target_impedance",
                "frequency_range", "max_board_size", "min_hole_size",
                "min_via_size", "min_drill_size", "copper_thickness",
                "substrate_thickness", "validation_enabled", "real_time_validation",
                "validation_interval", "severity_threshold", "window_size",
                "show_toolbar", "show_statusbar", "show_grid", "grid_size",
                "max_memory_usage", "parallel_processing", "cache_enabled",
                "cache_size"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "str" and not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif rule.get("type") == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                elif rule.get("type") == "list" and not isinstance(value, list):
                    errors.append(f"Field {field} must be a list")
                elif rule.get("type") == "tuple" and not isinstance(value, tuple):
                    errors.append(f"Field {field} must be a tuple")
                
                # String validation
                if rule.get("type") == "str":
                    if rule.get("min_length") and len(value) < rule["min_length"]:
                        errors.append(f"Field {field} must have minimum length {rule['min_length']}")
                    if rule.get("max_length") and len(value) > rule["max_length"]:
                        errors.append(f"Field {field} must have maximum length {rule['max_length']}")
                    if rule.get("allowed_values") and value not in rule["allowed_values"]:
                        errors.append(f"Field {field} must be one of {rule['allowed_values']}")
                
                # Numeric validation
                if rule.get("type") in ["int", "float"]:
                    if rule.get("min") is not None and value < rule["min"]:
                        errors.append(f"Field {field} must be >= {rule['min']}")
                    if rule.get("max") is not None and value > rule["max"]:
                        errors.append(f"Field {field} must be <= {rule['max']}")
                
                # List validation
                if rule.get("type") == "list":
                    if rule.get("min_length") and len(value) < rule["min_length"]:
                        errors.append(f"Field {field} must have minimum length {rule['min_length']}")
                    if rule.get("element_type") == "str":
                        for i, element in enumerate(value):
                            if not isinstance(element, str):
                                errors.append(f"Field {field}[{i}] must be a string")
                
                # Tuple validation
                if rule.get("type") == "tuple":
                    if rule.get("length") and len(value) != rule["length"]:
                        errors.append(f"Field {field} must have length {rule['length']}")
                    if rule.get("element_type") == "int":
                        for i, element in enumerate(value):
                            if not isinstance(element, int):
                                errors.append(f"Field {field}[{i}] must be an integer")
                            elif rule.get("min") is not None and element < rule["min"]:
                                errors.append(f"Field {field}[{i}] must be >= {rule['min']}")
                            elif rule.get("max") is not None and element > rule["max"]:
                                errors.append(f"Field {field}[{i}] must be <= {rule['max']}")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Settings validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Settings are valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse settings configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create settings item
            settings_item = SettingsItem(
                id=config_data.get("id", "settings"),
                output_directory=config_data.get("output_directory", self.get_default("output_directory")),
                default_project_name=config_data.get("default_project_name", self.get_default("default_project_name")),
                auto_save_interval=config_data.get("auto_save_interval", self.get_default("auto_save_interval")),
                log_level=config_data.get("log_level", self.get_default("log_level")),
                theme=config_data.get("theme", self.get_default("theme")),
                audio_layers=config_data.get("audio_layers", self.get_default("audio_layers")),
                min_track_width=config_data.get("min_track_width", self.get_default("min_track_width")),
                min_clearance=config_data.get("min_clearance", self.get_default("min_clearance")),
                ground_clearance=config_data.get("ground_clearance", self.get_default("ground_clearance")),
                target_impedance=config_data.get("target_impedance", self.get_default("target_impedance")),
                frequency_range=config_data.get("frequency_range", self.get_default("frequency_range")),
                max_board_size=config_data.get("max_board_size", self.get_default("max_board_size")),
                min_hole_size=config_data.get("min_hole_size", self.get_default("min_hole_size")),
                min_via_size=config_data.get("min_via_size", self.get_default("min_via_size")),
                min_drill_size=config_data.get("min_drill_size", self.get_default("min_drill_size")),
                copper_thickness=config_data.get("copper_thickness", self.get_default("copper_thickness")),
                substrate_thickness=config_data.get("substrate_thickness", self.get_default("substrate_thickness")),
                validation_enabled=config_data.get("validation_enabled", self.get_default("validation_enabled")),
                real_time_validation=config_data.get("real_time_validation", self.get_default("real_time_validation")),
                validation_interval=config_data.get("validation_interval", self.get_default("validation_interval")),
                severity_threshold=ValidationSeverity(config_data.get("severity_threshold", self.get_default("severity_threshold").value)),
                window_size=config_data.get("window_size", self.get_default("window_size")),
                show_toolbar=config_data.get("show_toolbar", self.get_default("show_toolbar")),
                show_statusbar=config_data.get("show_statusbar", self.get_default("show_statusbar")),
                show_grid=config_data.get("show_grid", self.get_default("show_grid")),
                grid_size=config_data.get("grid_size", self.get_default("grid_size")),
                max_memory_usage=config_data.get("max_memory_usage", self.get_default("max_memory_usage")),
                parallel_processing=config_data.get("parallel_processing", self.get_default("parallel_processing")),
                cache_enabled=config_data.get("cache_enabled", self.get_default("cache_enabled")),
                cache_size=config_data.get("cache_size", self.get_default("cache_size"))
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="settings",
                data=config_data,
                description="Application settings configuration"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Settings parsed successfully",
                data=settings_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare settings configuration data for saving.
        
        Returns:
            Configuration data
        """
        settings_section = self.get_section("settings")
        if settings_section:
            return settings_section.data
        
        # Return default configuration
        return {
            "id": "settings",
            "output_directory": self.get_default("output_directory"),
            "default_project_name": self.get_default("default_project_name"),
            "auto_save_interval": self.get_default("auto_save_interval"),
            "log_level": self.get_default("log_level"),
            "theme": self.get_default("theme"),
            "audio_layers": self.get_default("audio_layers"),
            "min_track_width": self.get_default("min_track_width"),
            "min_clearance": self.get_default("min_clearance"),
            "ground_clearance": self.get_default("ground_clearance"),
            "target_impedance": self.get_default("target_impedance"),
            "frequency_range": self.get_default("frequency_range"),
            "max_board_size": self.get_default("max_board_size"),
            "min_hole_size": self.get_default("min_hole_size"),
            "min_via_size": self.get_default("min_via_size"),
            "min_drill_size": self.get_default("min_drill_size"),
            "copper_thickness": self.get_default("copper_thickness"),
            "substrate_thickness": self.get_default("substrate_thickness"),
            "validation_enabled": self.get_default("validation_enabled"),
            "real_time_validation": self.get_default("real_time_validation"),
            "validation_interval": self.get_default("validation_interval"),
            "severity_threshold": self.get_default("severity_threshold").value,
            "window_size": self.get_default("window_size"),
            "show_toolbar": self.get_default("show_toolbar"),
            "show_statusbar": self.get_default("show_statusbar"),
            "show_grid": self.get_default("show_grid"),
            "grid_size": self.get_default("grid_size"),
            "max_memory_usage": self.get_default("max_memory_usage"),
            "parallel_processing": self.get_default("parallel_processing"),
            "cache_enabled": self.get_default("cache_enabled"),
            "cache_size": self.get_default("cache_size")
        }
    
    def create_settings(self,
                       output_directory: str = None,
                       default_project_name: str = None,
                       auto_save_interval: int = None,
                       log_level: str = None,
                       theme: str = None,
                       audio_layers: List[str] = None,
                       min_track_width: float = None,
                       min_clearance: float = None,
                       ground_clearance: float = None,
                       target_impedance: float = None,
                       frequency_range: Tuple[float, float] = None,
                       max_board_size: float = None,
                       min_hole_size: float = None,
                       min_via_size: float = None,
                       min_drill_size: float = None,
                       copper_thickness: float = None,
                       substrate_thickness: float = None,
                       validation_enabled: bool = None,
                       real_time_validation: bool = None,
                       validation_interval: float = None,
                       severity_threshold: ValidationSeverity = None,
                       window_size: Tuple[int, int] = None,
                       show_toolbar: bool = None,
                       show_statusbar: bool = None,
                       show_grid: bool = None,
                       grid_size: float = None,
                       max_memory_usage: int = None,
                       parallel_processing: bool = None,
                       cache_enabled: bool = None,
                       cache_size: int = None) -> ConfigResult[SettingsItem]:
        """Create new settings configuration.
        
        Args:
            output_directory: Output directory for projects
            default_project_name: Default project name
            auto_save_interval: Auto-save interval in seconds
            log_level: Logging level
            theme: UI theme
            audio_layers: List of audio layers
            min_track_width: Minimum track width in mm
            min_clearance: Minimum clearance in mm
            ground_clearance: Ground clearance in mm
            target_impedance: Target impedance in ohms
            frequency_range: Frequency range in Hz
            max_board_size: Maximum board size in mm
            min_hole_size: Minimum hole size in mm
            min_via_size: Minimum via size in mm
            min_drill_size: Minimum drill size in mm
            copper_thickness: Copper thickness in um
            substrate_thickness: Substrate thickness in mm
            validation_enabled: Whether validation is enabled
            real_time_validation: Whether real-time validation is enabled
            validation_interval: Validation interval in seconds
            severity_threshold: Validation severity threshold
            window_size: Window size in pixels
            show_toolbar: Whether to show toolbar
            show_statusbar: Whether to show status bar
            show_grid: Whether to show grid
            grid_size: Grid size in mm
            max_memory_usage: Maximum memory usage in MB
            parallel_processing: Whether parallel processing is enabled
            cache_enabled: Whether caching is enabled
            cache_size: Cache size in MB
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"settings_{len(self._config_history) + 1}",
                "output_directory": output_directory or self.get_default("output_directory"),
                "default_project_name": default_project_name or self.get_default("default_project_name"),
                "auto_save_interval": auto_save_interval or self.get_default("auto_save_interval"),
                "log_level": log_level or self.get_default("log_level"),
                "theme": theme or self.get_default("theme"),
                "audio_layers": audio_layers or self.get_default("audio_layers"),
                "min_track_width": min_track_width or self.get_default("min_track_width"),
                "min_clearance": min_clearance or self.get_default("min_clearance"),
                "ground_clearance": ground_clearance or self.get_default("ground_clearance"),
                "target_impedance": target_impedance or self.get_default("target_impedance"),
                "frequency_range": frequency_range or self.get_default("frequency_range"),
                "max_board_size": max_board_size or self.get_default("max_board_size"),
                "min_hole_size": min_hole_size or self.get_default("min_hole_size"),
                "min_via_size": min_via_size or self.get_default("min_via_size"),
                "min_drill_size": min_drill_size or self.get_default("min_drill_size"),
                "copper_thickness": copper_thickness or self.get_default("copper_thickness"),
                "substrate_thickness": substrate_thickness or self.get_default("substrate_thickness"),
                "validation_enabled": validation_enabled if validation_enabled is not None else self.get_default("validation_enabled"),
                "real_time_validation": real_time_validation if real_time_validation is not None else self.get_default("real_time_validation"),
                "validation_interval": validation_interval or self.get_default("validation_interval"),
                "severity_threshold": (severity_threshold or self.get_default("severity_threshold")).value,
                "window_size": window_size or self.get_default("window_size"),
                "show_toolbar": show_toolbar if show_toolbar is not None else self.get_default("show_toolbar"),
                "show_statusbar": show_statusbar if show_statusbar is not None else self.get_default("show_statusbar"),
                "show_grid": show_grid if show_grid is not None else self.get_default("show_grid"),
                "grid_size": grid_size or self.get_default("grid_size"),
                "max_memory_usage": max_memory_usage or self.get_default("max_memory_usage"),
                "parallel_processing": parallel_processing if parallel_processing is not None else self.get_default("parallel_processing"),
                "cache_enabled": cache_enabled if cache_enabled is not None else self.get_default("cache_enabled"),
                "cache_size": cache_size or self.get_default("cache_size")
            }
            
            # Validate configuration
            validation_result = self._validate_config(config_data)
            if not validation_result.success:
                return validation_result
            
            # Parse configuration
            return self._parse_config(config_data)
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error creating settings: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def save_config(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if successful
        """
        try:
            result = self.save()
            return result.success
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset settings to defaults.
        
        Returns:
            True if successful
        """
        try:
            result = self.reset_to_defaults()
            return result.success
        except Exception as e:
            logging.error(f"Error resetting settings: {e}")
            return False 
