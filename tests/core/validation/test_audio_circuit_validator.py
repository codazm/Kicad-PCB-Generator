"""Tests for the audio circuit validator."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
from ....kicad_pcb_generator.core.validation.audio_circuit_validator import (
    AudioCircuitValidator,
    AudioCircuitType,
    DifferentialPairConfig,
    OpAmpConfig
)
from ....kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)

class TestAudioCircuitValidator(unittest.TestCase):
    """Test cases for the audio circuit validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = AudioCircuitValidator()
        self.board = MagicMock(spec=pcbnew.BOARD)
        self.validator.board = self.board

    @patch('pcbnew.GetBoard')
    def test_validate_differential_pair(self, mock_get_board):
        """Test differential pair validation."""
        # Mock board and tracks
        mock_get_board.return_value = self.board
        
        # Create mock tracks
        track_p = MagicMock(spec=pcbnew.TRACK)
        track_p.GetNetname.return_value = "NET_P"
        track_p.GetWidth.return_value = 200000  # 0.2mm
        track_p.GetLength.return_value = 1000000  # 1mm
        track_p.GetStart.return_value = pcbnew.VECTOR2I(0, 0)
        track_p.GetLayer.return_value = 0

        track_n = MagicMock(spec=pcbnew.TRACK)
        track_n.GetNetname.return_value = "NET_N"
        track_n.GetWidth.return_value = 200000  # 0.2mm
        track_n.GetLength.return_value = 1000000  # 1mm
        track_n.GetStart.return_value = pcbnew.VECTOR2I(100000, 0)  # 0.1mm spacing
        track_n.GetLayer.return_value = 0

        self.board.GetTracks.return_value = [track_p, track_n]

        # Test valid differential pair
        results = self.validator.validate_differential_pair("NET_P", "NET_N")
        self.assertEqual(len(results), 0)

        # Test invalid spacing
        track_n.GetStart.return_value = pcbnew.VECTOR2I(50000, 0)  # 0.05mm spacing
        results = self.validator.validate_differential_pair("NET_P", "NET_N")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, ValidationSeverity.ERROR)
        self.assertIn("spacing", results[0].message.lower())

        # Test length mismatch
        track_n.GetLength.return_value = 1500000  # 1.5mm
        results = self.validator.validate_differential_pair("NET_P", "NET_N")
        self.assertEqual(len(results), 2)
        self.assertTrue(any("length mismatch" in r.message.lower() for r in results))

        # Test width mismatch
        track_n.GetWidth.return_value = 250000  # 0.25mm
        results = self.validator.validate_differential_pair("NET_P", "NET_N")
        self.assertEqual(len(results), 3)
        self.assertTrue(any("width mismatch" in r.message.lower() for r in results))

    @patch('pcbnew.GetBoard')
    def test_validate_opamp_circuit(self, mock_get_board):
        """Test op-amp circuit validation."""
        # Mock board and components
        mock_get_board.return_value = self.board
        
        # Create mock op-amp
        opamp = MagicMock(spec=pcbnew.FOOTPRINT)
        opamp.GetReference.return_value = "U1"
        opamp.GetPosition.return_value = pcbnew.VECTOR2I(0, 0)

        # Create mock pads
        pad_vcc = MagicMock(spec=pcbnew.PAD)
        pad_vcc.GetName.return_value = "VCC"
        pad_vcc.GetNetname.return_value = "VCC"

        pad_gnd = MagicMock(spec=pcbnew.PAD)
        pad_gnd.GetName.return_value = "GND"
        pad_gnd.GetNetname.return_value = "GND"

        pad_in = MagicMock(spec=pcbnew.PAD)
        pad_in.GetName.return_value = "IN+"
        pad_in.GetNetname.return_value = "IN"

        pad_out = MagicMock(spec=pcbnew.PAD)
        pad_out.GetName.return_value = "OUT"
        pad_out.GetNetname.return_value = "OUT"

        pad_fb = MagicMock(spec=pcbnew.PAD)
        pad_fb.GetName.return_value = "FB"
        pad_fb.GetNetname.return_value = "FB"

        opamp.Pads.return_value = [pad_vcc, pad_gnd, pad_in, pad_out, pad_fb]

        # Create mock tracks
        track_vcc = MagicMock(spec=pcbnew.TRACK)
        track_vcc.GetNetname.return_value = "VCC"
        track_vcc.GetWidth.return_value = 150000  # 0.15mm
        track_vcc.GetStart.return_value = pcbnew.VECTOR2I(0, 0)

        track_in = MagicMock(spec=pcbnew.TRACK)
        track_in.GetNetname.return_value = "IN"
        track_in.GetWidth.return_value = 100000  # 0.1mm
        track_in.GetStart.return_value = pcbnew.VECTOR2I(0, 0)

        # Create mock components
        cap = MagicMock(spec=pcbnew.FOOTPRINT)
        cap.GetValue.return_value = "C1"
        cap.GetPosition.return_value = pcbnew.VECTOR2I(50000, 0)  # 0.5mm away

        res_in = MagicMock(spec=pcbnew.FOOTPRINT)
        res_in.GetValue.return_value = "R1"
        res_in.GetNetname.return_value = "IN"

        res_out = MagicMock(spec=pcbnew.FOOTPRINT)
        res_out.GetValue.return_value = "R2"
        res_out.GetNetname.return_value = "OUT"

        res_fb = MagicMock(spec=pcbnew.FOOTPRINT)
        res_fb.GetValue.return_value = "R3"
        res_fb.GetNetname.return_value = "FB"

        self.board.GetFootprints.return_value = [opamp, cap, res_in, res_out, res_fb]
        self.board.GetTracks.return_value = [track_vcc, track_in]

        # Test valid op-amp circuit
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 0)

        # Test missing decoupling capacitor
        cap.GetPosition.return_value = pcbnew.VECTOR2I(2000000, 0)  # 2mm away
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, ValidationSeverity.WARNING)
        self.assertIn("decoupling", results[0].message.lower())

        # Test power track width
        track_vcc.GetWidth.return_value = 100000  # 0.1mm
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 2)
        self.assertTrue(any("power track width" in r.message.lower() for r in results))

        # Test input impedance
        res_in.GetValue.return_value = "R1M"  # 1M ohm
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 3)
        self.assertTrue(any("input impedance" in r.message.lower() for r in results))

        # Test output impedance
        res_out.GetValue.return_value = "R50"  # 50 ohm
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 4)
        self.assertTrue(any("output impedance" in r.message.lower() for r in results))

        # Test feedback resistance
        res_fb.GetValue.return_value = "R500"  # 500 ohm
        results = self.validator.validate_opamp_circuit("U1")
        self.assertEqual(len(results), 5)
        self.assertTrue(any("feedback resistance" in r.message.lower() for r in results))

if __name__ == '__main__':
    unittest.main() 