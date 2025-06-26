"""
Unified Manufacturing Configuration Manager

This module provides comprehensive configuration management for all manufacturing parameters,
combining validation, optimization, and cost analysis settings.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig


@dataclass
class ManufacturingValidationConfigItem:
    """Data structure for manufacturing validation parameters."""
    min_hole_size: float
    max_hole_size: float
    min_pad_size: float
    max_pad_size: float
    min_silk_width: float
    max_silk_width: float
    description: str


@dataclass
class ManufacturingOptimizationConfigItem:
    """Data structure for manufacturing optimization parameters."""
    max_component_spacing: float
    prefer_orthogonal_orientation: bool
    max_orientation_angle: float
    min_pad_size: float
    max_via_size: float
    prefer_standard_grid: bool
    description: str


@dataclass
class CostAnalysisConfigItem:
    """Data structure for manufacturing cost analysis parameters."""
    cost_threshold: float
    yield_impact_threshold: float
    sensitive_area_radius: float
    min_component_spacing: float
    description: str


@dataclass
class PanelizationConfigItem:
    """Data structure for panelization parameters."""
    panel_size_x: float
    panel_size_y: float
    board_spacing: float
    edge_clearance: float
    fiducial_size: float
    fiducial_clearance: float
    description: str


@dataclass
class ThermalManagementConfigItem:
    """Data structure for thermal management parameters."""
    max_temperature_rise: float
    min_thermal_pad_size: float
    thermal_resistance_factor: float
    min_thermal_via_count: int
    description: str


@dataclass
class QualityControlConfigItem:
    """Data structure for quality control parameters."""
    min_test_point_size: float
    min_test_point_clearance: float
    require_fiducials: bool
    require_test_points: bool
    min_solder_mask_clearance: float
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for manufacturing validation settings."""
    check_manufacturing: bool
    check_manufacturing_optimization: bool
    check_cost_analysis: bool
    check_panelization: bool
    check_thermal_management: bool
    check_quality_control: bool
    description: str


@dataclass
class ThresholdsConfigItem:
    """Data structure for manufacturing severity thresholds."""
    warning_severity: float
    error_severity: float
    info_severity: float
    critical_severity: float
    description: str


@dataclass
class UnitsConfigItem:
    """Data structure for manufacturing units."""
    distance: str
    area: str
    cost: str
    temperature: str
    description: str


@dataclass
class ManufacturingConfigItem:
    """Data structure for unified manufacturing configuration."""
    validation: ManufacturingValidationConfigItem
    optimization: ManufacturingOptimizationConfigItem
    cost_analysis: CostAnalysisConfigItem
    panelization: PanelizationConfigItem
    thermal_management: ThermalManagementConfigItem
    quality_control: QualityControlConfigItem
    validation_settings: ValidationConfigItem
    thresholds: ThresholdsConfigItem
    units: UnitsConfigItem
    description: str


class ManufacturingConfig(BaseConfig[ManufacturingConfigItem]):
    """Unified configuration manager for all manufacturing parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the unified manufacturing configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "manufacturing_config.json"
        
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
            if "manufacturing" not in config_data:
                self.logger.error("Missing 'manufacturing' section in configuration")
                return False
            
            config = config_data["manufacturing"]
            
            # Validate manufacturing validation
            if "validation" not in config:
                self.logger.error("Missing 'validation' section in manufacturing")
                return False
            
            validation = config["validation"]
            if validation["min_hole_size"] <= 0:
                self.logger.error("Minimum hole size must be positive")
                return False
            
            if validation["max_hole_size"] <= validation["min_hole_size"]:
                self.logger.error("Maximum hole size must be greater than minimum")
                return False
            
            if validation["min_pad_size"] <= 0:
                self.logger.error("Minimum pad size must be positive")
                return False
            
            if validation["max_pad_size"] <= validation["min_pad_size"]:
                self.logger.error("Maximum pad size must be greater than minimum")
                return False
            
            # Validate manufacturing optimization
            if "optimization" not in config:
                self.logger.error("Missing 'optimization' section in manufacturing")
                return False
            
            optimization = config["optimization"]
            if optimization["max_component_spacing"] <= 0:
                self.logger.error("Maximum component spacing must be positive")
                return False
            
            if optimization["max_orientation_angle"] <= 0 or optimization["max_orientation_angle"] > 180:
                self.logger.error("Maximum orientation angle must be between 0 and 180 degrees")
                return False
            
            if optimization["min_pad_size"] <= 0:
                self.logger.error("Minimum pad size must be positive")
                return False
            
            if optimization["max_via_size"] <= 0:
                self.logger.error("Maximum via size must be positive")
                return False
            
            # Validate cost analysis
            if "cost_analysis" not in config:
                self.logger.error("Missing 'cost_analysis' section in manufacturing")
                return False
            
            cost_analysis = config["cost_analysis"]
            if cost_analysis["cost_threshold"] <= 0:
                self.logger.error("Cost threshold must be positive")
                return False
            
            if cost_analysis["yield_impact_threshold"] <= 0:
                self.logger.error("Yield impact threshold must be positive")
                return False
            
            if cost_analysis["sensitive_area_radius"] <= 0:
                self.logger.error("Sensitive area radius must be positive")
                return False
            
            if cost_analysis["min_component_spacing"] <= 0:
                self.logger.error("Minimum component spacing must be positive")
                return False
            
            # Validate panelization
            if "panelization" not in config:
                self.logger.error("Missing 'panelization' section in manufacturing")
                return False
            
            panelization = config["panelization"]
            if panelization["panel_size_x"] <= 0:
                self.logger.error("Panel size X must be positive")
                return False
            
            if panelization["panel_size_y"] <= 0:
                self.logger.error("Panel size Y must be positive")
                return False
            
            if panelization["board_spacing"] <= 0:
                self.logger.error("Board spacing must be positive")
                return False
            
            if panelization["edge_clearance"] <= 0:
                self.logger.error("Edge clearance must be positive")
                return False
            
            # Validate thermal management
            if "thermal_management" not in config:
                self.logger.error("Missing 'thermal_management' section in manufacturing")
                return False
            
            thermal = config["thermal_management"]
            if thermal["max_temperature_rise"] <= 0:
                self.logger.error("Maximum temperature rise must be positive")
                return False
            
            if thermal["min_thermal_pad_size"] <= 0:
                self.logger.error("Minimum thermal pad size must be positive")
                return False
            
            if thermal["min_thermal_via_count"] <= 0:
                self.logger.error("Minimum thermal via count must be positive")
                return False
            
            # Validate quality control
            if "quality_control" not in config:
                self.logger.error("Missing 'quality_control' section in manufacturing")
                return False
            
            quality = config["quality_control"]
            if quality["min_test_point_size"] <= 0:
                self.logger.error("Minimum test point size must be positive")
                return False
            
            if quality["min_test_point_clearance"] <= 0:
                self.logger.error("Minimum test point clearance must be positive")
                return False
            
            if quality["min_solder_mask_clearance"] <= 0:
                self.logger.error("Minimum solder mask clearance must be positive")
                return False
            
            # Validate validation settings
            if "validation_settings" not in config:
                self.logger.error("Missing 'validation_settings' section in manufacturing")
                return False
            
            # Validate thresholds
            if "thresholds" not in config:
                self.logger.error("Missing 'thresholds' section in manufacturing")
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
                self.logger.error("Missing 'units' section in manufacturing")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating manufacturing configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> ManufacturingConfigItem:
        """Parse configuration data into config item.
        
        Args:
            config_data: Configuration data to parse
            
        Returns:
            Parsed configuration item
        """
        try:
            config = config_data["manufacturing"]
            
            # Parse manufacturing validation
            validation_config = config["validation"]
            validation = ManufacturingValidationConfigItem(
                min_hole_size=validation_config["min_hole_size"],
                max_hole_size=validation_config["max_hole_size"],
                min_pad_size=validation_config["min_pad_size"],
                max_pad_size=validation_config["max_pad_size"],
                min_silk_width=validation_config["min_silk_width"],
                max_silk_width=validation_config["max_silk_width"],
                description=validation_config["description"]
            )
            
            # Parse manufacturing optimization
            optimization_config = config["optimization"]
            optimization = ManufacturingOptimizationConfigItem(
                max_component_spacing=optimization_config["max_component_spacing"],
                prefer_orthogonal_orientation=optimization_config["prefer_orthogonal_orientation"],
                max_orientation_angle=optimization_config["max_orientation_angle"],
                min_pad_size=optimization_config["min_pad_size"],
                max_via_size=optimization_config["max_via_size"],
                prefer_standard_grid=optimization_config["prefer_standard_grid"],
                description=optimization_config["description"]
            )
            
            # Parse cost analysis
            cost_analysis_config = config["cost_analysis"]
            cost_analysis = CostAnalysisConfigItem(
                cost_threshold=cost_analysis_config["cost_threshold"],
                yield_impact_threshold=cost_analysis_config["yield_impact_threshold"],
                sensitive_area_radius=cost_analysis_config["sensitive_area_radius"],
                min_component_spacing=cost_analysis_config["min_component_spacing"],
                description=cost_analysis_config["description"]
            )
            
            # Parse panelization
            panelization_config = config["panelization"]
            panelization = PanelizationConfigItem(
                panel_size_x=panelization_config["panel_size_x"],
                panel_size_y=panelization_config["panel_size_y"],
                board_spacing=panelization_config["board_spacing"],
                edge_clearance=panelization_config["edge_clearance"],
                fiducial_size=panelization_config["fiducial_size"],
                fiducial_clearance=panelization_config["fiducial_clearance"],
                description=panelization_config["description"]
            )
            
            # Parse thermal management
            thermal_config = config["thermal_management"]
            thermal_management = ThermalManagementConfigItem(
                max_temperature_rise=thermal_config["max_temperature_rise"],
                min_thermal_pad_size=thermal_config["min_thermal_pad_size"],
                thermal_resistance_factor=thermal_config["thermal_resistance_factor"],
                min_thermal_via_count=thermal_config["min_thermal_via_count"],
                description=thermal_config["description"]
            )
            
            # Parse quality control
            quality_config = config["quality_control"]
            quality_control = QualityControlConfigItem(
                min_test_point_size=quality_config["min_test_point_size"],
                min_test_point_clearance=quality_config["min_test_point_clearance"],
                require_fiducials=quality_config["require_fiducials"],
                require_test_points=quality_config["require_test_points"],
                min_solder_mask_clearance=quality_config["min_solder_mask_clearance"],
                description=quality_config["description"]
            )
            
            # Parse validation settings
            validation_settings_config = config["validation_settings"]
            validation_settings = ValidationConfigItem(
                check_manufacturing=validation_settings_config["check_manufacturing"],
                check_manufacturing_optimization=validation_settings_config["check_manufacturing_optimization"],
                check_cost_analysis=validation_settings_config["check_cost_analysis"],
                check_panelization=validation_settings_config["check_panelization"],
                check_thermal_management=validation_settings_config["check_thermal_management"],
                check_quality_control=validation_settings_config["check_quality_control"],
                description=validation_settings_config["description"]
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
                cost=units_config["cost"],
                temperature=units_config["temperature"],
                description=units_config["description"]
            )
            
            return ManufacturingConfigItem(
                validation=validation,
                optimization=optimization,
                cost_analysis=cost_analysis,
                panelization=panelization,
                thermal_management=thermal_management,
                quality_control=quality_control,
                validation_settings=validation_settings,
                thresholds=thresholds,
                units=units,
                description=config.get("description", "Manufacturing configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing manufacturing configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: ManufacturingConfigItem) -> dict:
        """Prepare config item for serialization.
        
        Args:
            config_item: Configuration item to prepare
            
        Returns:
            Prepared configuration data
        """
        try:
            # Convert validation
            validation = {
                "min_hole_size": config_item.validation.min_hole_size,
                "max_hole_size": config_item.validation.max_hole_size,
                "min_pad_size": config_item.validation.min_pad_size,
                "max_pad_size": config_item.validation.max_pad_size,
                "min_silk_width": config_item.validation.min_silk_width,
                "max_silk_width": config_item.validation.max_silk_width,
                "description": config_item.validation.description
            }
            
            # Convert optimization
            optimization = {
                "max_component_spacing": config_item.optimization.max_component_spacing,
                "prefer_orthogonal_orientation": config_item.optimization.prefer_orthogonal_orientation,
                "max_orientation_angle": config_item.optimization.max_orientation_angle,
                "min_pad_size": config_item.optimization.min_pad_size,
                "max_via_size": config_item.optimization.max_via_size,
                "prefer_standard_grid": config_item.optimization.prefer_standard_grid,
                "description": config_item.optimization.description
            }
            
            # Convert cost analysis
            cost_analysis = {
                "cost_threshold": config_item.cost_analysis.cost_threshold,
                "yield_impact_threshold": config_item.cost_analysis.yield_impact_threshold,
                "sensitive_area_radius": config_item.cost_analysis.sensitive_area_radius,
                "min_component_spacing": config_item.cost_analysis.min_component_spacing,
                "description": config_item.cost_analysis.description
            }
            
            # Convert panelization
            panelization = {
                "panel_size_x": config_item.panelization.panel_size_x,
                "panel_size_y": config_item.panelization.panel_size_y,
                "board_spacing": config_item.panelization.board_spacing,
                "edge_clearance": config_item.panelization.edge_clearance,
                "fiducial_size": config_item.panelization.fiducial_size,
                "fiducial_clearance": config_item.panelization.fiducial_clearance,
                "description": config_item.panelization.description
            }
            
            # Convert thermal management
            thermal_management = {
                "max_temperature_rise": config_item.thermal_management.max_temperature_rise,
                "min_thermal_pad_size": config_item.thermal_management.min_thermal_pad_size,
                "thermal_resistance_factor": config_item.thermal_management.thermal_resistance_factor,
                "min_thermal_via_count": config_item.thermal_management.min_thermal_via_count,
                "description": config_item.thermal_management.description
            }
            
            # Convert quality control
            quality_control = {
                "min_test_point_size": config_item.quality_control.min_test_point_size,
                "min_test_point_clearance": config_item.quality_control.min_test_point_clearance,
                "require_fiducials": config_item.quality_control.require_fiducials,
                "require_test_points": config_item.quality_control.require_test_points,
                "min_solder_mask_clearance": config_item.quality_control.min_solder_mask_clearance,
                "description": config_item.quality_control.description
            }
            
            # Convert validation settings
            validation_settings = {
                "check_manufacturing": config_item.validation_settings.check_manufacturing,
                "check_manufacturing_optimization": config_item.validation_settings.check_manufacturing_optimization,
                "check_cost_analysis": config_item.validation_settings.check_cost_analysis,
                "check_panelization": config_item.validation_settings.check_panelization,
                "check_thermal_management": config_item.validation_settings.check_thermal_management,
                "check_quality_control": config_item.validation_settings.check_quality_control,
                "description": config_item.validation_settings.description
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
                "cost": config_item.units.cost,
                "temperature": config_item.units.temperature,
                "description": config_item.units.description
            }
            
            return {
                "manufacturing": {
                    "validation": validation,
                    "optimization": optimization,
                    "cost_analysis": cost_analysis,
                    "panelization": panelization,
                    "thermal_management": thermal_management,
                    "quality_control": quality_control,
                    "validation_settings": validation_settings,
                    "thresholds": thresholds,
                    "units": units,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing manufacturing configuration: {str(e)}")
            raise
    
    def get_validation_config(self) -> Optional[ManufacturingValidationConfigItem]:
        """Get manufacturing validation configuration.
        
        Returns:
            Manufacturing validation configuration
        """
        try:
            return self.config.validation
        except Exception as e:
            self.logger.error(f"Error getting manufacturing validation configuration: {str(e)}")
            return None
    
    def get_optimization_config(self) -> Optional[ManufacturingOptimizationConfigItem]:
        """Get manufacturing optimization configuration.
        
        Returns:
            Manufacturing optimization configuration
        """
        try:
            return self.config.optimization
        except Exception as e:
            self.logger.error(f"Error getting manufacturing optimization configuration: {str(e)}")
            return None
    
    def get_cost_analysis_config(self) -> Optional[CostAnalysisConfigItem]:
        """Get cost analysis configuration.
        
        Returns:
            Cost analysis configuration
        """
        try:
            return self.config.cost_analysis
        except Exception as e:
            self.logger.error(f"Error getting cost analysis configuration: {str(e)}")
            return None
    
    def get_panelization_config(self) -> Optional[PanelizationConfigItem]:
        """Get panelization configuration.
        
        Returns:
            Panelization configuration
        """
        try:
            return self.config.panelization
        except Exception as e:
            self.logger.error(f"Error getting panelization configuration: {str(e)}")
            return None
    
    def get_thermal_management_config(self) -> Optional[ThermalManagementConfigItem]:
        """Get thermal management configuration.
        
        Returns:
            Thermal management configuration
        """
        try:
            return self.config.thermal_management
        except Exception as e:
            self.logger.error(f"Error getting thermal management configuration: {str(e)}")
            return None
    
    def get_quality_control_config(self) -> Optional[QualityControlConfigItem]:
        """Get quality control configuration.
        
        Returns:
            Quality control configuration
        """
        try:
            return self.config.quality_control
        except Exception as e:
            self.logger.error(f"Error getting quality control configuration: {str(e)}")
            return None
    
    def get_validation_settings_config(self) -> Optional[ValidationConfigItem]:
        """Get validation settings configuration.
        
        Returns:
            Validation settings configuration
        """
        try:
            return self.config.validation_settings
        except Exception as e:
            self.logger.error(f"Error getting validation settings configuration: {str(e)}")
            return None
    
    def get_thresholds_config(self) -> Optional[ThresholdsConfigItem]:
        """Get thresholds configuration.
        
        Returns:
            Thresholds configuration
        """
        try:
            return self.config.thresholds
        except Exception as e:
            self.logger.error(f"Error getting thresholds configuration: {str(e)}")
            return None
    
    def get_units_config(self) -> Optional[UnitsConfigItem]:
        """Get units configuration.
        
        Returns:
            Units configuration
        """
        try:
            return self.config.units
        except Exception as e:
            self.logger.error(f"Error getting units configuration: {str(e)}")
            return None 