"""Thermal management using KiCad's native functionality."""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pcbnew
from kicad.core.thermal.thermal_manager import ThermalManager, ThermalZone

from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus

@dataclass
class ThermalConfigItem:
    """Data structure for thermal configuration items."""
    id: str
    max_temperature: float = 100.0  # Maximum allowed temperature in °C
    min_component_spacing: float = 0.5  # Minimum spacing between components in mm
    thermal_relief_gap: float = 0.5  # Thermal relief gap in mm
    thermal_relief_spoke_width: float = 0.3  # Thermal relief spoke width in mm
    thermal_relief_spoke_count: int = 4  # Number of thermal relief spokes
    optimize_thermal_zones: bool = True  # Whether to optimize thermal zones
    validate_thermal_design: bool = True  # Whether to validate thermal design
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ThermalConfig(BaseConfig[ThermalConfigItem]):
    """Configuration for thermal management.
    
    Now inherits from BaseConfig for standardized configuration operations.
    """
    
    def __init__(self, name: str = "ThermalConfig", config_path: Optional[str] = None):
        """Initialize thermal configuration.
        
        Args:
            name: Configuration name
            config_path: Path to configuration file
        """
        super().__init__(name, config_path)
        self._setup_default_values()
        self._setup_validation_rules()
    
    def _setup_default_values(self) -> None:
        """Set up default configuration values."""
        self.set_default("max_temperature", 100.0)
        self.set_default("min_component_spacing", 0.5)
        self.set_default("thermal_relief_gap", 0.5)
        self.set_default("thermal_relief_spoke_width", 0.3)
        self.set_default("thermal_relief_spoke_count", 4)
        self.set_default("optimize_thermal_zones", True)
        self.set_default("validate_thermal_design", True)
    
    def _setup_validation_rules(self) -> None:
        """Set up validation rules for configuration values."""
        self.add_validation_rule("max_temperature", {
            "type": "float",
            "min": 0.0,
            "max": 200.0,
            "required": True
        })
        self.add_validation_rule("min_component_spacing", {
            "type": "float",
            "min": 0.1,
            "max": 10.0,
            "required": True
        })
        self.add_validation_rule("thermal_relief_gap", {
            "type": "float",
            "min": 0.1,
            "max": 2.0,
            "required": True
        })
        self.add_validation_rule("thermal_relief_spoke_width", {
            "type": "float",
            "min": 0.1,
            "max": 1.0,
            "required": True
        })
        self.add_validation_rule("thermal_relief_spoke_count", {
            "type": "int",
            "min": 2,
            "max": 8,
            "required": True
        })
        self.add_validation_rule("optimize_thermal_zones", {
            "type": "bool",
            "required": True
        })
        self.add_validation_rule("validate_thermal_design", {
            "type": "bool",
            "required": True
        })
    
    def _validate_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Validate thermal configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            Validation result
        """
        try:
            errors = []
            
            # Validate required fields
            required_fields = [
                "max_temperature", "min_component_spacing", "thermal_relief_gap",
                "thermal_relief_spoke_width", "thermal_relief_spoke_count",
                "optimize_thermal_zones", "validate_thermal_design"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    errors.append(f"Missing required field: {field}")
                    continue
                
                value = config_data[field]
                rule = self._validation_rules.get(field, {})
                
                # Type validation
                if rule.get("type") == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Field {field} must be a number")
                elif rule.get("type") == "int" and not isinstance(value, int):
                    errors.append(f"Field {field} must be an integer")
                elif rule.get("type") == "bool" and not isinstance(value, bool):
                    errors.append(f"Field {field} must be a boolean")
                
                # Range validation
                if "min" in rule and value < rule["min"]:
                    errors.append(f"Field {field} must be >= {rule['min']}")
                if "max" in rule and value > rule["max"]:
                    errors.append(f"Field {field} must be <= {rule['max']}")
            
            if errors:
                return ConfigResult(
                    success=False,
                    status=ConfigStatus.INVALID,
                    message="Thermal configuration validation failed",
                    errors=errors,
                    config_type=self.name
                )
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.VALID,
                message="Thermal configuration is valid",
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error validating thermal configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> ConfigResult:
        """Parse thermal configuration data.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsing result
        """
        try:
            # Create thermal config item
            thermal_item = ThermalConfigItem(
                id=config_data.get("id", "thermal_config"),
                max_temperature=config_data.get("max_temperature", 100.0),
                min_component_spacing=config_data.get("min_component_spacing", 0.5),
                thermal_relief_gap=config_data.get("thermal_relief_gap", 0.5),
                thermal_relief_spoke_width=config_data.get("thermal_relief_spoke_width", 0.3),
                thermal_relief_spoke_count=config_data.get("thermal_relief_spoke_count", 4),
                optimize_thermal_zones=config_data.get("optimize_thermal_zones", True),
                validate_thermal_design=config_data.get("validate_thermal_design", True)
            )
            
            # Add to sections
            self.add_section(ConfigSection(
                name="thermal_settings",
                data=config_data,
                description="Thermal management configuration settings"
            ))
            
            return ConfigResult(
                success=True,
                status=ConfigStatus.LOADED,
                message="Thermal configuration parsed successfully",
                data=thermal_item,
                config_type=self.name
            )
            
        except Exception as e:
            return ConfigResult(
                success=False,
                status=ConfigStatus.ERROR,
                message=f"Error parsing thermal configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )
    
    def _prepare_config_data(self) -> Dict[str, Any]:
        """Prepare thermal configuration data for saving.
        
        Returns:
            Configuration data
        """
        thermal_section = self.get_section("thermal_settings")
        if thermal_section:
            return thermal_section.data
        
        # Return default configuration
        return {
            "id": "thermal_config",
            "max_temperature": self.get_default("max_temperature"),
            "min_component_spacing": self.get_default("min_component_spacing"),
            "thermal_relief_gap": self.get_default("thermal_relief_gap"),
            "thermal_relief_spoke_width": self.get_default("thermal_relief_spoke_width"),
            "thermal_relief_spoke_count": self.get_default("thermal_relief_spoke_count"),
            "optimize_thermal_zones": self.get_default("optimize_thermal_zones"),
            "validate_thermal_design": self.get_default("validate_thermal_design")
        }
    
    def create_thermal_config(self, 
                             max_temperature: float = 100.0,
                             min_component_spacing: float = 0.5,
                             thermal_relief_gap: float = 0.5,
                             thermal_relief_spoke_width: float = 0.3,
                             thermal_relief_spoke_count: int = 4,
                             optimize_thermal_zones: bool = True,
                             validate_thermal_design: bool = True) -> ConfigResult[ThermalConfigItem]:
        """Create a new thermal configuration.
        
        Args:
            max_temperature: Maximum allowed temperature in °C
            min_component_spacing: Minimum spacing between components in mm
            thermal_relief_gap: Thermal relief gap in mm
            thermal_relief_spoke_width: Thermal relief spoke width in mm
            thermal_relief_spoke_count: Number of thermal relief spokes
            optimize_thermal_zones: Whether to optimize thermal zones
            validate_thermal_design: Whether to validate thermal design
            
        Returns:
            Configuration result
        """
        try:
            config_data = {
                "id": f"thermal_config_{len(self._config_history) + 1}",
                "max_temperature": max_temperature,
                "min_component_spacing": min_component_spacing,
                "thermal_relief_gap": thermal_relief_gap,
                "thermal_relief_spoke_width": thermal_relief_spoke_width,
                "thermal_relief_spoke_count": thermal_relief_spoke_count,
                "optimize_thermal_zones": optimize_thermal_zones,
                "validate_thermal_design": validate_thermal_design
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
                message=f"Error creating thermal configuration: {e}",
                errors=[str(e)],
                config_type=self.name
            )

class ThermalManagement:
    """Manages thermal aspects of PCB design using KiCad's native functionality."""
    
    def __init__(self, board: Optional[pcbnew.BOARD] = None, logger: Optional[logging.Logger] = None):
        """Initialize thermal management.
        
        Args:
            board: Optional KiCad board object
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.board = board
        self.thermal_manager = ThermalManager(board)
        self.config = ThermalConfig()
    
    def set_board(self, board: pcbnew.BOARD) -> None:
        """Set the board to manage.
        
        Args:
            board: KiCad board object
        """
        self.board = board
        self.thermal_manager.set_board(board)
        self.logger.info("Set board for thermal management")
    
    def create_thermal_zone(self, name: str, position: Tuple[float, float], 
                           size: Tuple[float, float], temperature: float = 25.0,
                           components: Optional[List[str]] = None) -> None:
        """Create a thermal zone.
        
        Args:
            name: Zone name
            position: (x, y) position in mm
            size: (width, height) in mm
            temperature: Initial temperature in °C
            components: Optional list of component references
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        # Create thermal zone
        zone = ThermalZone(
            name=name,
            position=position,
            size=size,
            temperature=temperature,
            components=components or []
        )
        
        # Add zone using KiCad's thermal manager
        self.thermal_manager.create_thermal_zone(zone)
        
        # Add components if specified
        if components:
            for comp_ref in components:
                self.thermal_manager.add_component_to_zone(name, comp_ref)
        
        self.logger.info(f"Created thermal zone: {name}")
    
    def analyze_thermal(self) -> Dict[str, float]:
        """Analyze thermal performance.
        
        Returns:
            Dictionary mapping zone names to temperatures
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        # Use KiCad's thermal analysis
        temperatures = self.thermal_manager.analyze_thermal()
        
        # Log results
        for zone, temp in temperatures.items():
            self.logger.info(f"Zone {zone} temperature: {temp}°C")
        
        return temperatures
    
    def optimize_thermal_design(self) -> None:
        """Optimize thermal design."""
        if not self.board:
            raise RuntimeError("No board set")
        
        if self.config.optimize_thermal_zones:
            # Use KiCad's thermal optimization
            self.thermal_manager.optimize_thermal_zones()
            self.logger.info("Optimized thermal zones")
    
    def validate_thermal_design(self) -> List[str]:
        """Validate thermal design.
        
        Returns:
            List of validation errors
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        if not self.config.validate_thermal_design:
            return []
        
        # Use KiCad's thermal validation
        errors = self.thermal_manager.validate_thermal_design()
        
        # Log validation results
        if errors:
            self.logger.warning("Thermal validation found issues:")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("Thermal validation passed")
        
        return errors
    
    def get_thermal_zones(self) -> Dict[str, ThermalZone]:
        """Get all thermal zones.
        
        Returns:
            Dictionary mapping zone names to ThermalZone objects
        """
        if not self.board:
            raise RuntimeError("No board set")
        
        return self.thermal_manager.zones
    
    def update_thermal_config(self, **kwargs) -> None:
        """Update thermal configuration.
        
        Args:
            **kwargs: Configuration values to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.logger.info("Updated thermal configuration") 