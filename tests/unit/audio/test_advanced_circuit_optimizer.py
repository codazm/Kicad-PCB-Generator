"""
Unit tests for the advanced circuit optimizer.
"""

import unittest
from unittest.mock import Mock, patch
import pcbnew
import numpy as np

from kicad_pcb_generator.audio.optimization.advanced_circuit_optimizer import (
    AdvancedCircuitOptimizer,
    OptimizationType,
    OptimizationResult
)

class TestAdvancedCircuitOptimizer(unittest.TestCase):
    """Test cases for AdvancedCircuitOptimizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = Mock(spec=pcbnew.BOARD)
        self.optimizer = AdvancedCircuitOptimizer(self.board)
        
        # Mock board methods
        self.board.GetNetsByName.return_value = {
            'VCC': Mock(spec=pcbnew.NETINFO_ITEM),
            'GND': Mock(spec=pcbnew.NETINFO_ITEM),
            'SIGNAL1': Mock(spec=pcbnew.NETINFO_ITEM),
            'SIGNAL2': Mock(spec=pcbnew.NETINFO_ITEM)
        }
        
        # Mock footprints
        self.mock_footprints = [
            self._create_mock_footprint('R1', ['Power']),
            self._create_mock_footprint('C1', ['HighSpeed']),
            self._create_mock_footprint('U1', ['Thermal'])
        ]
        self.board.GetFootprints.return_value = self.mock_footprints
    
    def _create_mock_footprint(self, reference: str, properties: list) -> Mock:
        """Create a mock footprint.
        
        Args:
            reference: Component reference
            properties: List of property names
            
        Returns:
            Mock footprint
        """
        footprint = Mock(spec=pcbnew.FOOTPRINT)
        footprint.GetReference.return_value = reference
        footprint.GetProperties.return_value = [
            Mock(GetName=lambda: prop) for prop in properties
        ]
        return footprint
    
    def test_optimize_circuit(self):
        """Test optimize_circuit method."""
        # Mock individual optimization results
        mock_results = {
            OptimizationType.SIGNAL_PATH: OptimizationResult(
                type=OptimizationType.SIGNAL_PATH,
                score=0.9,
                changes=[{'type': 'track_width', 'net': 'SIGNAL1'}],
                metrics={'impedance': 50.0},
                warnings=[],
                errors=[]
            ),
            OptimizationType.POWER_DISTRIBUTION: OptimizationResult(
                type=OptimizationType.POWER_DISTRIBUTION,
                score=0.8,
                changes=[{'type': 'power_trace', 'net': 'VCC'}],
                metrics={'voltage_drop': 0.05},
                warnings=[],
                errors=[]
            ),
            OptimizationType.GROUND_PLANE: OptimizationResult(
                type=OptimizationType.GROUND_PLANE,
                score=0.95,
                changes=[{'type': 'ground_plane', 'layer': 'In2.Cu'}],
                metrics={'ground_impedance': 0.1},
                warnings=[],
                errors=[]
            ),
            OptimizationType.COMPONENT_PLACEMENT: OptimizationResult(
                type=OptimizationType.COMPONENT_PLACEMENT,
                score=0.85,
                changes=[{'type': 'placement', 'component': 'R1'}],
                metrics={'placement_score': 0.85},
                warnings=[],
                errors=[]
            ),
            OptimizationType.THERMAL: OptimizationResult(
                type=OptimizationType.THERMAL,
                score=0.9,
                changes=[{'type': 'thermal_relief', 'component': 'U1'}],
                metrics={'max_temperature': 70.0},
                warnings=[],
                errors=[]
            ),
            OptimizationType.EMI: OptimizationResult(
                type=OptimizationType.EMI,
                score=0.95,
                changes=[{'type': 'shielding', 'area': 'A1'}],
                metrics={'emi_level': -40.0},
                warnings=[],
                errors=[]
            )
        }
        
        # Patch individual optimization methods
        with patch.multiple(
            self.optimizer,
            optimize_signal_paths=lambda: mock_results[OptimizationType.SIGNAL_PATH],
            optimize_power_distribution=lambda: mock_results[OptimizationType.POWER_DISTRIBUTION],
            optimize_ground_plane=lambda: mock_results[OptimizationType.GROUND_PLANE],
            optimize_component_placement=lambda: mock_results[OptimizationType.COMPONENT_PLACEMENT],
            optimize_thermal=lambda: mock_results[OptimizationType.THERMAL],
            optimize_emi=lambda: mock_results[OptimizationType.EMI]
        ):
            result = self.optimizer.optimize_circuit()
            
            # Verify combined results
            self.assertAlmostEqual(result.score, 0.89, places=2)
            self.assertEqual(len(result.changes), 6)
            self.assertEqual(len(result.metrics), 6)
            self.assertEqual(len(result.warnings), 0)
            self.assertEqual(len(result.errors), 0)
    
    def test_optimize_signal_paths(self):
        """Test optimize_signal_paths method."""
        # Mock track
        mock_track = Mock(spec=pcbnew.TRACK)
        mock_track.GetWidth.return_value = 200000  # 0.2mm
        mock_track.SetWidth = Mock()
        
        # Mock net
        mock_net = Mock(spec=pcbnew.NETINFO_ITEM)
        mock_net.GetTracks.return_value = [mock_track]
        
        # Update board mock
        self.board.GetNetsByName.return_value = {
            'SIGNAL1': mock_net
        }
        
        result = self.optimizer.optimize_signal_paths()
        
        # Verify results
        self.assertEqual(result.type, OptimizationType.SIGNAL_PATH)
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(len(result.changes), 1)
        self.assertEqual(result.changes[0]['type'], 'track_width')
        self.assertEqual(result.changes[0]['net'], 'SIGNAL1')
        mock_track.SetWidth.assert_called_once()
    
    def test_optimize_power_distribution(self):
        """Test optimize_power_distribution method."""
        # Mock power net
        mock_net = Mock(spec=pcbnew.NETINFO_ITEM)
        mock_net.GetNetname.return_value = 'VCC'
        
        # Update board mock
        self.board.GetNetsByName.return_value = {
            'VCC': mock_net
        }
        
        result = self.optimizer.optimize_power_distribution()
        
        # Verify results
        self.assertEqual(result.type, OptimizationType.POWER_DISTRIBUTION)
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(len(result.changes), 0)  # No changes as methods are not implemented
        self.assertEqual(result.metrics['voltage_drop'], 0.05)
    
    def test_optimize_ground_plane(self):
        """Test optimize_ground_plane method."""
        result = self.optimizer.optimize_ground_plane()
        
        # Verify results
        self.assertEqual(result.type, OptimizationType.GROUND_PLANE)
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(len(result.changes), 0)  # No changes as methods are not implemented
        self.assertEqual(result.metrics['ground_impedance'], 0.1)
    
    def test_optimize_component_placement(self):
        """Test optimize_component_placement method."""
        # Mock component position
        mock_position = pcbnew.VECTOR2I(1000000, 1000000)  # 1mm, 1mm
        
        # Patch _find_optimal_position
        with patch.object(
            self.optimizer,
            '_find_optimal_position',
            return_value=mock_position
        ):
            result = self.optimizer.optimize_component_placement()
            
            # Verify results
            self.assertEqual(result.type, OptimizationType.COMPONENT_PLACEMENT)
            self.assertAlmostEqual(result.score, 0.9)
            self.assertEqual(len(result.changes), 3)  # One for each component
            for change in result.changes:
                self.assertEqual(change['type'], 'component_placement')
                self.assertIn(change['reference'], ['R1', 'C1', 'U1'])
                self.assertEqual(change['new_position'], mock_position)
    
    def test_optimize_thermal(self):
        """Test optimize_thermal method."""
        result = self.optimizer.optimize_thermal()
        
        # Verify results
        self.assertEqual(result.type, OptimizationType.THERMAL)
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(len(result.changes), 0)  # No changes as methods are not implemented
        self.assertEqual(result.metrics['max_temperature'], 70.0)
    
    def test_optimize_emi(self):
        """Test optimize_emi method."""
        result = self.optimizer.optimize_emi()
        
        # Verify results
        self.assertEqual(result.type, OptimizationType.EMI)
        self.assertAlmostEqual(result.score, 0.9)
        self.assertEqual(len(result.changes), 0)  # No changes as methods are not implemented
        self.assertEqual(result.metrics['emi_level'], -40.0)
    
    def test_sort_components_by_importance(self):
        """Test _sort_components_by_importance method."""
        sorted_components = self.optimizer._sort_components_by_importance(self.mock_footprints)
        
        # Verify sorting order
        self.assertEqual(sorted_components[0].GetReference(), 'R1')  # Power
        self.assertEqual(sorted_components[1].GetReference(), 'C1')  # HighSpeed
        self.assertEqual(sorted_components[2].GetReference(), 'U1')  # Thermal
    
    def test_get_high_power_components(self):
        """Test _get_high_power_components method."""
        high_power_components = self.optimizer._get_high_power_components()
        
        # Verify results
        self.assertEqual(len(high_power_components), 1)
        self.assertEqual(high_power_components[0].GetReference(), 'R1')
    
    def test_error_handling(self):
        """Test error handling in optimization methods."""
        # Mock an error in optimize_signal_paths
        with patch.object(
            self.optimizer,
            'optimize_signal_paths',
            side_effect=Exception('Test error')
        ):
            with self.assertRaises(Exception) as context:
                self.optimizer.optimize_circuit()
            
            self.assertEqual(str(context.exception), 'Test error')

if __name__ == '__main__':
    unittest.main() 
