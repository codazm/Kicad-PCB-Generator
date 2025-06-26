"""End-to-end tests for the format system."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint
from kicad_pcb_generator.ui.widgets.format_preview import FormatPreviewWidget
from kicad_pcb_generator.audio.pcb.formats.kosmo_validation import KosmoValidator
from kicad_pcb_generator.audio.pcb.formats import (
    KOSMO_FORMATS,
    EURORACK_FORMATS,
    GUITAR_PEDAL_FORMATS,
    DESKTOP_FORMATS
)

@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication([])

@pytest.fixture
def preview_widget(app):
    """Create format preview widget instance."""
    return FormatPreviewWidget()

@pytest.fixture
def kosmo_validator():
    """Create Kosmo validator instance."""
    return KosmoValidator("standard")

def test_format_selection_and_validation(preview_widget, kosmo_validator):
    """Test format selection and validation workflow."""
    # Select Kosmo standard format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Get format information
    format_info = preview_widget.current_format
    assert format_info == KOSMO_FORMATS["standard"]
    
    # Validate component placement
    errors = kosmo_validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Check that component is in valid zone
    zones = kosmo_validator.get_recommended_zones()
    assert "control_knob" in zones

def test_format_preview_and_validation_integration(preview_widget, kosmo_validator):
    """Test integration between preview and validation systems."""
    # Select format and get preview
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Get format dimensions from preview
    width, height = preview_widget.current_format.board_size
    
    # Validate component placement using preview dimensions
    errors = kosmo_validator.validate_component_placement(
        component_type="power",
        position=(10.0, height - 10.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Toggle zones and verify validation still works
    preview_widget.show_zones_btn.click()
    assert not preview_widget.show_zones
    
    errors = kosmo_validator.validate_component_placement(
        component_type="power",
        position=(10.0, height - 10.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors

def test_format_switching_and_validation(preview_widget):
    """Test format switching and validation workflow."""
    # Test Kosmo format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    kosmo_validator = KosmoValidator("standard")
    
    # Validate Kosmo component
    errors = kosmo_validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Switch to Eurorack format
    preview_widget.format_type_combo.setCurrentText("Eurorack")
    preview_widget.format_combo.setCurrentText("4hp")
    
    # Verify format changed
    assert preview_widget.current_format == EURORACK_FORMATS["4hp"]
    
    # Validate Eurorack component (should fail as it's not in Kosmo format)
    errors = kosmo_validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert errors  # Should have errors as component is outside Kosmo zones

def test_component_placement_workflow(preview_widget, kosmo_validator):
    """Test complete component placement workflow."""
    # Select format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Get recommended zones
    zones = kosmo_validator.get_recommended_zones()
    
    # Place power connector
    power_zone = zones["power_connector"]
    power_x = (power_zone[0] + power_zone[2]) / 2
    power_y = (power_zone[1] + power_zone[3]) / 2
    
    errors = kosmo_validator.validate_component_placement(
        component_type="power",
        position=(power_x, power_y),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Place control knob
    knob_zone = zones["control_knob"]
    knob_x = (knob_zone[0] + knob_zone[2]) / 2
    knob_y = (knob_zone[1] + knob_zone[3]) / 2
    
    errors = kosmo_validator.validate_component_placement(
        component_type="knob",
        position=(knob_x, knob_y),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Place jack
    jack_zone = zones["jack"]
    jack_x = (jack_zone[0] + jack_zone[2]) / 2
    jack_y = (jack_zone[1] + jack_zone[3]) / 2
    
    errors = kosmo_validator.validate_component_placement(
        component_type="jack",
        position=(jack_x, jack_y),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors
    
    # Verify all components are in valid positions
    assert preview_widget.show_zones  # Zones should be visible
    items = preview_widget.scene.items()
    zone_items = [item for item in items if isinstance(item, QGraphicsRectItem) and item != items[0]]
    assert len(zone_items) == 3  # Should have 3 zone rectangles

def test_error_handling_and_recovery(preview_widget, kosmo_validator):
    """Test error handling and recovery in the format system."""
    # Select format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Try invalid component placement
    errors = kosmo_validator.validate_component_placement(
        component_type="knob",
        position=(2.0, 2.0),  # Too close to edge
        size=(10.0, 10.0),
        height=35.0  # Too tall
    )
    assert len(errors) > 0
    
    # Verify preview still works
    assert preview_widget.current_format == KOSMO_FORMATS["standard"]
    items = preview_widget.scene.items()
    assert len(items) > 0
    
    # Try invalid format type
    preview_widget.format_type_combo.setCurrentText("Invalid")
    assert preview_widget.current_type == "Invalid"
    assert preview_widget.format_combo.count() == 0
    
    # Recover by selecting valid format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    assert preview_widget.current_type == "Kosmo"
    assert preview_widget.format_combo.count() > 0 