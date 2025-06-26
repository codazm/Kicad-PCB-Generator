"""Tests for the enhanced validator module."""

import unittest
from unittest.mock import MagicMock, patch
import pcbnew

from kicad_pcb_generator.core.validation.enhanced_validator import (
    EnhancedValidator,
    EnhancedValidationCategory,
    EnhancedValidationResult
)

class TestEnhancedValidator(unittest.TestCase):
    """Test cases for the EnhancedValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = EnhancedValidator()
        self.mock_board = MagicMock(spec=pcbnew.BOARD)
        
        # Mock board methods
        self.mock_board.GetFootprints.return_value = []
        self.mock_board.GetTracks.return_value = []
        self.mock_board.GetVias.return_value = []
        self.mock_board.Zones.return_value = []
        self.mock_board.GetPads.return_value = []
        self.mock_board.GetLayerName.return_value = "Test Layer"
    
    def test_thermal_validation(self):
        """Test thermal validation functionality."""
        # Create mock footprint with power dissipation
        mock_footprint = MagicMock()
        mock_footprint.GetReference.return_value = "U1"
        mock_footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_footprint.GetPowerDissipation.return_value = 2.0  # 2W power dissipation
        mock_footprint.Pads.return_value = []
        
        self.mock_board.GetFootprints.return_value = [mock_footprint]
        
        # Run validation
        results = self.validator._validate_thermal(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, EnhancedValidationResult) and
            r.category == EnhancedValidationCategory.THERMAL and
            "High power component" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_cross_layer_validation(self):
        """Test cross-layer validation functionality."""
        # Create mock track that changes layers
        mock_track = MagicMock()
        mock_track.GetLayer.return_value = 0
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_track.GetEnd.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        
        self.mock_board.GetTracks.return_value = [mock_track]
        self.mock_board.GetVias.return_value = []  # No vias for layer transition
        
        # Run validation
        results = self.validator._validate_cross_layer(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, EnhancedValidationResult) and
            r.category == EnhancedValidationCategory.CROSS_LAYER and
            "Track changes layers without via" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_signal_integrity_validation(self):
        """Test signal integrity validation functionality."""
        # Create mock track with high-speed signal
        mock_track = MagicMock()
        mock_track.GetNetname.return_value = "CLK1"
        mock_track.GetWidth.return_value = 100000  # 0.1mm width
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        self.mock_board.GetTracks.return_value = [mock_track]
        
        # Run validation
        results = self.validator._validate_signal_integrity(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, EnhancedValidationResult) and
            r.category == EnhancedValidationCategory.SIGNAL_INTEGRITY and
            "High-speed signal" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_power_distribution_validation(self):
        """Test power distribution validation functionality."""
        # Create mock power zone
        mock_zone = MagicMock()
        mock_zone.GetNetname.return_value = "PWR_3V3"
        mock_zone.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        self.mock_board.Zones.return_value = [mock_zone]
        self.mock_board.GetPads.return_value = []  # No connected pads
        
        # Run validation
        results = self.validator._validate_power_distribution(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, EnhancedValidationResult) and
            r.category == EnhancedValidationCategory.POWER_DISTRIBUTION and
            "Power plane" in r.message
            for r in results[pcbnew.GENERAL]
        ))
    
    def test_manufacturing_optimization_validation(self):
        """Test manufacturing optimization validation functionality."""
        # Create mock footprints with non-orthogonal orientation
        mock_footprint1 = MagicMock()
        mock_footprint1.GetReference.return_value = "U1"
        mock_footprint1.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_footprint1.GetOrientation.return_value = 45  # 45-degree rotation
        
        mock_footprint2 = MagicMock()
        mock_footprint2.GetReference.return_value = "U2"
        mock_footprint2.GetPosition.return_value = pcbnew.VECTOR2I(1500000, 1500000)
        mock_footprint2.GetOrientation.return_value = 0
        
        self.mock_board.GetFootprints.return_value = [mock_footprint1, mock_footprint2]
        
        # Run validation
        results = self.validator._validate_manufacturing_optimization(self.mock_board)
        
        # Verify results
        self.assertIn(pcbnew.GENERAL, results)
        self.assertTrue(any(
            isinstance(r, EnhancedValidationResult) and
            r.category == EnhancedValidationCategory.MANUFACTURING_OPTIMIZATION and
            "non-orthogonal orientation" in r.message
            for r in results[pcbnew.GENERAL]
        ))

if __name__ == '__main__':
    unittest.main() 