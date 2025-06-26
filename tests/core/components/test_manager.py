"""Tests for component management system."""
import json
import pytest
from datetime import datetime
from pathlib import Path

from kicad_pcb_generator.core.components.manager import ComponentManager, ComponentData

def test_component_data_creation():
    """Test component data creation."""
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Check attributes
    assert component.id == "R1"
    assert component.type == "resistor"
    assert component.value == "10k"
    assert component.footprint == "R_0805_2012Metric"
    assert component.position is None
    assert component.orientation is None
    assert component.layer is None
    assert component.metadata == {}
    assert isinstance(component.created_at, datetime)
    assert isinstance(component.updated_at, datetime)

def test_component_data_serialization():
    """Test component data serialization."""
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        position=(10.0, 20.0),
        orientation=90.0,
        layer="F.Cu",
        metadata={"tolerance": "1%"}
    )
    
    # Convert to dict
    data = component.to_dict()
    
    # Check data
    assert data["id"] == "R1"
    assert data["type"] == "resistor"
    assert data["value"] == "10k"
    assert data["footprint"] == "R_0805_2012Metric"
    assert data["position"] == (10.0, 20.0)
    assert data["orientation"] == 90.0
    assert data["layer"] == "F.Cu"
    assert data["metadata"] == {"tolerance": "1%"}
    assert "created_at" in data
    assert "updated_at" in data
    
    # Create from dict
    new_component = ComponentData.from_dict(data)
    
    # Check component
    assert new_component.id == component.id
    assert new_component.type == component.type
    assert new_component.value == component.value
    assert new_component.footprint == component.footprint
    assert new_component.position == component.position
    assert new_component.orientation == component.orientation
    assert new_component.layer == component.layer
    assert new_component.metadata == component.metadata

def test_component_manager_initialization(temp_dir):
    """Test component manager initialization."""
    # Create manager
    manager = ComponentManager(str(temp_dir))
    
    # Check attributes
    assert manager.base_path == temp_dir
    assert isinstance(manager.components, dict)
    assert len(manager.components) == 0

def test_component_manager_add_component(temp_dir):
    """Test adding components."""
    # Create manager
    manager = ComponentManager(str(temp_dir))
    
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Add component
    assert manager.add_component(component)
    
    # Check component
    assert "R1" in manager.components
    assert manager.components["R1"].id == "R1"
    assert manager.components["R1"].type == "resistor"
    assert manager.components["R1"].value == "10k"
    assert manager.components["R1"].footprint == "R_0805_2012Metric"
    
    # Check file
    components_file = temp_dir / "components.json"
    assert components_file.exists()
    
    with open(components_file, "r") as f:
        data = json.load(f)
        assert "R1" in data
        assert data["R1"]["id"] == "R1"
        assert data["R1"]["type"] == "resistor"
        assert data["R1"]["value"] == "10k"
        assert data["R1"]["footprint"] == "R_0805_2012Metric"

def test_component_manager_update_component(temp_dir):
    """Test updating components."""
    # Create manager
    manager = ComponentManager(str(temp_dir))
    
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Add component
    assert manager.add_component(component)
    
    # Update component
    assert manager.update_component("R1", value="20k", position=(10.0, 20.0))
    
    # Check component
    assert manager.components["R1"].value == "20k"
    assert manager.components["R1"].position == (10.0, 20.0)
    
    # Check file
    components_file = temp_dir / "components.json"
    with open(components_file, "r") as f:
        data = json.load(f)
        assert data["R1"]["value"] == "20k"
        assert data["R1"]["position"] == [10.0, 20.0]

def test_component_manager_remove_component(temp_dir):
    """Test removing components."""
    # Create manager
    manager = ComponentManager(str(temp_dir))
    
    # Create component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric"
    )
    
    # Add component
    assert manager.add_component(component)
    
    # Remove component
    assert manager.remove_component("R1")
    
    # Check component
    assert "R1" not in manager.components
    
    # Check file
    components_file = temp_dir / "components.json"
    with open(components_file, "r") as f:
        data = json.load(f)
        assert "R1" not in data

def test_component_manager_validation(temp_dir):
    """Test component validation."""
    # Create manager
    manager = ComponentManager(str(temp_dir))
    
    # Test missing required fields
    component = ComponentData(
        id="",
        type="",
        value="",
        footprint=""
    )
    assert not manager.add_component(component)
    
    # Test invalid position
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        position=(10.0,)  # Invalid position
    )
    assert not manager.add_component(component)
    
    # Test invalid orientation
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        orientation="90"  # Invalid orientation
    )
    assert not manager.add_component(component)
    
    # Test invalid layer
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        layer="Invalid"  # Invalid layer
    )
    assert not manager.add_component(component)
    
    # Test valid component
    component = ComponentData(
        id="R1",
        type="resistor",
        value="10k",
        footprint="R_0805_2012Metric",
        position=(10.0, 20.0),
        orientation=90.0,
        layer="F.Cu"
    )
    assert manager.add_component(component) 
