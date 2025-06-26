"""Unit tests for thermal management."""
import unittest
import tempfile
import os
import pcbnew
from kicad_pcb_generator.core.manufacturing.thermal import ThermalManagement, ThermalConfig

class TestThermalManagement(unittest.TestCase):
    """Test cases for thermal management."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a minimal test board
        self.board = pcbnew.BOARD()
        
        # Create thermal management instance
        self.thermal = ThermalManagement(self.board)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        os.rmdir(self.temp_dir)
    
    def test_create_thermal_zone(self):
        """Test creating a thermal zone."""
        # Create a thermal zone
        self.thermal.create_thermal_zone(
            name="test_zone",
            position=(10.0, 10.0),
            size=(20.0, 20.0),
            temperature=25.0,
            components=["R1", "R2"]
        )
        
        # Check if zone was created
        zones = self.thermal.get_thermal_zones()
        self.assertIn("test_zone", zones)
        
        # Check zone properties
        zone = zones["test_zone"]
        self.assertEqual(zone.name, "test_zone")
        self.assertEqual(zone.position, (10.0, 10.0))
        self.assertEqual(zone.size, (20.0, 20.0))
        self.assertEqual(zone.temperature, 25.0)
        self.assertEqual(zone.components, ["R1", "R2"])
    
    def test_analyze_thermal(self):
        """Test thermal analysis."""
        # Create a thermal zone
        self.thermal.create_thermal_zone(
            name="test_zone",
            position=(10.0, 10.0),
            size=(20.0, 20.0)
        )
        
        # Analyze thermal performance
        temperatures = self.thermal.analyze_thermal()
        
        # Check results
        self.assertIn("test_zone", temperatures)
        self.assertIsInstance(temperatures["test_zone"], float)
    
    def test_optimize_thermal_design(self):
        """Test thermal design optimization."""
        # Create a thermal zone
        self.thermal.create_thermal_zone(
            name="test_zone",
            position=(10.0, 10.0),
            size=(20.0, 20.0)
        )
        
        # Optimize thermal design
        self.thermal.optimize_thermal_design()
        
        # Check if optimization was applied
        zones = self.thermal.get_thermal_zones()
        self.assertIn("test_zone", zones)
    
    def test_validate_thermal_design(self):
        """Test thermal design validation."""
        # Create a thermal zone
        self.thermal.create_thermal_zone(
            name="test_zone",
            position=(10.0, 10.0),
            size=(20.0, 20.0)
        )
        
        # Validate thermal design
        errors = self.thermal.validate_thermal_design()
        
        # Check validation results
        self.assertIsInstance(errors, list)
    
    def test_update_thermal_config(self):
        """Test updating thermal configuration."""
        # Update configuration
        self.thermal.update_thermal_config(
            max_temperature=120.0,
            min_component_spacing=1.0
        )
        
        # Check updated values
        self.assertEqual(self.thermal.config.max_temperature, 120.0)
        self.assertEqual(self.thermal.config.min_component_spacing, 1.0)
    
    def test_invalid_board(self):
        """Test behavior with invalid board."""
        # Create thermal management without board
        thermal = ThermalManagement()
        
        # Try to create thermal zone
        with self.assertRaises(RuntimeError):
            thermal.create_thermal_zone(
                name="test_zone",
                position=(10.0, 10.0),
                size=(20.0, 20.0)
            )
    
    def test_invalid_zone_parameters(self):
        """Test behavior with invalid zone parameters."""
        # Try to create thermal zone with invalid position
        with self.assertRaises(ValueError):
            self.thermal.create_thermal_zone(
                name="test_zone",
                position=(-1.0, -1.0),  # Invalid position
                size=(20.0, 20.0)
            )
        
        # Try to create thermal zone with invalid size
        with self.assertRaises(ValueError):
            self.thermal.create_thermal_zone(
                name="test_zone",
                position=(10.0, 10.0),
                size=(0.0, 0.0)  # Invalid size
            )

if __name__ == '__main__':
    unittest.main() 