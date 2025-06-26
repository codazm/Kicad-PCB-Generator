"""Unit tests for ground plane optimization."""
import unittest
from unittest.mock import Mock, patch
import pcbnew
from kicad_pcb_generator.core.board.ground_plane import GroundPlaneOptimizer, GroundPlaneConfig
from kicad_pcb_generator.core.board.layer_manager import LayerType

class TestGroundPlaneConfig(unittest.TestCase):
    """Test ground plane configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = GroundPlaneConfig()
        
        self.assertEqual(config.min_area, 1000.0)
        self.assertEqual(config.min_width, 2.0)
        self.assertEqual(config.thermal_relief_gap, 0.5)
        self.assertEqual(config.thermal_relief_width, 0.3)
        self.assertEqual(config.thermal_relief_spokes, 4)
        self.assertEqual(config.via_spacing, 1.0)
        self.assertEqual(config.via_diameter, 0.6)
        self.assertEqual(config.via_drill, 0.3)
        self.assertTrue(config.split_analog_digital)
        self.assertTrue(config.star_grounding)
        self.assertTrue(config.optimize_thermal)
        self.assertTrue(config.validate_design)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = GroundPlaneConfig(
            min_area=2000.0,
            min_width=3.0,
            thermal_relief_gap=0.6,
            thermal_relief_width=0.4,
            thermal_relief_spokes=6,
            via_spacing=2.0,
            via_diameter=0.8,
            via_drill=0.4,
            split_analog_digital=False,
            star_grounding=False,
            optimize_thermal=False,
            validate_design=False
        )
        
        self.assertEqual(config.min_area, 2000.0)
        self.assertEqual(config.min_width, 3.0)
        self.assertEqual(config.thermal_relief_gap, 0.6)
        self.assertEqual(config.thermal_relief_width, 0.4)
        self.assertEqual(config.thermal_relief_spokes, 6)
        self.assertEqual(config.via_spacing, 2.0)
        self.assertEqual(config.via_diameter, 0.8)
        self.assertEqual(config.via_drill, 0.4)
        self.assertFalse(config.split_analog_digital)
        self.assertFalse(config.star_grounding)
        self.assertFalse(config.optimize_thermal)
        self.assertFalse(config.validate_design)

class TestGroundPlaneOptimizer(unittest.TestCase):
    """Test ground plane optimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = Mock(spec=pcbnew.BOARD)
        self.config = GroundPlaneConfig()
        self.optimizer = GroundPlaneOptimizer(self.board, self.config)
        
        # Mock layer manager
        self.optimizer.layer_manager._layer_properties = {
            0: Mock(type=LayerType.GROUND),
            1: Mock(type=LayerType.AUDIO_GROUND),
            2: Mock(type=LayerType.SIGNAL)
        }
        
        # Mock board methods
        self.board.GetNetcodeFromNetname.return_value = 1
        self.board.Zones.return_value = []
    
    def test_initialization(self):
        """Test optimizer initialization."""
        self.assertEqual(self.optimizer.board, self.board)
        self.assertEqual(self.optimizer.config, self.config)
        self.assertIsNotNone(self.optimizer.logger)
        self.assertIsNotNone(self.optimizer.layer_manager)
        self.assertIsNotNone(self.optimizer.validator)
    
    def test_get_ground_layers(self):
        """Test ground layer identification."""
        ground_layers = self.optimizer._get_ground_layers()
        self.assertEqual(len(ground_layers), 2)
        self.assertIn(0, ground_layers)
        self.assertIn(1, ground_layers)
    
    def test_get_or_create_ground_zone(self):
        """Test ground zone creation."""
        # Mock existing zone
        existing_zone = Mock(spec=pcbnew.ZONE)
        existing_zone.GetLayer.return_value = 0
        existing_zone.GetNetname.return_value = "GND"
        self.board.Zones.return_value = [existing_zone]
        
        zone = self.optimizer._get_or_create_ground_zone(0)
        self.assertEqual(zone, existing_zone)
        
        # Test new zone creation
        self.board.Zones.return_value = []
        zone = self.optimizer._get_or_create_ground_zone(0)
        self.assertIsInstance(zone, Mock)
        self.board.Add.assert_called_once()
    
    def test_optimize_thermal_relief(self):
        """Test thermal relief optimization."""
        # Mock ground zone
        zone = Mock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        self.board.Zones.return_value = [zone]
        
        self.optimizer._optimize_thermal_relief()
        
        zone.SetThermalReliefGap.assert_called_once()
        zone.SetThermalReliefCopperBridge.assert_called_once()
        zone.SetThermalReliefSpokeCount.assert_called_once()
        zone.Rebuild.assert_called_once()
    
    def test_add_ground_vias(self):
        """Test ground via addition."""
        # Mock ground zone
        zone = Mock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetBoundingBox.return_value = Mock(
            GetLeft=lambda: 0,
            GetRight=lambda: 1000000,
            GetTop=lambda: 0,
            GetBottom=lambda: 1000000
        )
        zone.HitTest.return_value = True
        self.board.Zones.return_value = [zone]
        
        self.optimizer._add_ground_vias()
        
        self.board.Add.assert_called()
    
    def test_split_analog_digital_ground(self):
        """Test analog/digital ground splitting."""
        # Mock ground zone
        zone = Mock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetLayer.return_value = 0
        self.board.Zones.return_value = [zone]
        
        self.optimizer._split_analog_digital_ground()
        
        self.assertEqual(self.board.Add.call_count, 2)  # Two new zones
        self.board.Remove.assert_called_once()
    
    def test_implement_star_grounding(self):
        """Test star grounding implementation."""
        # Mock ground zones
        zones = [
            Mock(spec=pcbnew.ZONE, GetNetname=lambda: "GND", GetPosition=lambda: Mock(x=0, y=0)),
            Mock(spec=pcbnew.ZONE, GetNetname=lambda: "AGND", GetPosition=lambda: Mock(x=1000000, y=1000000))
        ]
        self.board.Zones.return_value = zones
        
        self.optimizer._implement_star_grounding()
        
        self.board.Add.assert_called()
    
    def test_validate_ground_plane(self):
        """Test ground plane validation."""
        # Mock validator
        self.optimizer.validator.validate_board.return_value = {
            "General": [Mock(message="Ground plane issue")]
        }
        
        self.optimizer._validate_ground_plane()
        
        self.optimizer.validator.validate_board.assert_called_once_with(self.board)
    
    @patch('pcbnew.Version')
    def test_kicad_version_validation(self, mock_version):
        """Test KiCad version validation."""
        # Test valid version
        mock_version.return_value = "9.0.0"
        optimizer = GroundPlaneOptimizer(self.board)
        self.assertIsNotNone(optimizer)
        
        # Test invalid version
        mock_version.return_value = "8.0.0"
        with self.assertRaises(RuntimeError):
            GroundPlaneOptimizer(self.board)

if __name__ == '__main__':
    unittest.main() 