"""Unit tests for the panelization manager."""
import unittest
import os
import tempfile
from kicad_pcb_generator.core.manufacturing.panelization import PanelizationManager, PanelizationConfig

class TestPanelizationManager(unittest.TestCase):
    def setUp(self):
        self.manager = PanelizationManager()
        self.temp_dir = tempfile.mkdtemp()
        self.test_board = os.path.join(self.temp_dir, "test_board.kicad_pcb")
        
        # Create a minimal test board file
        with open(self.test_board, "w") as f:
            f.write("(kicad_pcb (version 20211123) (host pcbnew 9.0.0)\n")
            f.write("  (general\n")
            f.write("    (thickness 1.6)\n")
            f.write("    (drawings 0)\n")
            f.write("    (tracks 0)\n")
            f.write("    (zones 0)\n")
            f.write("    (modules 0)\n")
            f.write("    (nets 0)\n")
            f.write("  )\n")
            f.write("  (page A4)\n")
            f.write("  (layers\n")
            f.write("    (0 F.Cu signal)\n")
            f.write("    (31 B.Cu signal)\n")
            f.write("  )\n")
            f.write(")")

    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.test_board):
            os.remove(self.test_board)
        os.rmdir(self.temp_dir)

    def test_validate_kikit_installation(self):
        """Test KiKit installation validation."""
        result = self.manager._validate_kikit_installation()
        self.assertIsInstance(result, bool)

    def test_panelize_board(self):
        """Test board panelization."""
        config = PanelizationConfig(
            rows=2,
            columns=2,
            spacing=5.0,
            frame_width=2.0,
            mouse_bites=True,
            vcuts=True,
            tooling_holes=True,
            fiducials=True
        )
        
        output_file = os.path.join(self.temp_dir, "panelized.kicad_pcb")
        result = self.manager.panelize_board(self.test_board, output_file, config)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))

    def test_validate_panelization_config(self):
        """Test panelization configuration validation."""
        config = PanelizationConfig(
            rows=2,
            columns=2,
            spacing=5.0,
            frame_width=2.0,
            mouse_bites=True,
            vcuts=True,
            tooling_holes=True,
            fiducials=True
        )
        
        result = self.manager.validate_panelization_config(config)
        self.assertTrue(result)

    def test_invalid_panelization_config(self):
        """Test invalid panelization configuration."""
        config = PanelizationConfig(
            rows=0,  # Invalid rows
            columns=2,
            spacing=5.0,
            frame_width=2.0,
            mouse_bites=True,
            vcuts=True,
            tooling_holes=True,
            fiducials=True
        )
        
        result = self.manager.validate_panelization_config(config)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main() 