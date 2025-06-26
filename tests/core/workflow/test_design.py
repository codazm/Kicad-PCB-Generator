"""Tests for design workflow system."""
import pytest
from pathlib import Path

from kicad_pcb_generator.core.workflow.design import DesignWorkflow
from kicad_pcb_generator.audio.circuits import PreamplifierTemplate

@pytest.fixture
def design_dir(tmp_path):
    """Create a temporary directory for design data."""
    return tmp_path / "design"

@pytest.fixture
def template_dir(tmp_path):
    """Create a temporary directory for template data."""
    return tmp_path / "templates"

@pytest.fixture
def preamp_template(template_dir):
    """Create a preamplifier template."""
    return PreamplifierTemplate(str(template_dir))

@pytest.fixture
def design_workflow(design_dir, preamp_template):
    """Create a design workflow with a preamplifier template."""
    workflow = DesignWorkflow(str(design_dir))
    workflow.set_template(preamp_template)
    return workflow

def test_design_workflow_initialization(design_dir):
    """Test design workflow initialization."""
    workflow = DesignWorkflow(str(design_dir))
    assert workflow.base_path == design_dir
    assert workflow.design_dir == design_dir / "design"
    assert workflow.state["status"] == "initialized"
    assert workflow.template is None

def test_set_template(design_workflow, preamp_template):
    """Test setting template."""
    assert design_workflow.template == preamp_template
    assert design_workflow.state["template"] == preamp_template.name
    assert design_workflow.state["rules"] == preamp_template.rules

def test_add_component(design_workflow):
    """Test adding a component."""
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    assert "R2" in design_workflow.state["components"]
    assert design_workflow.state["components"]["R2"] == component_data

def test_remove_component(design_workflow):
    """Test removing a component."""
    # Add a component first
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    
    # Remove the component
    design_workflow.remove_component("R2")
    assert "R2" not in design_workflow.state["components"]

def test_update_component(design_workflow):
    """Test updating a component."""
    # Add a component first
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    
    # Update the component
    updated_data = {
        "id": "R2",
        "type": "resistor",
        "value": "2k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.update_component("R2", updated_data)
    assert design_workflow.state["components"]["R2"] == updated_data

def test_add_net(design_workflow):
    """Test adding a net."""
    net_data = {
        "name": "VCC",
        "pins": ["U1-8", "R1-1"]
    }
    design_workflow.add_net(net_data)
    assert "VCC" in design_workflow.state["nets"]
    assert design_workflow.state["nets"]["VCC"] == net_data

def test_remove_net(design_workflow):
    """Test removing a net."""
    # Add a net first
    net_data = {
        "name": "VCC",
        "pins": ["U1-8", "R1-1"]
    }
    design_workflow.add_net(net_data)
    
    # Remove the net
    design_workflow.remove_net("VCC")
    assert "VCC" not in design_workflow.state["nets"]

def test_add_track(design_workflow):
    """Test adding a track."""
    track_data = {
        "net": "VCC",
        "layer": "F.Cu",
        "width": 0.3,
        "points": [(0, 0), (10, 0)]
    }
    design_workflow.add_track(track_data)
    assert "track_0" in design_workflow.state["tracks"]
    assert design_workflow.state["tracks"]["track_0"] == track_data

def test_remove_track(design_workflow):
    """Test removing a track."""
    # Add a track first
    track_data = {
        "net": "VCC",
        "layer": "F.Cu",
        "width": 0.3,
        "points": [(0, 0), (10, 0)]
    }
    design_workflow.add_track(track_data)
    
    # Remove the track
    design_workflow.remove_track("track_0")
    assert "track_0" not in design_workflow.state["tracks"]

def test_add_zone(design_workflow):
    """Test adding a zone."""
    zone_data = {
        "net": "GND",
        "layer": "F.Cu",
        "priority": 1,
        "fill_mode": "solid",
        "outline": [(0, 0), (0, 10), (10, 10), (10, 0)]
    }
    design_workflow.add_zone(zone_data)
    assert "zone_0" in design_workflow.state["zones"]
    assert design_workflow.state["zones"]["zone_0"] == zone_data

def test_remove_zone(design_workflow):
    """Test removing a zone."""
    # Add a zone first
    zone_data = {
        "net": "GND",
        "layer": "F.Cu",
        "priority": 1,
        "fill_mode": "solid",
        "outline": [(0, 0), (0, 10), (10, 10), (10, 0)]
    }
    design_workflow.add_zone(zone_data)
    
    # Remove the zone
    design_workflow.remove_zone("zone_0")
    assert "zone_0" not in design_workflow.state["zones"]

def test_validate_design(design_workflow):
    """Test design validation."""
    # Add required components and nets
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    
    net_data = {
        "name": "VCC",
        "pins": ["U1-8", "R1-1"]
    }
    design_workflow.add_net(net_data)
    
    # Validate design
    errors = design_workflow.validate_design()
    assert isinstance(errors, list)

def test_export_design(design_workflow, tmp_path):
    """Test exporting design."""
    # Add some data
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    
    # Export design
    output_path = str(tmp_path / "export")
    design_workflow.export_design(output_path)
    
    # Check exported files
    assert (Path(output_path) / "design_state.json").exists()
    assert (Path(output_path) / "components").exists()

def test_load_design(design_workflow, tmp_path):
    """Test loading design."""
    # Add some data
    component_data = {
        "id": "R2",
        "type": "resistor",
        "value": "1k",
        "footprint": "R_0805_2012Metric",
        "metadata": {"tolerance": "1%", "power": "0.25W"}
    }
    design_workflow.add_component(component_data)
    
    # Export design
    output_path = str(tmp_path / "export")
    design_workflow.export_design(output_path)
    
    # Create new workflow and load design
    new_workflow = DesignWorkflow(str(tmp_path / "new_design"))
    new_workflow.load_design(output_path)
    
    # Check loaded data
    assert "R2" in new_workflow.state["components"]
    assert new_workflow.state["components"]["R2"] == component_data

def test_design_status(design_workflow):
    """Test design status management."""
    # Check initial status
    assert design_workflow.get_design_status() == "initialized"
    
    # Update status
    design_workflow.update_design_status("in_progress")
    assert design_workflow.get_design_status() == "in_progress" 
