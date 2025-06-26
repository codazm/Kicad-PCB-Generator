"""Unit tests for the output manager."""
import unittest
import os
import tempfile
from kicad_pcb_generator.core.manufacturing.output import OutputManager, OutputConfig

class TestOutputManager(unittest.TestCase):
    def setUp(self):
        self.manager = OutputManager()
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

    def test_validate_gerber2blend_installation(self):
        """Test gerber2blend installation validation."""
        result = self.manager._validate_gerber2blend_installation()
        self.assertIsInstance(result, bool)

    def test_generate_output(self):
        """Test manufacturing output generation."""
        config = OutputConfig(
            generate_gerber=True,
            generate_drill=True,
            generate_3d=True,
            generate_pdf=True,
            generate_bom=True,
            generate_pick_and_place=True,
            output_directory=self.temp_dir
        )
        
        result = self.manager.generate_output(self.test_board, config)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(all(os.path.exists(path) for path in result.values()))

    def test_generate_gerber_files(self):
        """Test Gerber file generation."""
        result = self.manager._generate_gerber_files(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(all(os.path.exists(path) for path in result.values()))

    def test_generate_drill_files(self):
        """Test drill file generation."""
        result = self.manager._generate_drill_files(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(all(os.path.exists(path) for path in result.values()))

    def test_generate_3d_visualization(self):
        """Test 3D visualization generation."""
        result = self.manager._generate_3d_visualization(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(all(os.path.exists(path) for path in result.values()))

    def test_generate_pdf(self):
        """Test PDF generation."""
        result = self.manager._generate_pdf(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.exists(result))

    def test_generate_bom(self):
        """Test BOM generation."""
        result = self.manager._generate_bom(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.exists(result))

    def test_generate_pick_and_place(self):
        """Test pick and place file generation."""
        result = self.manager._generate_pick_and_place(self.test_board, self.temp_dir)
        
        self.assertIsInstance(result, str)
        self.assertTrue(os.path.exists(result))

if __name__ == "__main__":
    unittest.main() 