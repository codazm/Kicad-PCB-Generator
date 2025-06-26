"""Unit tests for 3D model management."""
import unittest
import tempfile
import os
import pcbnew
from kicad_pcb_generator.core.manufacturing.models import ModelManagement, ModelConfig

class TestModelManagement(unittest.TestCase):
    """Test cases for 3D model management."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a minimal test board
        self.board = pcbnew.BOARD()
        
        # Create model management instance
        self.models = ModelManagement(self.board)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        os.rmdir(self.temp_dir)
    
    def test_generate_3d_model(self):
        """Test generating a 3D model."""
        # Generate 3D model
        output_path = os.path.join(self.temp_dir, "test_model.step")
        self.models.generate_3d_model(output_path)
        
        # Check if model was generated
        self.assertTrue(os.path.exists(output_path))
    
    def test_validate_3d_model(self):
        """Test validating a 3D model."""
        # Generate 3D model
        output_path = os.path.join(self.temp_dir, "test_model.step")
        self.models.generate_3d_model(output_path)
        
        # Validate model
        errors = self.models.validate_3d_model(output_path)
        
        # Check validation results
        self.assertIsInstance(errors, list)
    
    def test_update_model_config(self):
        """Test updating model configuration."""
        # Update configuration
        self.models.update_model_config(
            output_format="step",
            resolution=0.1,
            include_components=True
        )
        
        # Check updated values
        self.assertEqual(self.models.config.output_format, "step")
        self.assertEqual(self.models.config.resolution, 0.1)
        self.assertTrue(self.models.config.include_components)
    
    def test_invalid_board(self):
        """Test behavior with invalid board."""
        # Create model management without board
        models = ModelManagement()
        
        # Try to generate 3D model
        with self.assertRaises(RuntimeError):
            models.generate_3d_model("test_model.step")
    
    def test_invalid_output_path(self):
        """Test behavior with invalid output path."""
        # Try to generate 3D model with invalid path
        with self.assertRaises(ValueError):
            self.models.generate_3d_model("")  # Empty path
    
    def test_invalid_model_format(self):
        """Test behavior with invalid model format."""
        # Update configuration with invalid format
        with self.assertRaises(ValueError):
            self.models.update_model_config(
                output_format="invalid_format"
            )
    
    def test_invalid_resolution(self):
        """Test behavior with invalid resolution."""
        # Update configuration with invalid resolution
        with self.assertRaises(ValueError):
            self.models.update_model_config(
                resolution=0.0  # Invalid resolution
            )

if __name__ == '__main__':
    unittest.main() 
