"""Unit tests for circuit file handler."""

import pytest
from pathlib import Path
import json
import tempfile
import shutil

from kicad_pcb_generator.audio.simulation.circuit_file_handler import (
    CircuitFileHandler, CircuitData, CircuitComponent
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def file_handler():
    """Create a circuit file handler."""
    return CircuitFileHandler()

@pytest.fixture
def sample_circuit():
    """Create a sample circuit."""
    return CircuitData(
        name="Test Circuit",
        description="A test circuit",
        components=[
            CircuitComponent(
                name="R1",
                type="Resistor",
                value="1k",
                parameters={"tolerance": "1%"},
                position={"x": 0, "y": 0},
                connections=["VCC", "GND"]
            ),
            CircuitComponent(
                name="C1",
                type="Capacitor",
                value="100n",
                parameters={"voltage": "16V"},
                position={"x": 100, "y": 0},
                connections=["VCC", "GND"]
            )
        ],
        nets=["VCC", "GND"],
        parameters={"voltage": "5V"}
    )

def test_create_new_circuit(file_handler):
    """Test creating a new circuit."""
    circuit = file_handler.create_new_circuit("Test Circuit")
    
    assert circuit.name == "Test Circuit"
    assert circuit.description == ""
    assert len(circuit.components) == 0
    assert len(circuit.nets) == 0
    assert len(circuit.parameters) == 0

def test_save_and_load_circuit(file_handler, temp_dir, sample_circuit):
    """Test saving and loading a circuit."""
    # Save circuit
    file_path = temp_dir / "test.circuit"
    assert file_handler.save_circuit(sample_circuit, file_path)
    
    # Load circuit
    loaded_circuit = file_handler.load_circuit(file_path)
    assert loaded_circuit is not None
    
    # Check circuit data
    assert loaded_circuit.name == sample_circuit.name
    assert loaded_circuit.description == sample_circuit.description
    assert len(loaded_circuit.components) == len(sample_circuit.components)
    assert len(loaded_circuit.nets) == len(sample_circuit.nets)
    assert loaded_circuit.parameters == sample_circuit.parameters
    
    # Check components
    for i, component in enumerate(loaded_circuit.components):
        original = sample_circuit.components[i]
        assert component.name == original.name
        assert component.type == original.type
        assert component.value == original.value
        assert component.parameters == original.parameters
        assert component.position == original.position
        assert component.connections == original.connections

def test_add_component(file_handler, sample_circuit):
    """Test adding a component."""
    # Create new component
    component = CircuitComponent(
        name="L1",
        type="Inductor",
        value="10mH",
        parameters={"current": "1A"},
        position={"x": 200, "y": 0},
        connections=["VCC", "GND"]
    )
    
    # Add component
    assert file_handler.add_component(sample_circuit, component)
    assert len(sample_circuit.components) == 3
    
    # Try adding duplicate
    assert not file_handler.add_component(sample_circuit, component)

def test_remove_component(file_handler, sample_circuit):
    """Test removing a component."""
    # Remove component
    assert file_handler.remove_component(sample_circuit, "R1")
    assert len(sample_circuit.components) == 1
    
    # Try removing non-existent component
    assert not file_handler.remove_component(sample_circuit, "R1")

def test_update_component(file_handler, sample_circuit):
    """Test updating a component."""
    # Create updated component
    updated = CircuitComponent(
        name="R1",
        type="Resistor",
        value="2k",
        parameters={"tolerance": "5%"},
        position={"x": 50, "y": 50},
        connections=["VCC", "OUT"]
    )
    
    # Update component
    assert file_handler.update_component(sample_circuit, updated)
    
    # Check update
    component = file_handler.get_component(sample_circuit, "R1")
    assert component is not None
    assert component.value == "2k"
    assert component.parameters["tolerance"] == "5%"
    assert component.position == {"x": 50, "y": 50}
    assert component.connections == ["VCC", "OUT"]
    
    # Try updating non-existent component
    assert not file_handler.update_component(
        sample_circuit,
        CircuitComponent(
            name="R2",
            type="Resistor",
            value="1k",
            parameters={},
            position={"x": 0, "y": 0},
            connections=[]
        )
    )

def test_get_component(file_handler, sample_circuit):
    """Test getting a component."""
    # Get existing component
    component = file_handler.get_component(sample_circuit, "R1")
    assert component is not None
    assert component.name == "R1"
    
    # Get non-existent component
    assert file_handler.get_component(sample_circuit, "R2") is None

def test_list_components(file_handler, sample_circuit):
    """Test listing components."""
    components = file_handler.list_components(sample_circuit)
    assert len(components) == 2
    assert all(isinstance(comp, CircuitComponent) for comp in components)

def test_validate_circuit(file_handler):
    """Test circuit validation."""
    # Create invalid circuit
    invalid_circuit = CircuitData(
        name="",
        description="",
        components=[
            CircuitComponent(
                name="",
                type="",
                value=None,
                parameters={},
                position={"x": 0, "y": 0},
                connections=[]
            ),
            CircuitComponent(
                name="R1",
                type="Resistor",
                value="1k",
                parameters={},
                position={"x": 0, "y": 0},
                connections=[]
            ),
            CircuitComponent(
                name="R1",  # Duplicate name
                type="Resistor",
                value="2k",
                parameters={},
                position={"x": 0, "y": 0},
                connections=[]
            )
        ],
        nets=[],
        parameters={}
    )
    
    # Validate circuit
    errors = file_handler.validate_circuit(invalid_circuit)
    assert len(errors) > 0
    assert "Circuit name is required" in errors
    assert "Component name is required" in errors
    assert "Component type is required" in errors
    assert "Component value is required" in errors
    assert "Duplicate component names found" in errors

def test_file_operations_error_handling(file_handler, temp_dir):
    """Test error handling in file operations."""
    # Try loading non-existent file
    assert file_handler.load_circuit(temp_dir / "nonexistent.circuit") is None
    
    # Try saving to invalid path
    assert not file_handler.save_circuit(
        CircuitData("Test", "", [], [], {}),
        Path("/invalid/path/test.circuit")
    ) 
