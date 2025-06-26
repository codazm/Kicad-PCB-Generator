"""Base template system for audio circuits."""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from ..components import ComponentManager, ComponentData

@dataclass
class LayerStack:
    """PCB layer stack configuration."""
    name: str
    layers: List[str]
    thickness: Dict[str, float]
    material: Dict[str, str]
    dielectric: Dict[str, float]

@dataclass
class ZoneSettings:
    """PCB zone settings."""
    name: str
    layer: str
    net: str
    priority: int
    fill_mode: str
    thermal_gap: float
    thermal_bridge_width: float
    min_thickness: float
    keep_islands: bool
    smoothing: bool

@dataclass
class DesignVariant:
    """PCB design variant."""
    name: str
    description: str
    components: Dict[str, ComponentData]
    nets: Dict[str, List[str]]
    rules: Dict[str, Any]

class TemplateBase:
    """Base template for audio circuits.
    
    This class provides the foundation for all audio circuit templates,
    handling common functionality like component management, layer stacks,
    and design rules.
    """
    
    def __init__(self, base_path: str, logger: Optional[logging.Logger] = None):
        """Initialize template.
        
        Args:
            base_path: Base path for template data
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.base_path = Path(base_path)
        self.component_manager = ComponentManager(str(self.base_path / "components"), logger=self.logger)
        
        # Template data
        self.name: str = ""
        self.description: str = ""
        self.version: str = "1.0.0"
        self.layer_stack: Optional[LayerStack] = None
        self.zones: Dict[str, ZoneSettings] = {}
        self.variants: Dict[str, DesignVariant] = {}
        self.rules: Dict[str, Any] = {}
        
        # Create necessary directories
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def load_template(self, template_path: str) -> bool:
        """Load template from file.
        
        Args:
            template_path: Path to template file
            
        Returns:
            True if successful
        """
        try:
            template_file = Path(template_path)
            if not template_file.exists():
                self.logger.error(f"Template file not found: {template_path}")
                return False
            
            with open(template_file, "r") as f:
                data = json.load(f)
            
            # Load basic info
            self.name = data["name"]
            self.description = data["description"]
            self.version = data["version"]
            
            # Load layer stack
            if "layer_stack" in data:
                stack_data = data["layer_stack"]
                self.layer_stack = LayerStack(
                    name=stack_data["name"],
                    layers=stack_data["layers"],
                    thickness=stack_data["thickness"],
                    material=stack_data["material"],
                    dielectric=stack_data["dielectric"]
                )
            
            # Load zones
            if "zones" in data:
                for zone_name, zone_data in data["zones"].items():
                    self.zones[zone_name] = ZoneSettings(
                        name=zone_name,
                        layer=zone_data["layer"],
                        net=zone_data["net"],
                        priority=zone_data["priority"],
                        fill_mode=zone_data["fill_mode"],
                        thermal_gap=zone_data["thermal_gap"],
                        thermal_bridge_width=zone_data["thermal_bridge_width"],
                        min_thickness=zone_data["min_thickness"],
                        keep_islands=zone_data["keep_islands"],
                        smoothing=zone_data["smoothing"]
                    )
            
            # Load variants
            if "variants" in data:
                for variant_name, variant_data in data["variants"].items():
                    # Load components
                    components = {}
                    for comp_id, comp_data in variant_data["components"].items():
                        components[comp_id] = ComponentData.from_dict(comp_data)
                    
                    self.variants[variant_name] = DesignVariant(
                        name=variant_name,
                        description=variant_data["description"],
                        components=components,
                        nets=variant_data["nets"],
                        rules=variant_data["rules"]
                    )
            
            # Load rules
            if "rules" in data:
                self.rules = data["rules"]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load template: {e}")
            return False
    
    def save_template(self, template_path: str) -> bool:
        """Save template to file.
        
        Args:
            template_path: Path to template file
            
        Returns:
            True if successful
        """
        try:
            # Prepare data
            data = {
                "name": self.name,
                "description": self.description,
                "version": self.version
            }
            
            # Save layer stack
            if self.layer_stack:
                data["layer_stack"] = {
                    "name": self.layer_stack.name,
                    "layers": self.layer_stack.layers,
                    "thickness": self.layer_stack.thickness,
                    "material": self.layer_stack.material,
                    "dielectric": self.layer_stack.dielectric
                }
            
            # Save zones
            data["zones"] = {
                zone_name: {
                    "layer": zone.layer,
                    "net": zone.net,
                    "priority": zone.priority,
                    "fill_mode": zone.fill_mode,
                    "thermal_gap": zone.thermal_gap,
                    "thermal_bridge_width": zone.thermal_bridge_width,
                    "min_thickness": zone.min_thickness,
                    "keep_islands": zone.keep_islands,
                    "smoothing": zone.smoothing
                }
                for zone_name, zone in self.zones.items()
            }
            
            # Save variants
            data["variants"] = {
                variant_name: {
                    "description": variant.description,
                    "components": {
                        comp_id: comp.to_dict()
                        for comp_id, comp in variant.components.items()
                    },
                    "nets": variant.nets,
                    "rules": variant.rules
                }
                for variant_name, variant in self.variants.items()
            }
            
            # Save rules
            data["rules"] = self.rules
            
            # Save to file
            template_file = Path(template_path)
            with open(template_file, "w") as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save template: {e}")
            return False
    
    def get_layer_stack(self) -> Optional[LayerStack]:
        """Get layer stack.
        
        Returns:
            Layer stack if set
        """
        return self.layer_stack
    
    def get_zone_settings(self, zone_name: str) -> Optional[ZoneSettings]:
        """Get zone settings.
        
        Args:
            zone_name: Zone name
            
        Returns:
            Zone settings if found
        """
        return self.zones.get(zone_name)
    
    def get_design_variant(self, variant_name: str) -> Optional[DesignVariant]:
        """Get design variant.
        
        Args:
            variant_name: Variant name
            
        Returns:
            Design variant if found
        """
        return self.variants.get(variant_name)
    
    def get_components(self) -> Dict[str, ComponentData]:
        """Get all components.
        
        Returns:
            Dictionary of components
        """
        return self.component_manager.get_components()
    
    def get_nets(self) -> Dict[str, List[str]]:
        """Get all nets.
        
        Returns:
            Dictionary of nets
        """
        nets = {}
        for variant in self.variants.values():
            nets.update(variant.nets)
        return nets
    
    def get_design_rules(self) -> Dict[str, Any]:
        """Get design rules.
        
        Returns:
            Dictionary of design rules
        """
        return self.rules
    
    def validate_template(self) -> bool:
        """Validate template.
        
        Returns:
            True if valid
        """
        try:
            # Check required fields
            if not self.name or not self.description or not self.version:
                self.logger.error("Missing required fields")
                return False
            
            # Validate layer stack
            if self.layer_stack:
                if not self._validate_layer_stack(self.layer_stack):
                    return False
            
            # Validate components
            for component in self.component_manager.get_components().values():
                if not self.component_manager._validate_component(component):
                    return False
            
            # Validate nets
            for net_name, connections in self.get_nets().items():
                if not net_name or not isinstance(connections, list):
                    self.logger.error(f"Invalid net: {net_name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate template: {e}")
            return False
    
    def _validate_layer_stack(self, layer_stack: LayerStack) -> bool:
        """Validate layer stack.
        
        Args:
            layer_stack: Layer stack to validate
            
        Returns:
            True if valid
        """
        try:
            # Check required fields
            if not layer_stack.name or not layer_stack.layers:
                self.logger.error("Missing required layer stack fields")
                return False
            
            # Check layer consistency
            if not all(layer in layer_stack.thickness for layer in layer_stack.layers):
                self.logger.error("Missing thickness for some layers")
                return False
            
            if not all(layer in layer_stack.material for layer in layer_stack.layers):
                self.logger.error("Missing material for some layers")
                return False
            
            if not all(layer in layer_stack.dielectric for layer in layer_stack.layers):
                self.logger.error("Missing dielectric for some layers")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate layer stack: {e}")
            return False 