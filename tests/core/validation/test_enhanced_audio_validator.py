"""Unit tests for enhanced audio validation features."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
import math
from kicad_pcb_generator.audio.validation.audio_validator import AudioPCBValidator
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory, ValidationSeverity
from kicad_pcb_generator.utils.config.settings import Settings
from kicad_pcb_generator.utils.logging.logger import Logger

class TestEnhancedAudioValidator(unittest.TestCase):
    """Test suite for enhanced audio validation features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.logger = Logger(__name__)
        self.validator = AudioPCBValidator(settings=self.settings, logger=self.logger)
        self.board = MagicMock(spec=pcbnew.BOARD)
        
        # Set up default board properties
        self.board.GetBoardEdgesBoundingBox.return_value = MagicMock(
            GetWidth=lambda: 100e6,  # 100mm
            GetHeight=lambda: 100e6,  # 100mm
            GetLeft=lambda: 0,
            GetRight=lambda: 100e6,
            GetTop=lambda: 0,
            GetBottom=lambda: 100e6
        )
        
        # Set up default copper thickness
        self.board.GetCopperThickness.return_value = 35e-6  # 35μm
        
        # Set up default board thickness
        self.board.GetBoardThickness.return_value = 1.6e6  # 1.6mm
    
    def test_impedance_calculation(self):
        """Test track impedance calculation."""
        # Create mock track
        track = MagicMock(spec=pcbnew.TRACK)
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLayer.return_value = pcbnew.F_Cu
        
        # Calculate impedance
        impedance = self.validator._calculate_track_impedance(track, self.board)
        
        # Verify impedance is within expected range (typically 50-100Ω for audio)
        self.assertIsNotNone(impedance)
        self.assertGreater(impedance, 0)
        self.assertLess(impedance, 200)  # Should be well below 200Ω
    
    def test_parallel_track_detection(self):
        """Test parallel track detection."""
        # Create mock tracks
        track1 = MagicMock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=10e6, y=0)  # 10mm horizontal
        track1.GetLayer.return_value = pcbnew.F_Cu
        
        track2 = MagicMock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = MagicMock(x=0, y=1e6)
        track2.GetEnd.return_value = MagicMock(x=10e6, y=1e6)  # 10mm horizontal, 1mm above
        track2.GetLayer.return_value = pcbnew.F_Cu
        
        self.board.GetTracks.return_value = [track1, track2]
        
        # Find parallel tracks
        parallel_tracks = self.validator._find_parallel_tracks(track1, self.board)
        
        # Verify parallel track detection
        self.assertEqual(len(parallel_tracks), 1)
        self.assertEqual(parallel_tracks[0], track2)
    
    def test_crosstalk_calculation(self):
        """Test crosstalk calculation between parallel tracks."""
        # Create mock tracks
        track1 = MagicMock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=10e6, y=0)
        
        track2 = MagicMock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = MagicMock(x=0, y=0.2e6)  # 0.2mm away
        track2.GetEnd.return_value = MagicMock(x=10e6, y=0.2e6)
        
        # Calculate crosstalk
        crosstalk = self.validator._calculate_crosstalk(track1, [track2])
        
        # Verify crosstalk is within expected range (0-1)
        self.assertGreaterEqual(crosstalk, 0)
        self.assertLessEqual(crosstalk, 1)
    
    def test_ground_plane_coverage(self):
        """Test ground plane coverage calculation."""
        # Create mock ground zone
        zone = MagicMock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetArea.return_value = 5000e6  # 5000mm²
        
        self.board.GetZones.return_value = [zone]
        
        # Calculate ground area
        ground_area = self.validator._calculate_ground_area(self.board)
        
        # Verify ground area calculation
        self.assertEqual(ground_area, 5000)  # Should be 5000mm²
    
    def test_star_ground_verification(self):
        """Test star ground topology verification."""
        # Create mock ground tracks forming a star topology
        track1 = MagicMock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = MagicMock(x=50e6, y=50e6)  # Center point
        track1.GetEnd.return_value = MagicMock(x=60e6, y=50e6)
        
        track2 = MagicMock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = MagicMock(x=50e6, y=50e6)  # Center point
        track2.GetEnd.return_value = MagicMock(x=50e6, y=60e6)
        
        track3 = MagicMock(spec=pcbnew.TRACK)
        track3.GetStart.return_value = MagicMock(x=50e6, y=50e6)  # Center point
        track3.GetEnd.return_value = MagicMock(x=40e6, y=50e6)
        
        # Create mock ground net
        ground_net = MagicMock()
        ground_net.GetName.return_value = "GND"
        
        self.board.GetNets.return_value = [ground_net]
        self.board.GetTracks.return_value = [track1, track2, track3]
        
        # Verify star ground topology
        is_star_ground = self.validator._verify_star_ground(self.board)
        self.assertTrue(is_star_ground)
    
    def test_ground_loop_detection(self):
        """Test ground loop detection."""
        # Create mock ground tracks forming a loop
        track1 = MagicMock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = MagicMock(x=0, y=0)
        track1.GetEnd.return_value = MagicMock(x=10e6, y=0)
        
        track2 = MagicMock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = MagicMock(x=10e6, y=0)
        track2.GetEnd.return_value = MagicMock(x=10e6, y=10e6)
        
        track3 = MagicMock(spec=pcbnew.TRACK)
        track3.GetStart.return_value = MagicMock(x=10e6, y=10e6)
        track3.GetEnd.return_value = MagicMock(x=0, y=10e6)
        
        track4 = MagicMock(spec=pcbnew.TRACK)
        track4.GetStart.return_value = MagicMock(x=0, y=10e6)
        track4.GetEnd.return_value = MagicMock(x=0, y=0)
        
        # Create mock ground net
        ground_net = MagicMock()
        ground_net.GetName.return_value = "GND"
        
        self.board.GetNets.return_value = [ground_net]
        self.board.GetTracks.return_value = [track1, track2, track3, track4]
        
        # Detect ground loops
        ground_loops = self.validator._detect_ground_loops(self.board)
        
        # Verify ground loop detection
        self.assertGreater(len(ground_loops), 0)
    
    def test_signal_integrity_validation(self):
        """Test signal integrity validation."""
        # Create mock audio signal track
        track = MagicMock(spec=pcbnew.TRACK)
        track.GetNetname.return_value = "AUDIO_SIG"
        track.GetWidth.return_value = 0.15e6  # 0.15mm (below minimum)
        track.GetStart.return_value = MagicMock(x=0, y=0)
        track.GetEnd.return_value = MagicMock(x=10e6, y=0)
        track.GetLayer.return_value = pcbnew.F_Cu
        
        self.board.GetTracks.return_value = [track]
        
        # Run signal integrity validation
        results = self.validator._validate_signal_integrity(self.board)
        
        # Verify validation results
        self.assertIn(ValidationCategory.SIGNAL, results)
        signal_results = results[ValidationCategory.SIGNAL]
        
        # Should have warnings for:
        # 1. Track width too small
        # 2. Impedance mismatch
        self.assertGreaterEqual(len(signal_results), 1)
        
        # Verify track width warning
        width_warnings = [r for r in signal_results if "width" in r.message.lower()]
        self.assertGreaterEqual(len(width_warnings), 1)
    
    def test_grounding_validation(self):
        """Test grounding validation."""
        # Create mock ground zone with low coverage
        zone = MagicMock(spec=pcbnew.ZONE)
        zone.GetNetname.return_value = "GND"
        zone.GetArea.return_value = 2000e6  # 2000mm² (20% coverage)
        
        self.board.GetZones.return_value = [zone]
        
        # Run grounding validation
        results = self.validator._validate_grounding(self.board)
        
        # Verify validation results
        self.assertIn(ValidationCategory.GROUND, results)
        ground_results = results[ValidationCategory.GROUND]
        
        # Should have warnings for:
        # 1. Low ground plane coverage
        # 2. Missing star ground topology
        self.assertGreaterEqual(len(ground_results), 1)
        
        # Verify ground plane coverage warning
        coverage_warnings = [r for r in ground_results if "coverage" in r.message.lower()]
        self.assertGreaterEqual(len(coverage_warnings), 1)
    
    def test_validation_integration(self):
        """Test integration of all validation features."""
        # Create mock board with various issues
        # 1. Audio signal track with width issues
        audio_track = MagicMock(spec=pcbnew.TRACK)
        audio_track.GetNetname.return_value = "AUDIO_SIG"
        audio_track.GetWidth.return_value = 0.15e6  # 0.15mm (below minimum)
        audio_track.GetStart.return_value = MagicMock(x=0, y=0)
        audio_track.GetEnd.return_value = MagicMock(x=10e6, y=0)
        
        # 2. Ground zone with low coverage
        ground_zone = MagicMock(spec=pcbnew.ZONE)
        ground_zone.GetNetname.return_value = "GND"
        ground_zone.GetArea.return_value = 2000e6  # 2000mm² (20% coverage)
        
        self.board.GetTracks.return_value = [audio_track]
        self.board.GetZones.return_value = [ground_zone]
        
        # Run full validation
        results = self.validator.validate(self.board)
        
        # Verify all validation categories are present
        categories = {result.category for result in results}
        self.assertIn(ValidationCategory.SIGNAL, categories)
        self.assertIn(ValidationCategory.GROUND, categories)
        
        # Verify validation results
        signal_results = [r for r in results if r.category == ValidationCategory.SIGNAL]
        ground_results = [r for r in results if r.category == ValidationCategory.GROUND]
        
        self.assertGreater(len(signal_results), 0)
        self.assertGreater(len(ground_results), 0) 