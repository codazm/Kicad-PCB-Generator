"""End-to-end tests for the expedited PCB generation workflow."""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
import json
import sys

from kicad_pcb_generator.core.falstad_importer import FalstadImporter, FalstadImportError
from kicad_pcb_generator.core.project_manager import ProjectManager
from kicad_pcb_generator.core.pcb import PCBGenerator, PCBGenerationConfig
from kicad_pcb_generator.core.templates.board_presets import board_preset_registry, BoardProfile
from kicad_pcb_generator.cli import falstad2pcb, create_project, generate_pcb
from kicad_pcb_generator.core.validation.board_validator import BoardValidator
from kicad_pcb_generator.audio.validation.audio_validator import AudioPCBValidator
from kicad_pcb_generator.core.validation.real_time_validator import RealTimeValidator


class TestExpeditedWorkflow(unittest.TestCase):
    """End-to-end tests for the expedited PCB generation workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        cls.output_dir = os.path.join(cls.test_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Create test schematic
        cls.schematic_path = os.path.join(cls.test_dir, "test_circuit.json")
        cls._create_test_falstad_schematic(cls.schematic_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up each test case."""
        # Initialize components
        self.project_manager = ProjectManager(self.test_dir)
        self.pcb_generator = PCBGenerator(self.project_manager)
        self.falstad_importer = FalstadImporter()
        
        # Initialize validators
        self.board_validator = BoardValidator()
        self.audio_validator = AudioPCBValidator()
        self.realtime_validator = RealTimeValidator()

    def test_falstad2pcb_workflow(self):
        """Test the falstad2pcb expedited workflow."""
        # Create mock args for falstad2pcb
        class MockArgs:
            def __init__(self):
                self.falstad = self.schematic_path
                self.project = "test_project"
                self.config = None
                self.export = ["gerber", "bom"]
        
        args = MockArgs()
        args.falstad = self.schematic_path
        args.project = "test_project"
        args.config = None
        args.export = ["gerber", "bom"]
        
        # Test falstad2pcb workflow
        try:
            falstad2pcb(args)
            
            # Verify project was created
            project_path = self.project_manager.get_project_path("test_project")
            self.assertTrue(project_path.exists())
            
            # Verify output files exist
            output_path = project_path / "output"
            self.assertTrue(output_path.exists())
            
            # Verify PCB file was created
            pcb_files = list(output_path.glob("*.kicad_pcb"))
            self.assertGreater(len(pcb_files), 0)
            
        except Exception as e:
            # Skip if KiCad is not available
            if "pcbnew" in str(e).lower():
                self.skipTest("KiCad not available for testing")
            else:
                raise

    def test_board_preset_workflow(self):
        """Test workflow with board presets."""
        # Test creating project with board preset
        class MockCreateArgs:
            def __init__(self):
                self.name = "preset_test_project"
                self.template = "basic_audio_amp"
                self.board_preset = "Eurorack 3U"
        
        create_args = MockCreateArgs()
        
        try:
            create_project(create_args)
            
            # Verify project was created with board preset
            project_path = self.project_manager.get_project_path("preset_test_project")
            self.assertTrue(project_path.exists())
            
            # Load project config to verify board preset was applied
            config_path = project_path / "config" / "project.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Check if board config was stored
                self.assertIn("settings", config_data)
                self.assertIn("board_config", config_data["settings"])
                
        except Exception as e:
            # Skip if KiCad is not available
            if "pcbnew" in str(e).lower():
                self.skipTest("KiCad not available for testing")
            else:
                raise

    def test_falstad_importer_workflow(self):
        """Test Falstad importer workflow."""
        # Test importing Falstad schematic
        try:
            # Load and parse Falstad file
            with open(self.schematic_path, 'r') as f:
                falstad_data = json.load(f)
            
            # Convert to netlist
            netlist = self.falstad_importer.to_netlist(falstad_data)
            
            # Verify netlist was created
            self.assertIsNotNone(netlist)
            self.assertGreater(len(netlist.footprints), 0)
            self.assertGreater(len(netlist.nets), 0)
            
            # Verify component mapping
            component_types = [fp.lib_id for fp in netlist.footprints]
            self.assertIn("Device:R", component_types)
            self.assertIn("Device:C", component_types)
            
        except Exception as e:
            self.fail(f"Falstad import workflow failed: {e}")

    def test_board_preset_validation(self):
        """Test board preset validation."""
        # Test valid Eurorack 3U dimensions
        is_valid = board_preset_registry.validate_board_size(128.5, 128.5, BoardProfile.EURORACK_3U)
        self.assertTrue(is_valid)
        
        # Test with tolerance
        is_valid = board_preset_registry.validate_board_size(127.5, 129.5, BoardProfile.EURORACK_3U)
        self.assertTrue(is_valid)
        
        # Test invalid dimensions
        is_valid = board_preset_registry.validate_board_size(100.0, 100.0, BoardProfile.EURORACK_3U)
        self.assertFalse(is_valid)

    def test_express_workflow_error_handling(self):
        """Test error handling in the expedited workflow."""
        # Test invalid Falstad file
        invalid_schematic_path = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_schematic_path, 'w') as f:
            f.write('{"invalid": "json"}')
        
        class MockArgs:
            def __init__(self):
                self.falstad = invalid_schematic_path
                self.project = "error_test_project"
                self.config = None
                self.export = []
        
        args = MockArgs()
        
        # Should raise FalstadImportError
        with self.assertRaises(FalstadImportError):
            falstad2pcb(args)

    @staticmethod
    def _create_test_falstad_schematic(path: str):
        """Create a test Falstad JSON schematic file."""
        content = {
            "elements": [
                {
                    "type": "resistor",
                    "value": "10k",
                    "properties": {},
                    "pos": {"x": 100, "y": 100}
                },
                {
                    "type": "capacitor",
                    "value": "100n",
                    "properties": {},
                    "pos": {"x": 200, "y": 100}
                },
                {
                    "type": "opamp",
                    "value": "TL072",
                    "properties": {"pins": "8"},
                    "pos": {"x": 300, "y": 100}
                }
            ],
            "wires": [
                {"start": {"x": 100, "y": 100}, "end": {"x": 200, "y": 100}},
                {"start": {"x": 200, "y": 100}, "end": {"x": 300, "y": 100}}
            ]
        }
        with open(path, 'w') as f:
            json.dump(content, f)


if __name__ == '__main__':
    unittest.main() 