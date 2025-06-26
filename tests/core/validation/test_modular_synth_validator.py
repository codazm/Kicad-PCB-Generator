"""Tests for the modular synth validator."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
from ....src.kicad_pcb_generator.core.validation.modular_synth_validator import (
    ModularSynthValidator,
    VCOConfig,
    VCFConfig,
    VCAConfig
)
from ....src.kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)

class TestModularSynthValidator(unittest.TestCase):
    """Test cases for the modular synth validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = ModularSynthValidator()
        self.board = MagicMock(spec=pcbnew.BOARD)
        self.validator.board = self.board

    @patch('pcbnew.GetBoard')
    def test_validate_vco_circuit(self, mock_get_board):
        """Test VCO circuit validation."""
        # Mock board and components
        mock_get_board.return_value = self.board
        
        # Create mock VCO component
        vco = MagicMock()
        vco.GetReference.return_value = "U1"
        
        # Create mock pads
        power_pad = MagicMock()
        power_pad.GetNetname.return_value = "VCC"
        power_pad.GetName.return_value = "VCC"
        
        control_pad = MagicMock()
        control_pad.GetNetname.return_value = "CV"
        control_pad.GetName.return_value = "CV"
        
        output_pad = MagicMock()
        output_pad.GetNetname.return_value = "OUT"
        output_pad.GetName.return_value = "OUT"
        
        timing_pad = MagicMock()
        timing_pad.GetNetname.return_value = "OSC"
        timing_pad.GetName.return_value = "OSC"
        
        vco.Pads.return_value = [power_pad, control_pad, output_pad, timing_pad]
        
        # Create mock tracks
        power_track = MagicMock()
        power_track.GetNetname.return_value = "VCC"
        power_track.GetWidth.return_value = 0.1e6  # 0.1mm
        power_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        control_track = MagicMock()
        control_track.GetNetname.return_value = "CV"
        control_track.GetWidth.return_value = 0.15e6  # 0.15mm
        control_track.GetStart.return_value = pcbnew.VECTOR2I(1000, 1000)
        
        output_track = MagicMock()
        output_track.GetNetname.return_value = "OUT"
        output_track.GetWidth.return_value = 0.15e6  # 0.15mm
        output_track.GetStart.return_value = pcbnew.VECTOR2I(2000, 2000)
        
        timing_track = MagicMock()
        timing_track.GetNetname.return_value = "OSC"
        timing_track.GetWidth.return_value = 0.15e6  # 0.15mm
        timing_track.GetStart.return_value = pcbnew.VECTOR2I(3000, 3000)
        
        # Create mock timing capacitor
        timing_cap = MagicMock()
        timing_cap.GetReference.return_value = "C1"
        timing_cap.GetPosition.return_value = pcbnew.VECTOR2I(3100, 3100)
        
        # Set up board mocks
        self.board.GetFootprints.return_value = [vco, timing_cap]
        self.board.GetTracks.return_value = [power_track, control_track, output_track, timing_track]
        
        # Run validation
        results = self.validator.validate_vco_circuit("U1")
        
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
            "Timing capacitor too close" in r.message
            for r in results
        ))

    @patch('pcbnew.GetBoard')
    def test_validate_vcf_circuit(self, mock_get_board):
        """Test VCF circuit validation."""
        # Mock board and components
        mock_get_board.return_value = self.board
        
        # Create mock VCF component
        vcf = MagicMock()
        vcf.GetReference.return_value = "U2"
        
        # Create mock pads
        power_pad = MagicMock()
        power_pad.GetNetname.return_value = "VCC"
        power_pad.GetName.return_value = "VCC"
        
        control_pad = MagicMock()
        control_pad.GetNetname.return_value = "CV"
        control_pad.GetName.return_value = "CV"
        
        input_pad = MagicMock()
        input_pad.GetNetname.return_value = "IN"
        input_pad.GetName.return_value = "IN"
        
        output_pad = MagicMock()
        output_pad.GetNetname.return_value = "OUT"
        output_pad.GetName.return_value = "OUT"
        
        filter_pad = MagicMock()
        filter_pad.GetNetname.return_value = "FILTER"
        filter_pad.GetName.return_value = "FILTER"
        
        vcf.Pads.return_value = [power_pad, control_pad, input_pad, output_pad, filter_pad]
        
        # Create mock tracks
        power_track = MagicMock()
        power_track.GetNetname.return_value = "VCC"
        power_track.GetWidth.return_value = 0.1e6  # 0.1mm
        power_track.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        
        control_track = MagicMock()
        control_track.GetNetname.return_value = "CV"
        control_track.GetWidth.return_value = 0.15e6  # 0.15mm
        control_track.GetStart.return_value = pcbnew.VECTOR2I(1000, 1000)
        
        input_track = MagicMock()
        input_track.GetNetname.return_value = "IN"
        input_track.GetWidth.return_value = 0.15e6  # 0.15mm
        input_track.GetStart.return_value = pcbnew.VECTOR2I(2000, 2000)
        
        output_track = MagicMock()
        output_track.GetNetname.return_value = "OUT"
        output_track.GetWidth.return_value = 0.15e6  # 0.15mm
        output_track.GetStart.return_value = pcbnew.VECTOR2I(3000, 3000)
        
        filter_track = MagicMock()
        filter_track.GetNetname.return_value = "FILTER"
        filter_track.GetWidth.return_value = 0.15e6  # 0.15mm
        filter_track.GetStart.return_value = pcbnew.VECTOR2I(4000, 4000)
        
        # Create mock filter components
        filter_cap = MagicMock()
        filter_cap.GetReference.return_value = "C2"
        filter_cap.GetPosition.return_value = pcbnew.VECTOR2I(4100, 4100)
        
        filter_res = MagicMock()
        filter_res.GetReference.return_value = "R1"
        filter_res.GetPosition.return_value = pcbnew.VECTOR2I(4200, 4200)
        
        # Set up board mocks
        self.board.GetFootprints.return_value = [vcf, filter_cap, filter_res]
        self.board.GetTracks.return_value = [power_track, control_track, input_track, output_track, filter_track]
        
        # Run validation
        results = self.validator.validate_vcf_circuit("U2")
        
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
            "Filter capacitor too close" in r.message
            for r in results
        ))
        
        self.assertTrue(any(
            r.category == ValidationCategory.COMPONENT_PLACEMENT and
            r.severity == ValidationSeverity.ERROR and
            "Filter resistor too close" in r.message
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
        pad.GetNetname.return_value = "CV"
        
        resistor.Pads.return_value = [pad]
        
        # Set up board mock
        self.board.GetFootprints.return_value = [resistor]
        
        # Run test
        impedance = self.validator._calculate_input_impedance("CV", self.board)
        
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