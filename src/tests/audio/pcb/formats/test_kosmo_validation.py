"""Unit tests for Kosmo format validation."""

import pytest
from kicad_pcb_generator.audio.pcb.formats.kosmo_validation import (
    KosmoValidator,
    ComponentPlacementRule
)
from kicad_pcb_generator.audio.pcb.formats.kosmo import KOSMO_FORMATS

@pytest.fixture
def validator():
    """Create a validator instance for testing."""
    return KosmoValidator("standard")

def test_validator_initialization():
    """Test validator initialization with different formats."""
    for format_name in KOSMO_FORMATS.keys():
        validator = KosmoValidator(format_name)
        assert validator.format == KOSMO_FORMATS[format_name]
        assert isinstance(validator.rules, ComponentPlacementRule)

def test_component_placement_validation(validator):
    """Test component placement validation."""
    # Test valid placement
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors

    # Test edge clearance
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(2.0, 30.0),  # Too close to left edge
        size=(10.0, 10.0),
        height=20.0
    )
    assert any("left edge" in error for error in errors)

    # Test component height
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=35.0  # Exceeds max height
    )
    assert any("height exceeds maximum" in error for error in errors)

def test_component_zone_validation(validator):
    """Test component zone validation."""
    # Test power connector placement
    errors = validator.validate_component_placement(
        component_type="power",
        position=(10.0, 85.0),  # In power zone
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors

    errors = validator.validate_component_placement(
        component_type="power",
        position=(30.0, 30.0),  # Outside power zone
        size=(10.0, 10.0),
        height=20.0
    )
    assert any("power connector zone" in error for error in errors)

    # Test knob placement
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(30.0, 30.0),  # In knob zone
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors

    errors = validator.validate_component_placement(
        component_type="knob",
        position=(10.0, 85.0),  # Outside knob zone
        size=(10.0, 10.0),
        height=20.0
    )
    assert any("control knob zone" in error for error in errors)

def test_zone_boundary_validation(validator):
    """Test component placement at zone boundaries."""
    width, height = validator.format.board_size
    
    # Test component exactly at zone boundaries
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(25.0, 5.0),  # At zone boundary
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors

    # Test component partially overlapping zone
    errors = validator.validate_component_placement(
        component_type="knob",
        position=(20.0, 5.0),  # Partially outside zone
        size=(10.0, 10.0),
        height=20.0
    )
    assert any("control knob zone" in error for error in errors)

def test_get_recommended_zones(validator):
    """Test getting recommended component zones."""
    zones = validator.get_recommended_zones()
    assert "power_connector" in zones
    assert "control_knob" in zones
    assert "jack" in zones
    
    # Verify zone dimensions
    power_zone = zones["power_connector"]
    assert power_zone[0] == 5.0  # x1
    assert power_zone[1] == validator.format.board_size[1] - 15.0  # y1
    assert power_zone[2] == 20.0  # x2
    assert power_zone[3] == validator.format.board_size[1] - 5.0  # y2

def test_invalid_component_type(validator):
    """Test validation with invalid component type."""
    errors = validator.validate_component_placement(
        component_type="invalid_type",
        position=(30.0, 30.0),
        size=(10.0, 10.0),
        height=20.0
    )
    assert not errors  # Should not raise errors for unknown types 
