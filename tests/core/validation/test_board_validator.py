"""
Tests for the board validator module.
"""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew

from kicad_pcb_generator.core.validation.board_validator import BoardValidator, ValidationSeverity, ValidationIssue

class TestBoardValidator(unittest.TestCase):
    """Test cases for the BoardValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = BoardValidator()
        self.mock_board = MagicMock(spec=pcbnew.BOARD)
        self.validator.set_board(self.mock_board)
        
    def test_no_board_validation(self):
        """Test validation when no board is set."""
        validator = BoardValidator()
        issues = validator.validate_board()
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].severity, ValidationSeverity.ERROR)
        self.assertEqual(issues[0].message, "No board loaded for validation")
        
    def test_dimension_validation(self):
        """Test board dimension validation."""
        # Mock board edges
        mock_edges = MagicMock()
        mock_edges.GetWidth.return_value = 500000  # 0.5mm
        mock_edges.GetHeight.return_value = 500000  # 0.5mm
        self.mock_board.GetBoardEdgesBoundingBox.return_value = mock_edges
        
        issues = self.validator._validate_dimensions()
        self.assertTrue(any(issue.message == "Board dimensions are too small" for issue in issues))
        
    def test_component_validation(self):
        """Test component validation."""
        # Mock components
        mock_footprint1 = MagicMock()
        mock_footprint1.GetReference.return_value = "R1"
        mock_footprint1.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_footprint1.HitTest.return_value = False
        
        mock_footprint2 = MagicMock()
        mock_footprint2.GetReference.return_value = "R2"
        mock_footprint2.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_footprint2.HitTest.return_value = True
        
        self.mock_board.GetFootprints.return_value = [mock_footprint1, mock_footprint2]
        
        # Mock board edges
        mock_edges = MagicMock()
        mock_edges.Contains.return_value = True
        self.mock_board.GetBoardEdgesBoundingBox.return_value = mock_edges
        
        issues = self.validator._validate_components()
        self.assertTrue(any("overlaps" in issue.message for issue in issues))
        
    def test_track_validation(self):
        """Test track validation."""
        # Mock tracks
        mock_track = MagicMock()
        mock_track.GetWidth.return_value = 50000  # 0.05mm
        mock_track.GetLayer.return_value = pcbnew.F_Cu
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_track.HitTest.return_value = False
        
        self.mock_board.GetTracks.return_value = [mock_track]
        
        issues = self.validator._validate_tracks()
        self.assertTrue(any("Track width" in issue.message for issue in issues))
        
    def test_via_validation(self):
        """Test via validation."""
        # Mock vias
        mock_via = MagicMock()
        mock_via.GetDrill.return_value = 100000  # 0.1mm
        mock_via.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        self.mock_board.GetVias.return_value = [mock_via]
        
        issues = self.validator._validate_vias()
        self.assertTrue(any("Via drill size" in issue.message for issue in issues))
        
    def test_zone_validation(self):
        """Test zone validation."""
        # Mock zones
        mock_zone = MagicMock()
        mock_zone.GetNetname.return_value = "GND"
        mock_zone.GetLayer.return_value = pcbnew.F_Cu
        mock_zone.IsFilled.return_value = False
        
        self.mock_board.GetZones.return_value = [mock_zone]
        
        issues = self.validator._validate_zones()
        self.assertTrue(any("not filled" in issue.message for issue in issues))

if __name__ == '__main__':
    unittest.main() 