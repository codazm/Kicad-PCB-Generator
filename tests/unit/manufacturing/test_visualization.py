"""Unit tests for the visualization manager."""
import unittest
import os
import tempfile
from kicad_pcb_generator.core.manufacturing.visualization import VisualizationManager, VisualizationConfig

class TestVisualizationManager(unittest.TestCase):
    def setUp(self):
        self.manager = VisualizationManager()
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

    def test_validate_pcbdraw_installation(self):
        """Test PcbDraw installation validation."""
        result = self.manager._validate_pcbdraw_installation()
        self.assertIsInstance(result, bool)

    def test_generate_visualization(self):
        """Test board visualization generation."""
        config = VisualizationConfig(
            style="default",
            resolution=300,
            transparency=True,
            highlight_nets=["GND", "VCC"],
            highlight_components=["R1", "C1"],
            highlight_pads=True,
            highlight_tracks=True,
            highlight_zones=True,
            highlight_vias=True,
            highlight_holes=True,
            highlight_silkscreen=True,
            highlight_soldermask=True,
            highlight_courtyard=True,
            highlight_fabrication=True,
            highlight_other=True
        )
        
        output_file = os.path.join(self.temp_dir, "visualization.png")
        result = self.manager.generate_visualization(self.test_board, output_file, config)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(output_file))

    def test_validate_visualization_config(self):
        """Test visualization configuration validation."""
        config = VisualizationConfig(
            style="default",
            resolution=300,
            transparency=True,
            highlight_nets=["GND", "VCC"],
            highlight_components=["R1", "C1"],
            highlight_pads=True,
            highlight_tracks=True,
            highlight_zones=True,
            highlight_vias=True,
            highlight_holes=True,
            highlight_silkscreen=True,
            highlight_soldermask=True,
            highlight_courtyard=True,
            highlight_fabrication=True,
            highlight_other=True
        )
        
        result = self.manager.validate_visualization(config)
        self.assertTrue(result)

    def test_invalid_visualization_config(self):
        """Test invalid visualization configuration."""
        config = VisualizationConfig(
            style="default",
            resolution=0,  # Invalid resolution
            transparency=True,
            highlight_nets=["GND", "VCC"],
            highlight_components=["R1", "C1"],
            highlight_pads=True,
            highlight_tracks=True,
            highlight_zones=True,
            highlight_vias=True,
            highlight_holes=True,
            highlight_silkscreen=True,
            highlight_soldermask=True,
            highlight_courtyard=True,
            highlight_fabrication=True,
            highlight_other=True
        )
        
        result = self.manager.validate_visualization(config)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main() 