"""
Tests for the Falstad schematic importer.
"""

import json
import os
import pytest
from pathlib import Path
from typing import Dict, Any

from kicad_pcb_generator.core.falstad_importer import FalstadImporter, FalstadImportError
from kicad_pcb_generator.core.validation.falstad_validator import ValidationError

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path

@pytest.fixture
def valid_falstad_data() -> Dict[str, Any]:
    """Create a valid Falstad schematic data structure."""
    return {
        "elements": [
            {
                "type": "resistor",
                "x": 1.0,
                "y": 1.0,
                "rotation": 0.0,
                "value": "1k",
                "properties": {}
            },
            {
                "type": "capacitor",
                "x": 2.0,
                "y": 2.0,
                "rotation": 1.57,
                "value": "100n",
                "properties": {"voltage": "16V"}
            },
            {
                "type": "ground",
                "x": 0.0,
                "y": 0.0,
                "rotation": 0.0,
                "value": "",
                "properties": {}
            },
            {
                "type": "ic",
                "x": 3.0,
                "y": 3.0,
                "rotation": 0.0,
                "value": "opamp",
                "properties": {"pins": 8}
            }
        ],
        "wires": [
            {
                "x1": 1.0,
                "y1": 1.0,
                "x2": 2.0,
                "y2": 2.0
            },
            {
                "x1": 0.0,
                "y1": 0.0,
                "x2": 1.0,
                "y2": 1.0
            }
        ]
    }

@pytest.fixture
def valid_falstad_file(temp_dir, valid_falstad_data) -> str:
    """Create a valid Falstad schematic file."""
    file_path = temp_dir / "test_schematic.json"
    with open(file_path, 'w') as f:
        json.dump(valid_falstad_data, f)
    return str(file_path)

def test_import_valid_schematic(valid_falstad_file, temp_dir):
    """Test importing a valid Falstad schematic."""
    importer = FalstadImporter()
    output_path = importer.import_schematic(valid_falstad_file, str(temp_dir))
    
    assert os.path.exists(output_path)
    assert output_path.endswith(".kicad_sch")

def test_import_invalid_json(temp_dir):
    """Test importing an invalid JSON file."""
    invalid_file = temp_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("invalid json")
    
    importer = FalstadImporter()
    with pytest.raises(FalstadImportError):
        importer.import_schematic(str(invalid_file), str(temp_dir))

def test_import_missing_required_fields(temp_dir):
    """Test importing a schematic with missing required fields."""
    invalid_data = {
        "elements": []  # Missing "wires" field
    }
    
    invalid_file = temp_dir / "invalid_schematic.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    with pytest.raises(FalstadImportError):
        importer.import_schematic(str(invalid_file), str(temp_dir))

def test_import_invalid_component_coordinates(temp_dir):
    """Test importing a schematic with invalid component coordinates."""
    invalid_data = {
        "elements": [
            {
                "type": "resistor",
                "x": 1000.0,  # Too large
                "y": 1000.0,
                "rotation": 0.0,
                "value": "1k",
                "properties": {}
            }
        ],
        "wires": []
    }
    
    invalid_file = temp_dir / "invalid_coords.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    with pytest.raises(FalstadImportError):
        importer.import_schematic(str(invalid_file), str(temp_dir))

def test_import_invalid_wire_coordinates(temp_dir):
    """Test importing a schematic with invalid wire coordinates."""
    invalid_data = {
        "elements": [],
        "wires": [
            {
                "x1": 1000.0,  # Too large
                "y1": 1000.0,
                "x2": 2000.0,
                "y2": 2000.0
            }
        ]
    }
    
    invalid_file = temp_dir / "invalid_wires.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    with pytest.raises(FalstadImportError):
        importer.import_schematic(str(invalid_file), str(temp_dir))

def test_import_unsupported_component(temp_dir):
    """Test importing a schematic with an unsupported component type."""
    invalid_data = {
        "elements": [
            {
                "type": "unsupported",
                "x": 1.0,
                "y": 1.0,
                "rotation": 0.0,
                "value": "",
                "properties": {}
            }
        ],
        "wires": []
    }
    
    invalid_file = temp_dir / "unsupported_component.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    # Should not raise an error in non-strict mode
    output_path = importer.import_schematic(str(invalid_file), str(temp_dir), strict=False)
    assert os.path.exists(output_path)

def test_import_missing_required_property(temp_dir):
    """Test importing a schematic with missing required component properties."""
    invalid_data = {
        "elements": [
            {
                "type": "resistor",
                "x": 1.0,
                "y": 1.0,
                "rotation": 0.0,
                # Missing "value" property
                "properties": {}
            }
        ],
        "wires": []
    }
    
    invalid_file = temp_dir / "missing_property.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    with pytest.raises(FalstadImportError):
        importer.import_schematic(str(invalid_file), str(temp_dir))

def test_import_zero_length_wire(temp_dir):
    """Test importing a schematic with a zero-length wire."""
    invalid_data = {
        "elements": [],
        "wires": [
            {
                "x1": 1.0,
                "y1": 1.0,
                "x2": 1.0,  # Same as x1
                "y2": 1.0   # Same as y1
            }
        ]
    }
    
    invalid_file = temp_dir / "zero_length_wire.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    # Should not raise an error in non-strict mode
    output_path = importer.import_schematic(str(invalid_file), str(temp_dir), strict=False)
    assert os.path.exists(output_path)

def test_import_floating_component(temp_dir):
    """Test importing a schematic with a floating component."""
    invalid_data = {
        "elements": [
            {
                "type": "resistor",
                "x": 1.0,
                "y": 1.0,
                "rotation": 0.0,
                "value": "1k",
                "properties": {}
            }
        ],
        "wires": []  # No connections
    }
    
    invalid_file = temp_dir / "floating_component.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    importer = FalstadImporter()
    # Should not raise an error in non-strict mode
    output_path = importer.import_schematic(str(invalid_file), str(temp_dir), strict=False)
    assert os.path.exists(output_path) 