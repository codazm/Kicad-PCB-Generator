"""Unit tests for routing management."""
import unittest
import tempfile
import os
import pcbnew
from kicad_pcb_generator.core.manufacturing.routing import RoutingManagement, RoutingConfig

class TestRoutingManagement(unittest.TestCase):
    """Test cases for routing management."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a minimal test board
        self.board = pcbnew.BOARD()
        
        # Create routing management instance
        self.routing = RoutingManagement(self.board)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        os.rmdir(self.temp_dir)
    
    def test_create_differential_pair(self):
        """Test creating a differential pair."""
        # Create a differential pair
        self.routing.create_differential_pair(
            name="test_pair",
            net1="net1",
            net2="net2",
            width=0.2,
            gap=0.1
        )
        
        # Check if pair was created
        pairs = self.routing.get_differential_pairs()
        self.assertIn("test_pair", pairs)
        
        # Check pair properties
        pair = pairs["test_pair"]
        self.assertEqual(pair.name, "test_pair")
        self.assertEqual(pair.net1, "net1")
        self.assertEqual(pair.net2, "net2")
        self.assertEqual(pair.width, 0.2)
        self.assertEqual(pair.gap, 0.1)
    
    def test_match_trace_lengths(self):
        """Test trace length matching."""
        # Create a differential pair
        self.routing.create_differential_pair(
            name="test_pair",
            net1="net1",
            net2="net2"
        )
        
        # Match trace lengths
        self.routing.match_trace_lengths("test_pair", tolerance=0.1)
        
        # Check if matching was applied
        pairs = self.routing.get_differential_pairs()
        self.assertIn("test_pair", pairs)
    
    def test_validate_routing(self):
        """Test routing validation."""
        # Create a differential pair
        self.routing.create_differential_pair(
            name="test_pair",
            net1="net1",
            net2="net2"
        )
        
        # Validate routing
        errors = self.routing.validate_routing()
        
        # Check validation results
        self.assertIsInstance(errors, list)
    
    def test_update_routing_config(self):
        """Test updating routing configuration."""
        # Update configuration
        self.routing.update_routing_config(
            min_trace_width=0.1,
            min_clearance=0.2,
            min_via_diameter=0.3
        )
        
        # Check updated values
        self.assertEqual(self.routing.config.min_trace_width, 0.1)
        self.assertEqual(self.routing.config.min_clearance, 0.2)
        self.assertEqual(self.routing.config.min_via_diameter, 0.3)
    
    def test_invalid_board(self):
        """Test behavior with invalid board."""
        # Create routing management without board
        routing = RoutingManagement()
        
        # Try to create differential pair
        with self.assertRaises(RuntimeError):
            routing.create_differential_pair(
                name="test_pair",
                net1="net1",
                net2="net2"
            )
    
    def test_invalid_pair_parameters(self):
        """Test behavior with invalid pair parameters."""
        # Try to create differential pair with invalid width
        with self.assertRaises(ValueError):
            self.routing.create_differential_pair(
                name="test_pair",
                net1="net1",
                net2="net2",
                width=0.0  # Invalid width
            )
        
        # Try to create differential pair with invalid gap
        with self.assertRaises(ValueError):
            self.routing.create_differential_pair(
                name="test_pair",
                net1="net1",
                net2="net2",
                width=0.2,
                gap=0.0  # Invalid gap
            )

if __name__ == '__main__':
    unittest.main() 