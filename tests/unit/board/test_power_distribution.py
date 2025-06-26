"""Unit tests for power distribution management."""
import unittest
from unittest.mock import Mock, patch
import pcbnew
from kicad_pcb_generator.core.board.power_distribution import (
    PowerDistributionManager,
    PowerDistributionConfig
)

class TestPowerDistributionConfig(unittest.TestCase):
    """Test power distribution configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = PowerDistributionConfig()
        
        self.assertEqual(config.min_trace_width, 0.5)
        self.assertEqual(config.max_trace_width, 5.0)
        self.assertEqual(config.min_clearance, 0.5)
        self.assertEqual(config.max_clearance, 10.0)
        self.assertEqual(config.max_voltage_drop, 0.1)
        self.assertEqual(config.decoupling_cap_distance, 2.0)
        self.assertTrue(config.star_topology)
        self.assertTrue(config.power_planes['enabled'])
        self.assertEqual(config.power_planes['min_width'], 2.0)
        self.assertEqual(config.power_planes['clearance'], 0.5)
        self.assertTrue(config.power_planes['thermal_relief'])
        self.assertEqual(config.current_capacity['max_current'], 5.0)
        self.assertEqual(config.current_capacity['temperature_rise'], 10)
        self.assertEqual(config.current_capacity['safety_factor'], 1.5)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = PowerDistributionConfig(
            min_trace_width=1.0,
            max_trace_width=10.0,
            min_clearance=1.0,
            max_clearance=20.0,
            max_voltage_drop=0.2,
            decoupling_cap_distance=5.0,
            star_topology=False,
            power_planes={
                'enabled': False,
                'min_width': 5.0,
                'clearance': 1.0,
                'thermal_relief': False
            },
            current_capacity={
                'max_current': 10.0,
                'temperature_rise': 20,
                'safety_factor': 2.0
            }
        )
        
        self.assertEqual(config.min_trace_width, 1.0)
        self.assertEqual(config.max_trace_width, 10.0)
        self.assertEqual(config.min_clearance, 1.0)
        self.assertEqual(config.max_clearance, 20.0)
        self.assertEqual(config.max_voltage_drop, 0.2)
        self.assertEqual(config.decoupling_cap_distance, 5.0)
        self.assertFalse(config.star_topology)
        self.assertFalse(config.power_planes['enabled'])
        self.assertEqual(config.power_planes['min_width'], 5.0)
        self.assertEqual(config.power_planes['clearance'], 1.0)
        self.assertFalse(config.power_planes['thermal_relief'])
        self.assertEqual(config.current_capacity['max_current'], 10.0)
        self.assertEqual(config.current_capacity['temperature_rise'], 20)
        self.assertEqual(config.current_capacity['safety_factor'], 2.0)

class TestPowerDistributionManager(unittest.TestCase):
    """Test power distribution manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = Mock(spec=pcbnew.BOARD)
        self.config = PowerDistributionConfig()
        self.manager = PowerDistributionManager(self.board, self.config)
        
        # Mock board methods
        self.board.GetNetsByName.return_value = {
            'VCC': Mock(GetNetname=lambda: 'VCC'),
            'GND': Mock(GetNetname=lambda: 'GND')
        }
        self.board.GetLayerID.return_value = 1
        self.board.GetFootprintCount.return_value = 0
    
    def test_initialization(self):
        """Test manager initialization."""
        self.assertEqual(self.manager.board, self.board)
        self.assertEqual(self.manager.config, self.config)
        self.assertIsNotNone(self.manager.logger)
        self.assertIsNotNone(self.manager.validator)
        self.assertIsNotNone(self.manager.analyzer)
        self.assertIsNotNone(self.manager.collector)
    
    @patch('pcbnew.VERSION', '9.0.0')
    def test_kicad_version_validation(self):
        """Test KiCad version validation."""
        manager = PowerDistributionManager(self.board)
        self.assertIsNotNone(manager)
    
    @patch('pcbnew.VERSION', '8.0.0')
    def test_invalid_kicad_version(self):
        """Test invalid KiCad version."""
        with self.assertRaises(RuntimeError):
            PowerDistributionManager(self.board)
    
    def test_is_power_net(self):
        """Test power net identification."""
        self.assertTrue(self.manager._is_power_net('VCC'))
        self.assertTrue(self.manager._is_power_net('VDD'))
        self.assertTrue(self.manager._is_power_net('VSS'))
        self.assertTrue(self.manager._is_power_net('POWER'))
        self.assertFalse(self.manager._is_power_net('SIGNAL'))
    
    def test_is_power_track(self):
        """Test power track identification."""
        track = Mock(spec=pcbnew.TRACK)
        track.GetNetname.return_value = 'VCC'
        self.assertTrue(self.manager._is_power_track(track))
        
        track.GetNetname.return_value = 'SIGNAL'
        self.assertFalse(self.manager._is_power_track(track))
    
    def test_is_power_component(self):
        """Test power component identification."""
        # Test regulator
        comp = Mock(spec=pcbnew.FOOTPRINT)
        comp.GetValue.return_value = 'regulator'
        comp.GetReference.return_value = 'U1'
        self.assertTrue(self.manager._is_power_component(comp))
        
        # Test LDO
        comp.GetValue.return_value = 'ldo'
        self.assertTrue(self.manager._is_power_component(comp))
        
        # Test non-power component
        comp.GetValue.return_value = 'resistor'
        comp.GetReference.return_value = 'R1'
        self.assertFalse(self.manager._is_power_component(comp))
    
    def test_get_or_create_power_zone(self):
        """Test power zone creation."""
        # Mock existing zone
        existing_zone = Mock(spec=pcbnew.ZONE)
        existing_zone.GetNetname.return_value = 'VCC'
        self.board.Zones.return_value = [existing_zone]
        
        net = Mock(spec=pcbnew.NETINFO_ITEM)
        net.GetNetname.return_value = 'VCC'
        
        zone = self.manager._get_or_create_power_zone(net)
        self.assertEqual(zone, existing_zone)
        
        # Test new zone creation
        self.board.Zones.return_value = []
        zone = self.manager._get_or_create_power_zone(net)
        self.assertIsInstance(zone, Mock)
        self.board.Add.assert_called_once()
    
    def test_optimize_zone_settings(self):
        """Test zone settings optimization."""
        zone = Mock(spec=pcbnew.ZONE)
        
        self.manager._optimize_zone_settings(zone)
        
        zone.SetThermalReliefGap.assert_called_once()
        zone.SetThermalReliefCopperBridge.assert_called_once()
        zone.SetThermalReliefSpokeCount.assert_called_once()
        zone.SetMinThickness.assert_called_once()
        zone.SetClearance.assert_called_once()
        zone.SetIslandRemovalMode.assert_called_once()
        zone.SetPriority.assert_called_once()
        zone.Rebuild.assert_called_once()
    
    def test_calculate_trace_width(self):
        """Test trace width calculation."""
        track = Mock(spec=pcbnew.TRACK)
        net = Mock(spec=pcbnew.NETINFO_ITEM)
        track.GetNet.return_value = net
        
        width = self.manager._calculate_trace_width(track)
        self.assertGreaterEqual(width, self.config.min_trace_width)
        self.assertLessEqual(width, self.config.max_trace_width)
    
    def test_add_component_decoupling(self):
        """Test decoupling capacitor addition."""
        comp = Mock(spec=pcbnew.FOOTPRINT)
        pad = Mock(spec=pcbnew.PAD)
        pad.GetNetname.return_value = 'VCC'
        comp.Pads.return_value = [pad]
        
        caps = self.manager._add_component_decoupling(comp)
        self.assertIsInstance(caps, list)
    
    def test_create_decoupling_capacitor(self):
        """Test decoupling capacitor creation."""
        power_pin = Mock(spec=pcbnew.PAD)
        power_pin.GetPosition.return_value = Mock(x=0, y=0)
        
        cap = self.manager._create_decoupling_capacitor('100n', power_pin)
        self.assertIsInstance(cap, Mock)
        self.board.Add.assert_called_once()

if __name__ == '__main__':
    unittest.main() 