"""
Unified Layout Configuration Manager

This module provides comprehensive configuration management for all layout parameters,
combining basic layout settings with advanced optimization parameters.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..core.base.base_config import BaseConfig
from ..core.templates.board_presets import BoardProfile, board_preset_registry


@dataclass
class BoardSetupConfigItem:
    """Data structure for board setup parameters."""
    default_thickness: float
    default_copper_weight: int
    enabled_layers: List[str]
    board_profile: Optional[str] = None  # Board preset profile
    board_width_mm: Optional[float] = None
    board_height_mm: Optional[float] = None
    description: str = ""
    
    def get_board_preset(self) -> Optional[BoardProfile]:
        """Get the board profile enum if set.
        
        Returns:
            BoardProfile enum or None if not set
        """
        if self.board_profile:
            try:
                return BoardProfile(self.board_profile)
            except ValueError:
                return None
        return None
    
    def get_board_dimensions(self) -> Optional[tuple[float, float]]:
        """Get board dimensions from preset or custom values.
        
        Returns:
            Tuple of (width_mm, height_mm) or None if not available
        """
        if self.board_profile:
            profile = self.get_board_preset()
            if profile:
                preset = board_preset_registry.get_preset(profile)
                if preset:
                    return (preset.width_mm, preset.height_mm)
        
        if self.board_width_mm and self.board_height_mm:
            return (self.board_width_mm, self.board_height_mm)
        
        return None


@dataclass
class PlacementConfigItem:
    """Data structure for placement parameters."""
    margin_percentage: float
    center_spacing_percentage: float
    component_offset_percentage: float
    grid_spacing_percentage: float
    power_margin_multiplier: float
    description: str


@dataclass
class ComponentGroupConfigItem:
    """Data structure for component group parameters."""
    prefixes: List[str]
    placement_zone: str
    spacing_percentage: float
    priority: int
    thermal_consideration: bool
    description: str


@dataclass
class FerriteBeadConfigItem:
    """Data structure for ferrite bead parameters."""
    reference: str
    impedance: float
    current_rating: float
    description: str


@dataclass
class EMCFilterConfigItem:
    """Data structure for EMC filter parameters."""
    reference: str
    type: str
    cutoff_freq: float
    order: int
    attenuation: float
    description: str


@dataclass
class PowerFilterConfigItem:
    """Data structure for power filter parameters."""
    reference: str
    capacitance: float
    voltage_rating: float
    description: str


@dataclass
class AudioFilterConfigItem:
    """Data structure for audio filter parameters."""
    reference: str
    type: str
    cutoff_freq: float
    order: int
    ripple: float
    description: str


@dataclass
class PlacementZoneConfigItem:
    """Data structure for placement zone parameters."""
    x_percentage: float
    y_percentage: float
    description: str


@dataclass
class RoutingConfigItem:
    """Data structure for routing parameters."""
    min_track_width: float
    min_clearance: float
    via_diameter: float
    via_drill: float
    min_track_spacing: float
    max_track_length: float
    via_preference: float
    layer_preference: Dict[str, List[str]]
    description: str


@dataclass
class LayoutConstraintsConfigItem:
    """Data structure for layout optimization constraints."""
    min_track_width: float
    min_clearance: float
    min_via_size: float
    max_component_density: float
    max_track_density: float
    min_thermal_pad_size: float
    max_parallel_tracks: int
    min_power_track_width: float
    max_high_speed_length: float
    description: str


@dataclass
class OptimizationConfigItem:
    """Data structure for optimization parameters."""
    max_iterations: int
    convergence_threshold: float
    improvement_threshold: float
    cache_size: int
    memoization_cache_size: int
    position_evaluation_cache_size: int
    description: str


@dataclass
class ComponentPlacementConfigItem:
    """Data structure for component placement parameters."""
    margin_percentage: float
    spacing_percentage: float
    group_spacing_percentage: float
    thermal_zone_margin: float
    power_zone_margin: float
    signal_zone_margin: float
    description: str


@dataclass
class ThermalManagementConfigItem:
    """Data structure for thermal management parameters."""
    max_temperature_rise: float
    thermal_resistance_factor: float
    heat_dissipation_threshold: float
    thermal_pad_spacing: float
    thermal_via_count: int
    description: str


@dataclass
class SignalIntegrityConfigItem:
    """Data structure for signal integrity parameters."""
    max_crosstalk: float
    max_reflection: float
    impedance_tolerance: float
    max_parallel_length: float
    min_isolation_distance: float
    description: str


@dataclass
class AIAnalysisConfigItem:
    """Data structure for AI analysis parameters."""
    feature_weights: Dict[str, float]
    recommendation_threshold: float
    analysis_depth: int
    description: str


@dataclass
class ValidationConfigItem:
    """Data structure for validation settings."""
    check_component_placement: bool
    check_stability_components: bool
    check_routing: bool
    check_power_planes: bool
    check_ground_planes: bool
    check_constraints: bool
    check_thermal: bool
    check_signal_integrity: bool
    description: str


@dataclass
class LayoutConfigItem:
    """Data structure for unified layout configuration."""
    # Basic layout parameters
    board_setup: BoardSetupConfigItem
    placement: PlacementConfigItem
    component_groups: Dict[str, ComponentGroupConfigItem]
    stability_components: Dict[str, Dict[str, Union[FerriteBeadConfigItem, EMCFilterConfigItem, PowerFilterConfigItem, AudioFilterConfigItem]]]
    placement_zones: Dict[str, PlacementZoneConfigItem]
    routing: RoutingConfigItem
    validation: ValidationConfigItem
    
    # Advanced optimization parameters
    constraints: LayoutConstraintsConfigItem
    optimization: OptimizationConfigItem
    component_placement: ComponentPlacementConfigItem
    thermal_management: ThermalManagementConfigItem
    signal_integrity: SignalIntegrityConfigItem
    ai_analysis: AIAnalysisConfigItem
    
    description: str


class LayoutConfig(BaseConfig[LayoutConfigItem]):
    """Unified configuration manager for all layout parameters."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """Initialize the unified layout configuration.
        
        Args:
            config_path: Path to configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent / "layout_config.json"
        
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
            # Validate basic layout section
            if "layout" not in config_data:
                self.logger.error("Missing 'layout' section in configuration")
                return False
            
            layout_config = config_data["layout"]
            
            # Validate board setup
            if "board_setup" not in layout_config:
                self.logger.error("Missing 'board_setup' section in layout")
                return False
            
            board_setup = layout_config["board_setup"]
            if board_setup["default_thickness"] <= 0:
                self.logger.error("Board thickness must be positive")
                return False
            
            if board_setup["default_copper_weight"] <= 0:
                self.logger.error("Copper weight must be positive")
                return False
            
            if not board_setup["enabled_layers"]:
                self.logger.error("Enabled layers list cannot be empty")
                return False
            
            # Validate placement
            if "placement" not in layout_config:
                self.logger.error("Missing 'placement' section in layout")
                return False
            
            placement = layout_config["placement"]
            if placement["margin_percentage"] <= 0 or placement["margin_percentage"] >= 1:
                self.logger.error("Margin percentage must be between 0 and 1")
                return False
            
            if placement["center_spacing_percentage"] <= 0 or placement["center_spacing_percentage"] >= 1:
                self.logger.error("Center spacing percentage must be between 0 and 1")
                return False
            
            # Validate component groups
            if "component_groups" not in layout_config:
                self.logger.error("Missing 'component_groups' section in layout")
                return False
            
            component_groups = layout_config["component_groups"]
            required_groups = ["opamps", "connectors", "passives", "power"]
            for group in required_groups:
                if group not in component_groups:
                    self.logger.error(f"Missing component group '{group}'")
                    return False
            
            # Validate stability components
            if "stability_components" not in layout_config:
                self.logger.error("Missing 'stability_components' section in layout")
                return False
            
            # Validate placement zones
            if "placement_zones" not in layout_config:
                self.logger.error("Missing 'placement_zones' section in layout")
                return False
            
            # Validate routing
            if "routing" not in layout_config:
                self.logger.error("Missing 'routing' section in layout")
                return False
            
            routing = layout_config["routing"]
            if routing["min_track_width"] <= 0:
                self.logger.error("Minimum track width must be positive")
                return False
            
            if routing["min_clearance"] <= 0:
                self.logger.error("Minimum clearance must be positive")
                return False
            
            # Validate validation settings
            if "validation" not in layout_config:
                self.logger.error("Missing 'validation' section in layout")
                return False
            
            # Validate optimization section
            if "optimization" not in config_data:
                self.logger.error("Missing 'optimization' section in configuration")
                return False
            
            opt_config = config_data["optimization"]
            
            # Validate constraints
            if "constraints" not in opt_config:
                self.logger.error("Missing 'constraints' section in optimization")
                return False
            
            constraints = opt_config["constraints"]
            if constraints["min_track_width"] <= 0:
                self.logger.error("Minimum track width must be positive")
                return False
            
            if constraints["min_clearance"] <= 0:
                self.logger.error("Minimum clearance must be positive")
                return False
            
            if constraints["max_component_density"] <= 0:
                self.logger.error("Maximum component density must be positive")
                return False
            
            if constraints["max_parallel_tracks"] <= 0:
                self.logger.error("Maximum parallel tracks must be positive")
                return False
            
            # Validate optimization settings
            if "optimization" not in opt_config:
                self.logger.error("Missing 'optimization' section in optimization")
                return False
            
            optimization = opt_config["optimization"]
            if optimization["max_iterations"] <= 0:
                self.logger.error("Maximum iterations must be positive")
                return False
            
            if optimization["convergence_threshold"] <= 0:
                self.logger.error("Convergence threshold must be positive")
                return False
            
            if optimization["cache_size"] <= 0:
                self.logger.error("Cache size must be positive")
                return False
            
            # Validate component placement
            if "component_placement" not in opt_config:
                self.logger.error("Missing 'component_placement' section in optimization")
                return False
            
            # Validate thermal management
            if "thermal_management" not in opt_config:
                self.logger.error("Missing 'thermal_management' section in optimization")
                return False
            
            # Validate signal integrity
            if "signal_integrity" not in opt_config:
                self.logger.error("Missing 'signal_integrity' section in optimization")
                return False
            
            # Validate AI analysis
            if "ai_analysis" not in opt_config:
                self.logger.error("Missing 'ai_analysis' section in optimization")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating layout configuration: {str(e)}")
            return False
    
    def _parse_config(self, config_data: dict) -> LayoutConfigItem:
        """Parse configuration data into structured format.
        
        Args:
            config_data: Raw configuration data
            
        Returns:
            Parsed configuration item
        """
        try:
            layout_config = config_data["layout"]
            
            # Parse board setup
            board_setup_config = layout_config["board_setup"]
            board_setup = BoardSetupConfigItem(
                default_thickness=board_setup_config["default_thickness"],
                default_copper_weight=board_setup_config["default_copper_weight"],
                enabled_layers=board_setup_config["enabled_layers"],
                board_profile=board_setup_config.get("board_profile"),
                board_width_mm=board_setup_config.get("board_width_mm"),
                board_height_mm=board_setup_config.get("board_height_mm"),
                description=board_setup_config["description"]
            )
            
            # Parse placement
            placement_config = layout_config["placement"]
            placement = PlacementConfigItem(
                margin_percentage=placement_config["margin_percentage"],
                center_spacing_percentage=placement_config["center_spacing_percentage"],
                component_offset_percentage=placement_config["component_offset_percentage"],
                grid_spacing_percentage=placement_config["grid_spacing_percentage"],
                power_margin_multiplier=placement_config["power_margin_multiplier"],
                description=placement_config["description"]
            )
            
            # Parse component groups
            component_groups_config = layout_config["component_groups"]
            component_groups = {}
            for group_name, group_config in component_groups_config.items():
                component_groups[group_name] = ComponentGroupConfigItem(
                    prefixes=group_config["prefixes"],
                    placement_zone=group_config["placement_zone"],
                    spacing_percentage=group_config["spacing_percentage"],
                    priority=group_config["priority"],
                    thermal_consideration=group_config["thermal_consideration"],
                    description=group_config["description"]
                )
            
            # Parse stability components
            stability_config = layout_config["stability_components"]
            stability_components = {}
            
            # Parse ferrite beads
            ferrite_config = stability_config["ferrite_beads"]
            stability_components["ferrite_beads"] = {}
            for bead_name, bead_config in ferrite_config.items():
                stability_components["ferrite_beads"][bead_name] = FerriteBeadConfigItem(
                    reference=bead_config["reference"],
                    impedance=bead_config["impedance"],
                    current_rating=bead_config["current_rating"],
                    description=bead_config["description"]
                )
            
            # Parse EMC filters
            emc_config = stability_config["emc_filters"]
            stability_components["emc_filters"] = {}
            for filter_name, filter_config in emc_config.items():
                stability_components["emc_filters"][filter_name] = EMCFilterConfigItem(
                    reference=filter_config["reference"],
                    type=filter_config["type"],
                    cutoff_freq=filter_config["cutoff_freq"],
                    order=filter_config["order"],
                    attenuation=filter_config["attenuation"],
                    description=filter_config["description"]
                )
            
            # Parse power filters
            power_config = stability_config["power_filters"]
            stability_components["power_filters"] = {}
            for filter_name, filter_config in power_config.items():
                stability_components["power_filters"][filter_name] = PowerFilterConfigItem(
                    reference=filter_config["reference"],
                    capacitance=filter_config["capacitance"],
                    voltage_rating=filter_config["voltage_rating"],
                    description=filter_config["description"]
                )
            
            # Parse audio filters
            audio_config = stability_config["audio_filters"]
            stability_components["audio_filters"] = {}
            for filter_name, filter_config in audio_config.items():
                stability_components["audio_filters"][filter_name] = AudioFilterConfigItem(
                    reference=filter_config["reference"],
                    type=filter_config["type"],
                    cutoff_freq=filter_config["cutoff_freq"],
                    order=filter_config["order"],
                    ripple=filter_config["ripple"],
                    description=filter_config["description"]
                )
            
            # Parse placement zones
            zones_config = layout_config["placement_zones"]
            placement_zones = {}
            for zone_name, zone_config in zones_config.items():
                placement_zones[zone_name] = PlacementZoneConfigItem(
                    x_percentage=zone_config["x_percentage"],
                    y_percentage=zone_config["y_percentage"],
                    description=zone_config["description"]
                )
            
            # Parse routing
            routing_config = layout_config["routing"]
            routing = RoutingConfigItem(
                min_track_width=routing_config["min_track_width"],
                min_clearance=routing_config["min_clearance"],
                via_diameter=routing_config["via_diameter"],
                via_drill=routing_config["via_drill"],
                min_track_spacing=routing_config["min_track_spacing"],
                max_track_length=routing_config["max_track_length"],
                via_preference=routing_config["via_preference"],
                layer_preference=routing_config["layer_preference"],
                description=routing_config["description"]
            )
            
            # Parse validation
            validation_config = layout_config["validation"]
            validation = ValidationConfigItem(
                check_component_placement=validation_config["check_component_placement"],
                check_stability_components=validation_config["check_stability_components"],
                check_routing=validation_config["check_routing"],
                check_power_planes=validation_config["check_power_planes"],
                check_ground_planes=validation_config["check_ground_planes"],
                check_constraints=validation_config["check_constraints"],
                check_thermal=validation_config["check_thermal"],
                check_signal_integrity=validation_config["check_signal_integrity"],
                description=validation_config["description"]
            )
            
            # Parse optimization
            optimization_config = config_data["optimization"]
            optimization = OptimizationConfigItem(
                max_iterations=optimization_config["max_iterations"],
                convergence_threshold=optimization_config["convergence_threshold"],
                improvement_threshold=optimization_config["improvement_threshold"],
                cache_size=optimization_config["cache_size"],
                memoization_cache_size=optimization_config["memoization_cache_size"],
                position_evaluation_cache_size=optimization_config["position_evaluation_cache_size"],
                description=optimization_config["description"]
            )
            
            # Parse component placement
            component_placement_config = optimization_config["component_placement"]
            component_placement = ComponentPlacementConfigItem(
                margin_percentage=component_placement_config["margin_percentage"],
                spacing_percentage=component_placement_config["spacing_percentage"],
                group_spacing_percentage=component_placement_config["group_spacing_percentage"],
                thermal_zone_margin=component_placement_config["thermal_zone_margin"],
                power_zone_margin=component_placement_config["power_zone_margin"],
                signal_zone_margin=component_placement_config["signal_zone_margin"],
                description=component_placement_config["description"]
            )
            
            # Parse thermal management
            thermal_management_config = optimization_config["thermal_management"]
            thermal_management = ThermalManagementConfigItem(
                max_temperature_rise=thermal_management_config["max_temperature_rise"],
                thermal_resistance_factor=thermal_management_config["thermal_resistance_factor"],
                heat_dissipation_threshold=thermal_management_config["heat_dissipation_threshold"],
                thermal_pad_spacing=thermal_management_config["thermal_pad_spacing"],
                thermal_via_count=thermal_management_config["thermal_via_count"],
                description=thermal_management_config["description"]
            )
            
            # Parse signal integrity
            signal_integrity_config = optimization_config["signal_integrity"]
            signal_integrity = SignalIntegrityConfigItem(
                max_crosstalk=signal_integrity_config["max_crosstalk"],
                max_reflection=signal_integrity_config["max_reflection"],
                impedance_tolerance=signal_integrity_config["impedance_tolerance"],
                max_parallel_length=signal_integrity_config["max_parallel_length"],
                min_isolation_distance=signal_integrity_config["min_isolation_distance"],
                description=signal_integrity_config["description"]
            )
            
            # Parse AI analysis
            ai_analysis_config = optimization_config["ai_analysis"]
            ai_analysis = AIAnalysisConfigItem(
                feature_weights=ai_analysis_config["feature_weights"],
                recommendation_threshold=ai_analysis_config["recommendation_threshold"],
                analysis_depth=ai_analysis_config["analysis_depth"],
                description=ai_analysis_config["description"]
            )
            
            # Parse constraints
            constraints_config = optimization_config["constraints"]
            constraints = LayoutConstraintsConfigItem(
                min_track_width=constraints_config["min_track_width"],
                min_clearance=constraints_config["min_clearance"],
                min_via_size=constraints_config["min_via_size"],
                max_component_density=constraints_config["max_component_density"],
                max_track_density=constraints_config["max_track_density"],
                min_thermal_pad_size=constraints_config["min_thermal_pad_size"],
                max_parallel_tracks=constraints_config["max_parallel_tracks"],
                min_power_track_width=constraints_config["min_power_track_width"],
                max_high_speed_length=constraints_config["max_high_speed_length"],
                description=constraints_config["description"]
            )
            
            return LayoutConfigItem(
                board_setup=board_setup,
                placement=placement,
                component_groups=component_groups,
                stability_components=stability_components,
                placement_zones=placement_zones,
                routing=routing,
                validation=validation,
                constraints=constraints,
                optimization=optimization,
                component_placement=component_placement,
                thermal_management=thermal_management,
                signal_integrity=signal_integrity,
                ai_analysis=ai_analysis,
                description=layout_config.get("description", "Layout configuration")
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing layout configuration: {str(e)}")
            raise
    
    def _prepare_config_data(self, config_item: LayoutConfigItem) -> dict:
        """Prepare configuration item for serialization.
        
        Args:
            config_item: Configuration item to serialize
            
        Returns:
            Dictionary representation of configuration
        """
        try:
            # Convert board setup
            board_setup = {
                "default_thickness": config_item.board_setup.default_thickness,
                "default_copper_weight": config_item.board_setup.default_copper_weight,
                "enabled_layers": config_item.board_setup.enabled_layers,
                "board_profile": config_item.board_setup.board_profile,
                "board_width_mm": config_item.board_setup.board_width_mm,
                "board_height_mm": config_item.board_setup.board_height_mm,
                "description": config_item.board_setup.description
            }
            
            # Convert placement
            placement = {
                "margin_percentage": config_item.placement.margin_percentage,
                "center_spacing_percentage": config_item.placement.center_spacing_percentage,
                "component_offset_percentage": config_item.placement.component_offset_percentage,
                "grid_spacing_percentage": config_item.placement.grid_spacing_percentage,
                "power_margin_multiplier": config_item.placement.power_margin_multiplier,
                "description": config_item.placement.description
            }
            
            # Convert component groups
            component_groups = {}
            for group_name, group_config in config_item.component_groups.items():
                component_groups[group_name] = {
                    "prefixes": group_config.prefixes,
                    "placement_zone": group_config.placement_zone,
                    "spacing_percentage": group_config.spacing_percentage,
                    "priority": group_config.priority,
                    "thermal_consideration": group_config.thermal_consideration,
                    "description": group_config.description
                }
            
            # Convert stability components
            stability_components = {}
            
            # Convert ferrite beads
            ferrite_beads = {}
            for bead_name, bead_config in config_item.stability_components["ferrite_beads"].items():
                ferrite_beads[bead_name] = {
                    "reference": bead_config.reference,
                    "impedance": bead_config.impedance,
                    "current_rating": bead_config.current_rating,
                    "description": bead_config.description
                }
            stability_components["ferrite_beads"] = ferrite_beads
            
            # Convert EMC filters
            emc_filters = {}
            for filter_name, filter_config in config_item.stability_components["emc_filters"].items():
                emc_filters[filter_name] = {
                    "reference": filter_config.reference,
                    "type": filter_config.type,
                    "cutoff_freq": filter_config.cutoff_freq,
                    "order": filter_config.order,
                    "attenuation": filter_config.attenuation,
                    "description": filter_config.description
                }
            stability_components["emc_filters"] = emc_filters
            
            # Convert power filters
            power_filters = {}
            for filter_name, filter_config in config_item.stability_components["power_filters"].items():
                power_filters[filter_name] = {
                    "reference": filter_config.reference,
                    "capacitance": filter_config.capacitance,
                    "voltage_rating": filter_config.voltage_rating,
                    "description": filter_config.description
                }
            stability_components["power_filters"] = power_filters
            
            # Convert audio filters
            audio_filters = {}
            for filter_name, filter_config in config_item.stability_components["audio_filters"].items():
                audio_filters[filter_name] = {
                    "reference": filter_config.reference,
                    "type": filter_config.type,
                    "cutoff_freq": filter_config.cutoff_freq,
                    "order": filter_config.order,
                    "ripple": filter_config.ripple,
                    "description": filter_config.description
                }
            stability_components["audio_filters"] = audio_filters
            
            # Convert placement zones
            placement_zones = {}
            for zone_name, zone_config in config_item.placement_zones.items():
                placement_zones[zone_name] = {
                    "x_percentage": zone_config.x_percentage,
                    "y_percentage": zone_config.y_percentage,
                    "description": zone_config.description
                }
            
            # Convert routing
            routing = {
                "min_track_width": config_item.routing.min_track_width,
                "min_clearance": config_item.routing.min_clearance,
                "via_diameter": config_item.routing.via_diameter,
                "via_drill": config_item.routing.via_drill,
                "min_track_spacing": config_item.routing.min_track_spacing,
                "max_track_length": config_item.routing.max_track_length,
                "via_preference": config_item.routing.via_preference,
                "layer_preference": config_item.routing.layer_preference,
                "description": config_item.routing.description
            }
            
            # Convert validation
            validation = {
                "check_component_placement": config_item.validation.check_component_placement,
                "check_stability_components": config_item.validation.check_stability_components,
                "check_routing": config_item.validation.check_routing,
                "check_power_planes": config_item.validation.check_power_planes,
                "check_ground_planes": config_item.validation.check_ground_planes,
                "check_constraints": config_item.validation.check_constraints,
                "check_thermal": config_item.validation.check_thermal,
                "check_signal_integrity": config_item.validation.check_signal_integrity,
                "description": config_item.validation.description
            }
            
            # Convert constraints
            constraints = {
                "min_track_width": config_item.constraints.min_track_width,
                "min_clearance": config_item.constraints.min_clearance,
                "min_via_size": config_item.constraints.min_via_size,
                "max_component_density": config_item.constraints.max_component_density,
                "max_track_density": config_item.constraints.max_track_density,
                "min_thermal_pad_size": config_item.constraints.min_thermal_pad_size,
                "max_parallel_tracks": config_item.constraints.max_parallel_tracks,
                "min_power_track_width": config_item.constraints.min_power_track_width,
                "max_high_speed_length": config_item.constraints.max_high_speed_length,
                "description": config_item.constraints.description
            }
            
            # Convert optimization
            optimization = {
                "max_iterations": config_item.optimization.max_iterations,
                "convergence_threshold": config_item.optimization.convergence_threshold,
                "improvement_threshold": config_item.optimization.improvement_threshold,
                "cache_size": config_item.optimization.cache_size,
                "memoization_cache_size": config_item.optimization.memoization_cache_size,
                "position_evaluation_cache_size": config_item.optimization.position_evaluation_cache_size,
                "description": config_item.optimization.description
            }
            
            # Convert component placement
            component_placement = {
                "margin_percentage": config_item.component_placement.margin_percentage,
                "spacing_percentage": config_item.component_placement.spacing_percentage,
                "group_spacing_percentage": config_item.component_placement.group_spacing_percentage,
                "thermal_zone_margin": config_item.component_placement.thermal_zone_margin,
                "power_zone_margin": config_item.component_placement.power_zone_margin,
                "signal_zone_margin": config_item.component_placement.signal_zone_margin,
                "description": config_item.component_placement.description
            }
            
            # Convert thermal management
            thermal_management = {
                "max_temperature_rise": config_item.thermal_management.max_temperature_rise,
                "thermal_resistance_factor": config_item.thermal_management.thermal_resistance_factor,
                "heat_dissipation_threshold": config_item.thermal_management.heat_dissipation_threshold,
                "thermal_pad_spacing": config_item.thermal_management.thermal_pad_spacing,
                "thermal_via_count": config_item.thermal_management.thermal_via_count,
                "description": config_item.thermal_management.description
            }
            
            # Convert signal integrity
            signal_integrity = {
                "max_crosstalk": config_item.signal_integrity.max_crosstalk,
                "max_reflection": config_item.signal_integrity.max_reflection,
                "impedance_tolerance": config_item.signal_integrity.impedance_tolerance,
                "max_parallel_length": config_item.signal_integrity.max_parallel_length,
                "min_isolation_distance": config_item.signal_integrity.min_isolation_distance,
                "description": config_item.signal_integrity.description
            }
            
            # Convert AI analysis
            ai_analysis = {
                "feature_weights": config_item.ai_analysis.feature_weights,
                "recommendation_threshold": config_item.ai_analysis.recommendation_threshold,
                "analysis_depth": config_item.ai_analysis.analysis_depth,
                "description": config_item.ai_analysis.description
            }
            
            return {
                "layout": {
                    "board_setup": board_setup,
                    "placement": placement,
                    "component_groups": component_groups,
                    "stability_components": stability_components,
                    "placement_zones": placement_zones,
                    "routing": routing,
                    "validation": validation,
                    "constraints": constraints,
                    "optimization": optimization,
                    "component_placement": component_placement,
                    "thermal_management": thermal_management,
                    "signal_integrity": signal_integrity,
                    "ai_analysis": ai_analysis,
                    "description": config_item.description
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing layout configuration: {str(e)}")
            raise
    
    def get_board_setup_config(self) -> Optional[BoardSetupConfigItem]:
        """Get board setup configuration.
        
        Returns:
            Board setup configuration
        """
        try:
            config = self.get_config()
            return config.board_setup
        except Exception as e:
            self.logger.error(f"Error getting board setup configuration: {str(e)}")
            return None
    
    def get_placement_config(self) -> Optional[PlacementConfigItem]:
        """Get placement configuration.
        
        Returns:
            Placement configuration
        """
        try:
            config = self.get_config()
            return config.placement
        except Exception as e:
            self.logger.error(f"Error getting placement configuration: {str(e)}")
            return None
    
    def get_component_group_config(self, group_name: str) -> Optional[ComponentGroupConfigItem]:
        """Get component group configuration.
        
        Args:
            group_name: Name of the component group
            
        Returns:
            Component group configuration
        """
        try:
            config = self.get_config()
            return config.component_groups.get(group_name)
        except Exception as e:
            self.logger.error(f"Error getting component group configuration for {group_name}: {str(e)}")
            return None
    
    def get_stability_component_config(self, component_type: str, component_name: str) -> Optional[Union[FerriteBeadConfigItem, EMCFilterConfigItem, PowerFilterConfigItem, AudioFilterConfigItem]]:
        """Get stability component configuration.
        
        Args:
            component_type: Type of stability component (ferrite_beads, emc_filters, power_filters, audio_filters)
            component_name: Name of the component
            
        Returns:
            Stability component configuration
        """
        try:
            config = self.get_config()
            return config.stability_components.get(component_type, {}).get(component_name)
        except Exception as e:
            self.logger.error(f"Error getting stability component configuration for {component_type}/{component_name}: {str(e)}")
            return None
    
    def get_placement_zone_config(self, zone_name: str) -> Optional[PlacementZoneConfigItem]:
        """Get placement zone configuration.
        
        Args:
            zone_name: Name of the placement zone
            
        Returns:
            Placement zone configuration
        """
        try:
            config = self.get_config()
            return config.placement_zones.get(zone_name)
        except Exception as e:
            self.logger.error(f"Error getting placement zone configuration for {zone_name}: {str(e)}")
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
    
    def get_validation_config(self) -> Optional[ValidationConfigItem]:
        """Get validation configuration.
        
        Returns:
            Validation configuration
        """
        try:
            return self.config.validation
        except Exception as e:
            self.logger.error(f"Error getting validation configuration: {str(e)}")
            return None
    
    def get_constraints_config(self) -> Optional[LayoutConstraintsConfigItem]:
        """Get layout constraints configuration.
        
        Returns:
            Layout constraints configuration
        """
        try:
            return self.config.constraints
        except Exception as e:
            self.logger.error(f"Error getting layout constraints configuration: {str(e)}")
            return None
    
    def get_optimization_config(self) -> Optional[OptimizationConfigItem]:
        """Get optimization configuration.
        
        Returns:
            Optimization configuration
        """
        try:
            return self.config.optimization
        except Exception as e:
            self.logger.error(f"Error getting optimization configuration: {str(e)}")
            return None
    
    def get_component_placement_config(self) -> Optional[ComponentPlacementConfigItem]:
        """Get component placement configuration.
        
        Returns:
            Component placement configuration
        """
        try:
            return self.config.component_placement
        except Exception as e:
            self.logger.error(f"Error getting component placement configuration: {str(e)}")
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
    
    def get_signal_integrity_config(self) -> Optional[SignalIntegrityConfigItem]:
        """Get signal integrity configuration.
        
        Returns:
            Signal integrity configuration
        """
        try:
            return self.config.signal_integrity
        except Exception as e:
            self.logger.error(f"Error getting signal integrity configuration: {str(e)}")
            return None
    
    def get_ai_analysis_config(self) -> Optional[AIAnalysisConfigItem]:
        """Get AI analysis configuration.
        
        Returns:
            AI analysis configuration
        """
        try:
            return self.config.ai_analysis
        except Exception as e:
            self.logger.error(f"Error getting AI analysis configuration: {str(e)}")
            return None 