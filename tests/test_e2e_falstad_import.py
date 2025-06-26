"""
End-to-end tests for Falstad schematic import functionality.
"""

import os
import json
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

def test_cli_import(valid_falstad_file, temp_dir, monkeypatch):
    """Test Falstad import through CLI."""
    from kicad_pcb_generator.cli import import_falstad
    
    # Mock sys.exit to prevent test from exiting
    def mock_exit(code):
        if code != 0:
            raise SystemExit(code)
    monkeypatch.setattr('sys.exit', mock_exit)
    
    # Test successful import
    import_falstad(valid_falstad_file, str(temp_dir), True)
    
    # Verify output files
    output_sch = temp_dir / "test_schematic.kicad_sch"
    assert output_sch.exists()
    
    # Test invalid file
    invalid_file = temp_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("invalid json")
    
    with pytest.raises(SystemExit):
        import_falstad(str(invalid_file), str(temp_dir), True)

def test_gui_import(valid_falstad_file, temp_dir):
    """Test Falstad import through GUI."""
    import tkinter as tk
    from kicad_pcb_generator.gui import AudioPCBDesignerGUI
    
    # Create root window
    root = tk.Tk()
    
    try:
        # Create GUI
        gui = AudioPCBDesignerGUI(root)
        
        # Set paths
        gui.falstad_path.set(valid_falstad_file)
        gui.output_path.set(str(temp_dir))
        gui.strict_mode.set(True)
        
        # Import schematic
        gui.import_falstad()
        
        # Verify output files
        output_sch = temp_dir / "test_schematic.kicad_sch"
        assert output_sch.exists()
        
    finally:
        root.destroy()

def test_import_workflow(valid_falstad_file, temp_dir):
    """Test complete import workflow."""
    # Create importer
    importer = FalstadImporter()
    
    # Import schematic
    output_path = importer.import_schematic(
        falstad_path=valid_falstad_file,
        output_dir=str(temp_dir),
        strict=True
    )
    
    # Verify output files
    assert os.path.exists(output_path)
    assert output_path.endswith(".kicad_sch")
    
    # Verify schematic content
    with open(output_path, 'r') as f:
        content = f.read()
        assert "kicad_sch" in content
        assert "R" in content  # Resistor
        assert "C" in content  # Capacitor
        assert "GND" in content  # Ground

def test_import_with_validation(valid_falstad_file, temp_dir):
    """Test import with validation."""
    # Create importer
    importer = FalstadImporter()
    
    # Test strict mode
    output_path = importer.import_schematic(
        falstad_path=valid_falstad_file,
        output_dir=str(temp_dir),
        strict=True
    )
    assert os.path.exists(output_path)
    
    # Test non-strict mode with warnings
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
    
    invalid_file = temp_dir / "invalid_schematic.json"
    with open(invalid_file, 'w') as f:
        json.dump(invalid_data, f)
    
    # Should not raise error in non-strict mode
    output_path = importer.import_schematic(
        falstad_path=str(invalid_file),
        output_dir=str(temp_dir),
        strict=False
    )
    assert os.path.exists(output_path)

def test_import_error_handling(temp_dir):
    """Test error handling during import."""
    importer = FalstadImporter()
    
    # Test non-existent file
    with pytest.raises(FalstadImportError):
        importer.import_schematic(
            falstad_path="nonexistent.json",
            output_dir=str(temp_dir),
            strict=True
        )
    
    # Test invalid JSON
    invalid_file = temp_dir / "invalid.json"
    with open(invalid_file, 'w') as f:
        f.write("invalid json")
    
    with pytest.raises(FalstadImportError):
        importer.import_schematic(
            falstad_path=str(invalid_file),
            output_dir=str(temp_dir),
            strict=True
        )
    
    # Test invalid coordinates
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
    
    with pytest.raises(FalstadImportError):
        importer.import_schematic(
            falstad_path=str(invalid_file),
            output_dir=str(temp_dir),
            strict=True
        ) 