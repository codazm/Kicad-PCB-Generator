"""Tests for base template system."""
import json
import pytest
from pathlib import Path

from kicad_pcb_generator.core.templates.base import (
    TemplateBase,
    LayerStack,
    ZoneSettings,
    DesignVariant,
    ComponentData
)

def test_layer_stack_creation():
    """Test layer stack creation."""
    # Create layer stack
    layer_stack = LayerStack(
        name="4-Layer Stack",
        layers=["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
        thickness={
            "F.Cu": 0.035,
            "In1.Cu": 0.035,
            "In2.Cu": 0.035,
            "B.Cu": 0.035
        },
        material={
            "F.Cu": "Copper",
            "In1.Cu": "Copper",
            "In2.Cu": "Copper",
            "B.Cu": "Copper"
        },
        dielectric={
            "F.Cu": 0.1,
            "In1.Cu": 0.1,
            "In2.Cu": 0.1,
            "B.Cu": 0.1
        }
    )
    
    # Check attributes
    assert layer_stack.name == "4-Layer Stack"
    assert len(layer_stack.layers) == 4
    assert len(layer_stack.thickness) == 4
    assert len(layer_stack.material) == 4
    assert len(layer_stack.dielectric) == 4

def test_zone_settings_creation():
    """Test zone settings creation."""
    # Create zone settings
    zone = ZoneSettings(
        name="GND",
        layer="F.Cu",
        net="GND",
        priority=1,
        fill_mode="solid",
        thermal_gap=0.5,
        thermal_bridge_width=0.5,
        min_thickness=0.5,
        keep_islands=True,
        smoothing=True
    )
    
    # Check attributes
    assert zone.name == "GND"
    assert zone.layer == "F.Cu"
    assert zone.net == "GND"
    assert zone.priority == 1
    assert zone.fill_mode == "solid"
    assert zone.thermal_gap == 0.5
    assert zone.thermal_bridge_width == 0.5
    assert zone.min_thickness == 0.5
    assert zone.keep_islands is True
    assert zone.smoothing is True

def test_design_variant_creation():
    """Test design variant creation."""
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Create design variant
    variant = DesignVariant(
        name="Standard",
        description="Standard variant",
        components={"R1": component},
        nets={"GND": ["R1-1"], "VCC": ["R1-2"]},
        rules={"clearance": 0.2}
    )
    
    # Check attributes
    assert variant.name == "Standard"
    assert variant.description == "Standard variant"
    assert len(variant.components) == 1
    assert len(variant.nets) == 2
    assert len(variant.rules) == 1

def test_template_base_initialization(temp_dir):
    """Test template base initialization."""
    # Create template
    template = TemplateBase(str(temp_dir))
    
    # Check attributes
    assert template.base_path == temp_dir
    assert template.name == ""
    assert template.description == ""
    assert template.version == "1.0.0"
    assert template.layer_stack is None
    assert len(template.zones) == 0
    assert len(template.variants) == 0
    assert len(template.rules) == 0

def test_template_base_save_load(temp_dir):
    """Test template save and load."""
    # Create template
    template = TemplateBase(str(temp_dir))
    
    # Set template data
    template.name = "Test Template"
    template.description = "Test template description"
    template.version = "1.0.0"
    
    # Create layer stack
    template.layer_stack = LayerStack(
        name="4-Layer Stack",
        layers=["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"],
        thickness={
            "F.Cu": 0.035,
            "In1.Cu": 0.035,
            "In2.Cu": 0.035,
            "B.Cu": 0.035
        },
        material={
            "F.Cu": "Copper",
            "In1.Cu": "Copper",
            "In2.Cu": "Copper",
            "B.Cu": "Copper"
        },
        dielectric={
            "F.Cu": 0.1,
            "In1.Cu": 0.1,
            "In2.Cu": 0.1,
            "B.Cu": 0.1
        }
    )
    
    # Create zone
    template.zones["GND"] = ZoneSettings(
        name="GND",
        layer="F.Cu",
        net="GND",
        priority=1,
        fill_mode="solid",
        thermal_gap=0.5,
        thermal_bridge_width=0.5,
        min_thickness=0.5,
        keep_islands=True,
        smoothing=True
    )
    
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Create variant
    template.variants["Standard"] = DesignVariant(
        name="Standard",
        description="Standard variant",
        components={"R1": component},
        nets={"GND": ["R1-1"], "VCC": ["R1-2"]},
        rules={"clearance": 0.2}
    )
    
    # Set rules
    template.rules = {
        "clearance": 0.2,
        "track_width": 0.2,
        "via_diameter": 0.4,
        "via_drill": 0.2
    }
    
    # Save template
    template_path = temp_dir / "template.json"
    assert template.save_template(str(template_path))
    
    # Create new template
    new_template = TemplateBase(str(temp_dir))
    
    # Load template
    assert new_template.load_template(str(template_path))
    
    # Check attributes
    assert new_template.name == template.name
    assert new_template.description == template.description
    assert new_template.version == template.version
    
    # Check layer stack
    assert new_template.layer_stack is not None
    assert new_template.layer_stack.name == template.layer_stack.name
    assert new_template.layer_stack.layers == template.layer_stack.layers
    
    # Check zones
    assert len(new_template.zones) == len(template.zones)
    assert "GND" in new_template.zones
    assert new_template.zones["GND"].name == template.zones["GND"].name
    
    # Check variants
    assert len(new_template.variants) == len(template.variants)
    assert "Standard" in new_template.variants
    assert new_template.variants["Standard"].name == template.variants["Standard"].name
    
    # Check rules
    assert new_template.rules == template.rules

def test_template_base_validation(temp_dir):
    """Test template validation."""
    # Create template
    template = TemplateBase(str(temp_dir))
    
    # Test missing required fields
    assert not template.validate_template()
    
    # Set required fields
    template.name = "Test Template"
    template.description = "Test template description"
    template.version = "1.0.0"
    
    # Test valid template
    assert template.validate_template()
    
    # Test invalid layer stack
    template.layer_stack = LayerStack(
        name="",
        layers=[],
        thickness={},
        material={},
        dielectric={}
    )
    assert not template.validate_template()
    
    # Test invalid component
    component = ComponentData(
        id="",
        type="",
        value="",
        footprint=""
    )
    template.component_manager.add_component(component)
    assert not template.validate_template()
    
    # Test invalid net
    template.variants["Standard"] = DesignVariant(
        name="Standard",
        description="Standard variant",
        components={},
        nets={"": []},
        rules={}
    )
    assert not template.validate_template() 