class TestBaseValidator(unittest.TestCase):
    """Test base validator functionality."""

    def setUp(self):
        """Set up test environment."""
        self.validator = BaseValidator()

    def test_signal_validation(self):
        """Test signal validation functionality."""
        # Create mock board
        board = MagicMock(spec=pcbnew.BOARD)
        
        # Create mock tracks
        track1 = MagicMock(spec=pcbnew.TRACK)
        track1.IsTrack.return_value = True
        track1.GetNetname.return_value = "CLK1"
        track1.GetWidth.return_value = 0.15e6  # 0.15mm (below minimum)
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=10e6, y=0)
        track1.GetLayer.return_value = pcbnew.F_Cu
        
        track2 = MagicMock(spec=pcbnew.TRACK)
        track2.IsTrack.return_value = True
        track2.GetNetname.return_value = "AUDIO_SIG"
        track2.GetWidth.return_value = 0.25e6  # 0.25mm (valid)
        track2.GetStart.return_value = MagicMock(x=0, y=0)
        track2.GetEnd.return_value = MagicMock(x=10e6, y=0)
        track2.GetLayer.return_value = pcbnew.F_Cu
        
        # Create mock ground zone
        ground_zone = MagicMock(spec=pcbnew.ZONE)
        ground_zone.GetNetname.return_value = "GND"
        ground_zone.IsOnLayer.return_value = True
        
        # Set up board mocks
        board.GetTracks.return_value = [track1, track2]
        board.Zones.return_value = [ground_zone]
        board.GetCopperLayerThickness.return_value = 0.035e6  # 35um
        board.GetBoardThickness.return_value = 1.6e6  # 1.6mm
        
        # Run validation
        results = self.validator._validate_signal()
        
        # Verify results
        self.assertGreater(len(results), 0)
        
        # Check for high-speed signal width warning
        width_warnings = [r for r in results if "width" in r.message.lower() and "CLK1" in r.message]
        self.assertEqual(len(width_warnings), 1)
        self.assertEqual(width_warnings[0].severity, ValidationSeverity.ERROR)
        
        # Check for impedance calculation
        impedance_results = [r for r in results if "impedance" in r.message.lower()]
        self.assertGreater(len(impedance_results), 0)
        
        # Check for ground plane reference
        ground_ref_results = [r for r in results if "ground plane" in r.message.lower()]
        self.assertEqual(len(ground_ref_results), 0)  # Should have ground reference
        
        # Test parallel tracks
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=10e6, y=0)
        track2.GetStart.return_value = MagicMock(x=0, y=0.5e6)
        track2.GetEnd.return_value = MagicMock(x=10e6, y=0.5e6)
        
        results = self.validator._validate_signal()
        parallel_warnings = [r for r in results if "parallel" in r.message.lower()]
        self.assertGreater(len(parallel_warnings), 0)
        
        # Test crosstalk calculation
        crosstalk_results = [r for r in results if "crosstalk" in r.message.lower()]
        self.assertGreater(len(crosstalk_results), 0)
        
        # Test reflection calculation
        reflection_results = [r for r in results if "reflection" in r.message.lower()]
        self.assertGreater(len(reflection_results), 0)
        
        # Test termination check
        track1.GetNetname.return_value = "DDR_CLK"
        results = self.validator._validate_signal()
        termination_warnings = [r for r in results if "termination" in r.message.lower()]
        self.assertGreater(len(termination_warnings), 0)
        
        # Test error handling
        board.GetTracks.side_effect = Exception("Test error")
        results = self.validator._validate_signal()
        error_results = [r for r in results if r.severity == ValidationSeverity.ERROR]
        self.assertEqual(len(error_results), 1)
        self.assertIn("Error validating signal integrity", error_results[0].message) 