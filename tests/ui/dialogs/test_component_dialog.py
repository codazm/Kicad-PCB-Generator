"""Unit tests for component dialog."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from kicad_pcb_generator.ui.dialogs.component_dialog import ComponentDialog
from kicad_pcb_generator.audio.simulation.circuit_file_handler import CircuitComponent

@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication([])

@pytest.fixture
def sample_component():
    """Create a sample component."""
    return CircuitComponent(
        name="R1",
        type="Resistor",
        value="1k",
        parameters={
            "tolerance": "1%",
            "power": "0.25W"
        },
        position={"x": 0, "y": 0},
        connections=["VCC", "GND"]
    )

def test_new_component_dialog(app):
    """Test creating a new component dialog."""
    dialog = ComponentDialog()
    assert dialog.windowTitle() == "Component Properties"
    assert dialog.name_edit.text() == ""
    assert dialog.type_combo.currentText() == "Resistor"
    assert dialog.value_edit.text() == ""
    assert dialog.x_pos_spin.value() == 0
    assert dialog.y_pos_spin.value() == 0
    assert len(dialog.param_edits) == 0
    assert dialog.conn_edit.text() == ""

def test_edit_component_dialog(app, sample_component):
    """Test editing an existing component."""
    dialog = ComponentDialog(component=sample_component)
    assert dialog.name_edit.text() == "R1"
    assert dialog.type_combo.currentText() == "Resistor"
    assert dialog.value_edit.text() == "1k"
    assert dialog.x_pos_spin.value() == 0
    assert dialog.y_pos_spin.value() == 0
    assert len(dialog.param_edits) == 2
    assert "tolerance" in dialog.param_edits
    assert "power" in dialog.param_edits
    assert dialog.conn_edit.text() == "VCC, GND"

def test_add_parameter_field(app):
    """Test adding parameter fields."""
    dialog = ComponentDialog()
    
    # Add numeric parameter
    dialog.add_parameter_field(dialog.layout(), "resistance", 1000)
    assert "resistance" in dialog.param_edits
    assert isinstance(dialog.param_edits["resistance"], QDoubleSpinBox)
    assert dialog.param_edits["resistance"].value() == 1000
    
    # Add string parameter
    dialog.add_parameter_field(dialog.layout(), "package", "0805")
    assert "package" in dialog.param_edits
    assert isinstance(dialog.param_edits["package"], QLineEdit)
    assert dialog.param_edits["package"].text() == "0805"

def test_get_component(app):
    """Test getting component data from dialog."""
    dialog = ComponentDialog()
    
    # Set component data
    dialog.name_edit.setText("R1")
    dialog.type_combo.setCurrentText("Resistor")
    dialog.value_edit.setText("1k")
    dialog.x_pos_spin.setValue(100)
    dialog.y_pos_spin.setValue(200)
    
    # Add parameters
    dialog.add_parameter_field(dialog.layout(), "tolerance", "1%")
    dialog.add_parameter_field(dialog.layout(), "power", "0.25W")
    
    # Set connections
    dialog.conn_edit.setText("VCC, GND")
    
    # Get component
    component = dialog.get_component()
    
    # Check component data
    assert component.name == "R1"
    assert component.type == "Resistor"
    assert component.value == "1k"
    assert component.position == {"x": 100, "y": 200}
    assert component.parameters == {
        "tolerance": "1%",
        "power": "0.25W"
    }
    assert component.connections == ["VCC", "GND"]

def test_validation(app):
    """Test input validation."""
    dialog = ComponentDialog()
    
    # Try to accept with empty name
    dialog.name_edit.setText("")
    dialog.value_edit.setText("1k")
    dialog.accept()
    assert dialog.isVisible()  # Dialog should still be visible
    
    # Try to accept with empty value
    dialog.name_edit.setText("R1")
    dialog.value_edit.setText("")
    dialog.accept()
    assert dialog.isVisible()  # Dialog should still be visible
    
    # Try to accept with valid data
    dialog.name_edit.setText("R1")
    dialog.value_edit.setText("1k")
    dialog.accept()
    assert not dialog.isVisible()  # Dialog should be closed

def test_component_updated_signal(app):
    """Test component_updated signal."""
    dialog = ComponentDialog()
    
    # Set up signal handler
    received_component = None
    def on_component_updated(component):
        nonlocal received_component
        received_component = component
    
    dialog.component_updated.connect(on_component_updated)
    
    # Set component data
    dialog.name_edit.setText("R1")
    dialog.type_combo.setCurrentText("Resistor")
    dialog.value_edit.setText("1k")
    
    # Accept dialog
    dialog.accept()
    
    # Check signal
    assert received_component is not None
    assert received_component.name == "R1"
    assert received_component.type == "Resistor"
    assert received_component.value == "1k"

def test_cancel_dialog(app):
    """Test canceling the dialog."""
    dialog = ComponentDialog()
    
    # Set component data
    dialog.name_edit.setText("R1")
    dialog.type_combo.setCurrentText("Resistor")
    dialog.value_edit.setText("1k")
    
    # Set up signal handler
    signal_received = False
    def on_component_updated(component):
        nonlocal signal_received
        signal_received = True
    
    dialog.component_updated.connect(on_component_updated)
    
    # Reject dialog
    dialog.reject()
    
    # Check signal was not emitted
    assert not signal_received 