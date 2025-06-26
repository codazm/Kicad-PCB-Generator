"""Tests for stability and filtering components."""
import pytest
from kicad_pcb_generator.audio.components.stability import (
    StabilityManager,
    StabilityComponent,
    FilterType,
    FilterSpec
)

@pytest.fixture
def stability_manager():
    """Create a stability manager instance."""
    return StabilityManager()

def test_add_ferrite_bead(stability_manager):
    """Test adding a ferrite bead."""
    component = stability_manager.add_ferrite_bead("FB1", 100, 1.0)
    
    assert component.reference == "FB1"
    assert component.type == "ferrite"
    assert component.value == "100Ω @ 100MHz"
    assert component.properties["impedance"] == 100
    assert component.properties["current_rating"] == 1.0
    assert component.properties["dc_resistance"] == 0.1
    assert component.properties["frequency_range"] == "1MHz-1GHz"

def test_add_emc_filter(stability_manager):
    """Test adding an EMC filter."""
    filter_spec = FilterSpec(
        type=FilterType.EMI,
        cutoff_freq=1e6,  # 1MHz
        order=2,
        attenuation=-40
    )
    component = stability_manager.add_emc_filter("EMC1", filter_spec)
    
    assert component.reference == "EMC1"
    assert component.type == "emc_filter"
    assert component.value == "EMC Filter emi"
    assert component.filter_spec == filter_spec
    assert component.properties["insertion_loss"] == -40
    assert component.properties["voltage_rating"] == 250
    assert component.properties["current_rating"] == 1.0

def test_add_power_filter(stability_manager):
    """Test adding a power filter capacitor."""
    component = stability_manager.add_power_filter("C1", 10.0, 16.0)
    
    assert component.reference == "C1"
    assert component.type == "capacitor"
    assert component.value == "10.0µF"
    assert component.filter_spec.type == FilterType.LOW_PASS
    assert component.filter_spec.cutoff_freq == 1e3
    assert component.properties["capacitance"] == 10.0
    assert component.properties["voltage_rating"] == 16.0
    assert component.properties["esr"] == 0.01
    assert component.properties["temperature_coefficient"] == "X7R"

def test_add_audio_filter(stability_manager):
    """Test adding an audio filter."""
    filter_spec = FilterSpec(
        type=FilterType.LOW_PASS,
        cutoff_freq=20e3,  # 20kHz
        order=2,
        ripple=0.1
    )
    component = stability_manager.add_audio_filter("AF1", filter_spec)
    
    assert component.reference == "AF1"
    assert component.type == "audio_filter"
    assert component.value == "Audio Filter low_pass"
    assert component.filter_spec == filter_spec
    assert component.properties["insertion_loss"] == -0.1
    assert component.properties["impedance"] == 600
    assert component.properties["distortion"] == 0.001

def test_get_components(stability_manager):
    """Test getting all components."""
    # Add some components
    stability_manager.add_ferrite_bead("FB1", 100, 1.0)
    stability_manager.add_power_filter("C1", 10.0, 16.0)
    
    components = stability_manager.get_components()
    assert len(components) == 2
    assert all(isinstance(c, StabilityComponent) for c in components)

def test_get_component_by_reference(stability_manager):
    """Test getting a component by reference."""
    # Add a component
    stability_manager.add_ferrite_bead("FB1", 100, 1.0)
    
    # Test existing component
    component = stability_manager.get_component_by_reference("FB1")
    assert component is not None
    assert component.reference == "FB1"
    
    # Test non-existent component
    component = stability_manager.get_component_by_reference("NONEXISTENT")
    assert component is None

def test_get_components_by_type(stability_manager):
    """Test getting components by type."""
    # Add components of different types
    stability_manager.add_ferrite_bead("FB1", 100, 1.0)
    stability_manager.add_power_filter("C1", 10.0, 16.0)
    stability_manager.add_ferrite_bead("FB2", 200, 2.0)
    
    # Test getting ferrite beads
    ferrites = stability_manager.get_components_by_type("ferrite")
    assert len(ferrites) == 2
    assert all(c.type == "ferrite" for c in ferrites)
    
    # Test getting capacitors
    caps = stability_manager.get_components_by_type("capacitor")
    assert len(caps) == 1
    assert all(c.type == "capacitor" for c in caps)

def test_get_components_by_filter_type(stability_manager):
    """Test getting components by filter type."""
    # Add components with different filter types
    stability_manager.add_power_filter("C1", 10.0, 16.0)  # LOW_PASS
    filter_spec = FilterSpec(
        type=FilterType.EMI,
        cutoff_freq=1e6,
        order=2
    )
    stability_manager.add_emc_filter("EMC1", filter_spec)
    
    # Test getting low-pass filters
    low_pass = stability_manager.get_components_by_filter_type(FilterType.LOW_PASS)
    assert len(low_pass) == 1
    assert all(c.filter_spec.type == FilterType.LOW_PASS for c in low_pass)
    
    # Test getting EMI filters
    emi = stability_manager.get_components_by_filter_type(FilterType.EMI)
    assert len(emi) == 1
    assert all(c.filter_spec.type == FilterType.EMI for c in emi) 
