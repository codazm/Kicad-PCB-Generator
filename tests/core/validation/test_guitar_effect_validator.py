"""Tests for the guitar effect validator."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
from ....src.kicad_pcb_generator.core.validation.guitar_effect_validator import (
    GuitarEffectValidator,
    DistortionConfig,
    DelayConfig,
    ModulationConfig
)
from ....src.kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)

class TestGuitarEffectValidator(unittest.TestCase):
    """Test cases for the guitar effect validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = GuitarEffectValidator()
        self.board = MagicMock(spec=pcbnew.BOARD)
        self.validator.board = self.board

    @patch('pcbnew.GetBoard')
    def test_validate_distortion_circuit(self, mock_get_board):
        """Test distortion circuit validation."""
        # Mock board and components
        mock_get_board.return_value = self.board
        
        # Create mock effect component
        effect = MagicMock()
        effect.GetReference.return_value = "U1"
        
        # Create mock pads
        power_pad = MagicMock()
        power_pad.GetNetname.return_value = "VCC"
        power_pad.GetName.return_value = "VCC"
        
        input_pad = MagicMock()
        input_pad.GetNetname.return_value = "IN"
        input_pad.GetName.return_value = "IN"
        
        output_pad = MagicMock()
        output_pad.GetNetname.return_value = "OUT"
        output_pad.GetName.return_value = "OUT"
        
        bypass_pad = MagicMock()
        bypass_pad.GetNetname.return_value = "BYPASS"
        bypass_pad.GetName.return_value = "BYPASS"
        
        effect.Pads.return_value = [power_pad, input_pad, output_pad, bypass_pad]
        
        # Create mock tracks
        power_track = MagicMock()
        power_track.GetNetname.return_value = "VCC"
        power_track.GetWidth.return_value = 0.1e6  # 0.1mm
        power_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        input_track = MagicMock()
        input_track.GetNetname.return_value = "IN"
        input_track.GetWidth.return_value = 0.15e6  # 0.15mm
        input_track.GetStart.return_value = pcbnew.VECTOR2I(1000, 1000)
        
        output_track = MagicMock()
        output_track.GetNetname.return_value = "OUT"
        output_track.GetWidth.return_value = 0.15e6  # 0.15mm
        output_track.GetStart.return_value = pcbnew.VECTOR2I(2000, 2000)
        
        bypass_track = MagicMock()
        bypass_track.GetNetname.return_value = "BYPASS"
        bypass_track.GetWidth.return_value = 0.15e6  # 0.15mm
        bypass_track.GetStart.return_value = pcbnew.VECTOR2I(3000, 3000)
        
        # Create mock bypass capacitor
        bypass_cap = MagicMock()
        bypass_cap.GetReference.return_value = "C1"
        bypass_cap.GetPosition.return_value = pcbnew.VECTOR2I(3100, 3100)
        
        # Set up board mocks
        self.board.GetFootprints.return_value = [effect, bypass_cap]
        self.board.GetTracks.return_value = [power_track, input_track, output_track, bypass_track]
        
        # Run validation
        results = self.validator.validate_distortion_circuit("U1")
        
        # Verify results
        self.assertTrue(any(
            r.category == ValidationCategory.POWER and
            r.severity == ValidationSeverity.ERROR and
            "power track width" in r.message
            for r in results
        ))
        
        self.assertTrue(any(
            r.category == ValidationCategory.COMPONENT_PLACEMENT and
            r.severity == ValidationSeverity.ERROR and
            "Bypass capacitor too close" in r.message
            for r in results
        ))

    @patch('pcbnew.GetBoard')
    def test_validate_delay_circuit(self, mock_get_board):
        """Test delay circuit validation."""
        # Mock board and components
        mock_get_board.return_value = self.board
        
        # Create mock effect component
        effect = MagicMock()
        effect.GetReference.return_value = "U2"
        
        # Create mock pads
        power_pad = MagicMock()
        power_pad.GetNetname.return_value = "VCC"
        power_pad.GetName.return_value = "VCC"
        
        input_pad = MagicMock()
        input_pad.GetNetname.return_value = "IN"
        input_pad.GetName.return_value = "IN"
        
        output_pad = MagicMock()
        output_pad.GetNetname.return_value = "OUT"
        output_pad.GetName.return_value = "OUT"
        
        clock_pad = MagicMock()
        clock_pad.GetNetname.return_value = "CLK"
        clock_pad.GetName.return_value = "CLK"
        
        effect.Pads.return_value = [power_pad, input_pad, output_pad, clock_pad]
        
        # Create mock tracks
        power_track = MagicMock()
        power_track.GetNetname.return_value = "VCC"
        power_track.GetWidth.return_value = 0.1e6  # 0.1mm
        power_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        input_track = MagicMock()
        input_track.GetNetname.return_value = "IN"
        input_track.GetWidth.return_value = 0.15e6  # 0.15mm
        input_track.GetStart.return_value = pcbnew.VECTOR2I(1000, 1000)
        
        output_track = MagicMock()
        output_track.GetNetname.return_value = "OUT"
        output_track.GetWidth.return_value = 0.15e6  # 0.15mm
        output_track.GetStart.return_value = pcbnew.VECTOR2I(2000, 2000)
        
        clock_track = MagicMock()
        clock_track.GetNetname.return_value = "CLK"
        clock_track.GetWidth.return_value = 0.15e6  # 0.15mm
        clock_track.GetStart.return_value = pcbnew.VECTOR2I(3000, 3000)
        
        # Create mock clock capacitor
        clock_cap = MagicMock()
        clock_cap.GetReference.return_value = "C2"
        clock_cap.GetPosition.return_value = pcbnew.VECTOR2I(3100, 3100)
        
        # Set up board mocks
        self.board.GetFootprints.return_value = [effect, clock_cap]
        self.board.GetTracks.return_value = [power_track, input_track, output_track, clock_track]
        
        # Run validation
        results = self.validator.validate_delay_circuit("U2")
        
        # Verify results
        self.assertTrue(any(
            r.category == ValidationCategory.POWER and
            r.severity == ValidationSeverity.ERROR and
            "power track width" in r.message
            for r in results
        ))
        
        self.assertTrue(any(
            r.category == ValidationCategory.COMPONENT_PLACEMENT and
            r.severity == ValidationSeverity.ERROR and
            "Clock capacitor too close" in r.message
            for r in results
        ))

    def test_find_nearby_components(self):
        """Test finding nearby components."""
        # Create mock track
        track = MagicMock()
        track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        # Create mock components
        nearby_cap = MagicMock()
        nearby_cap.GetReference.return_value = "C1"
        nearby_cap.GetPosition.return_value = pcbnew.VECTOR2I(1000, 1000)  # 1mm away
        
        far_cap = MagicMock()
        far_cap.GetReference.return_value = "C2"
        far_cap.GetPosition.return_value = pcbnew.VECTOR2I(10000, 10000)  # 10mm away
        
        # Set up board mock
        self.board.GetFootprints.return_value = [nearby_cap, far_cap]
        
        # Run test
        nearby = self.validator._find_nearby_components(track, self.board, "C")
        
        # Verify results
        self.assertEqual(len(nearby), 1)
        self.assertEqual(nearby[0].GetReference(), "C1")

    def test_calculate_input_impedance(self):
        """Test calculating input impedance."""
        # Create mock resistor
        resistor = MagicMock()
        resistor.GetReference.return_value = "R1"
        resistor.GetValue.return_value = "10k"
        
        # Create mock pad
        pad = MagicMock()
        pad.GetNetname.return_value = "IN"
        
        resistor.Pads.return_value = [pad]
        
        # Set up board mock
        self.board.GetFootprints.return_value = [resistor]
        
        # Run test
        impedance = self.validator._calculate_input_impedance("IN", self.board)
        
        # Verify results
        self.assertEqual(impedance, 10000.0)  # 10k ohms

    def test_calculate_output_impedance(self):
        """Test calculating output impedance."""
        # Create mock resistor
        resistor = MagicMock()
        resistor.GetReference.return_value = "R2"
        resistor.GetValue.return_value = "1M"
        
        # Create mock pad
        pad = MagicMock()
        pad.GetNetname.return_value = "OUT"
        
        resistor.Pads.return_value = [pad]
        
        # Set up board mock
        self.board.GetFootprints.return_value = [resistor]
        
        # Run test
        impedance = self.validator._calculate_output_impedance("OUT", self.board)
        
        # Verify results
        self.assertEqual(impedance, 1000000.0)  # 1M ohms 