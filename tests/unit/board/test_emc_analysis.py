"""Unit tests for EMC analysis."""
import unittest
from unittest.mock import Mock, patch
import math
import pcbnew
from kicad_pcb_generator.core.board.emc_analysis import (
    EMCAnalyzer,
    EMCAnalysisConfig
)

class TestEMCAnalysisConfig(unittest.TestCase):
    """Test EMC analysis configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = EMCAnalysisConfig()
        
        # Signal integrity thresholds
        self.assertEqual(config.crosstalk_threshold, -40.0)
        self.assertEqual(config.reflection_threshold, 0.1)
        self.assertEqual(config.impedance_mismatch_threshold, 5.0)
        self.assertEqual(config.signal_quality_threshold, 0.8)
        
        # EMI/EMC thresholds
        self.assertEqual(config.radiated_emissions_limit, 40.0)
        self.assertEqual(config.conducted_emissions_limit, 30.0)
        self.assertEqual(config.susceptibility_limit, 50.0)
        self.assertEqual(config.compliance_margin, 10.0)
        
        # Analysis parameters
        self.assertEqual(config.frequency_range, (10e3, 1e9))
        self.assertEqual(config.frequency_points, 100)
        self.assertEqual(config.temperature, 25.0)
        
        # Stackup parameters
        self.assertEqual(config.dielectric_constant, 4.5)
        self.assertEqual(config.substrate_height, 0.035)
        self.assertEqual(config.copper_thickness, 0.035)
        self.assertEqual(config.copper_weight, 1.0)
        self.assertEqual(config.prepreg_thickness, 0.1)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = EMCAnalysisConfig(
            crosstalk_threshold=-50.0,
            reflection_threshold=0.2,
            impedance_mismatch_threshold=10.0,
            signal_quality_threshold=0.9,
            radiated_emissions_limit=50.0,
            conducted_emissions_limit=40.0,
            susceptibility_limit=60.0,
            compliance_margin=20.0,
            frequency_range=(1e3, 10e9),
            frequency_points=200,
            temperature=30.0,
            dielectric_constant=3.5,
            substrate_height=0.05,
            copper_thickness=0.05,
            copper_weight=2.0,
            prepreg_thickness=0.2
        )
        
        # Signal integrity thresholds
        self.assertEqual(config.crosstalk_threshold, -50.0)
        self.assertEqual(config.reflection_threshold, 0.2)
        self.assertEqual(config.impedance_mismatch_threshold, 10.0)
        self.assertEqual(config.signal_quality_threshold, 0.9)
        
        # EMI/EMC thresholds
        self.assertEqual(config.radiated_emissions_limit, 50.0)
        self.assertEqual(config.conducted_emissions_limit, 40.0)
        self.assertEqual(config.susceptibility_limit, 60.0)
        self.assertEqual(config.compliance_margin, 20.0)
        
        # Analysis parameters
        self.assertEqual(config.frequency_range, (1e3, 10e9))
        self.assertEqual(config.frequency_points, 200)
        self.assertEqual(config.temperature, 30.0)
        
        # Stackup parameters
        self.assertEqual(config.dielectric_constant, 3.5)
        self.assertEqual(config.substrate_height, 0.05)
        self.assertEqual(config.copper_thickness, 0.05)
        self.assertEqual(config.copper_weight, 2.0)
        self.assertEqual(config.prepreg_thickness, 0.2)

class TestEMCAnalyzer(unittest.TestCase):
    """Test EMC analyzer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = Mock(spec=pcbnew.BOARD)
        self.config = EMCAnalysisConfig()
        self.analyzer = EMCAnalyzer(self.board, self.config)
        
        # Mock board methods
        self.board.GetTracks.return_value = []
        self.board.GetNetsByName.return_value = {}
    
    def test_initialization(self):
        """Test analyzer initialization."""
        self.assertEqual(self.analyzer.board, self.board)
        self.assertEqual(self.analyzer.config, self.config)
        self.assertIsNotNone(self.analyzer.logger)
        self.assertIsNotNone(self.analyzer.audio_validator)
        self.assertIsNotNone(self.analyzer.safety_validator)
    
    @patch('pcbnew.VERSION', '9.0.0')
    def test_kicad_version_validation(self):
        """Test KiCad version validation."""
        analyzer = EMCAnalyzer(self.board)
        self.assertIsNotNone(analyzer)
    
    @patch('pcbnew.VERSION', '8.0.0')
    def test_invalid_kicad_version(self):
        """Test invalid KiCad version."""
        with self.assertRaises(RuntimeError):
            EMCAnalyzer(self.board)
    
    def test_analyze_emc(self):
        """Test comprehensive EMC analysis."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetNetname.return_value = 'SIGNAL1'
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Run analysis
        results = self.analyzer.analyze_emc()
        
        # Check results
        self.assertIn('signal_integrity', results)
        self.assertIn('emi_analysis', results)
        self.assertIn('safety_results', results)
        self.assertIn('audio_results', results)
    
    def test_analyze_signal_integrity(self):
        """Test signal integrity analysis."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetNetname.return_value = 'SIGNAL1'
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Run analysis
        results = self.analyzer.analyze_signal_integrity()
        
        # Check results
        self.assertIn('SIGNAL1', results.crosstalk)
        self.assertIn('SIGNAL1', results.reflections)
        self.assertIn('SIGNAL1', results.impedance_mismatch)
        self.assertIn('SIGNAL1', results.signal_quality)
    
    def test_analyze_emi(self):
        """Test EMI analysis."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetNetname.return_value = 'SIGNAL1'
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Run analysis
        results = self.analyzer.analyze_emi()
        
        # Check results
        self.assertIsInstance(results.radiated_emissions, dict)
        self.assertIsInstance(results.conducted_emissions, dict)
        self.assertIsInstance(results.susceptibility, dict)
        self.assertIsInstance(results.compliance_margin, float)
    
    def test_calculate_crosstalk(self):
        """Test crosstalk calculation."""
        # Mock tracks
        track1 = Mock(spec=pcbnew.TRACK)
        track1.GetType.return_value = pcbnew.PCB_TRACE_T
        track1.GetWidth.return_value = 0.2e6  # 0.2mm
        track1.GetStart.return_value = Mock(x=0, y=0)
        track1.GetEnd.return_value = Mock(x=10e6, y=0)
        
        track2 = Mock(spec=pcbnew.TRACK)
        track2.GetType.return_value = pcbnew.PCB_TRACE_T
        track2.GetWidth.return_value = 0.2e6  # 0.2mm
        track2.GetStart.return_value = Mock(x=0, y=1e6)
        track2.GetEnd.return_value = Mock(x=10e6, y=1e6)
        
        # Mock board
        self.board.GetTracks.return_value = [track1, track2]
        
        # Calculate crosstalk
        crosstalk = self.analyzer._calculate_crosstalk(track1)
        
        # Check result
        self.assertLess(crosstalk, 0)  # Should be negative dB
    
    def test_calculate_reflections(self):
        """Test reflection calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        
        # Calculate reflections
        reflections = self.analyzer._calculate_reflections(track)
        
        # Check result
        self.assertGreaterEqual(reflections, 0)
        self.assertLessEqual(reflections, 1)
    
    def test_calculate_impedance_mismatch(self):
        """Test impedance mismatch calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        
        # Calculate impedance mismatch
        mismatch = self.analyzer._calculate_impedance_mismatch(track)
        
        # Check result
        self.assertGreaterEqual(mismatch, 0)
    
    def test_calculate_signal_quality(self):
        """Test signal quality calculation."""
        # Calculate signal quality
        quality = self.analyzer._calculate_signal_quality(
            crosstalk=-40.0,
            reflections=0.1,
            impedance_mismatch=5.0
        )
        
        # Check result
        self.assertGreaterEqual(quality, 0)
        self.assertLessEqual(quality, 1)
    
    def test_calculate_radiated_emissions(self):
        """Test radiated emissions calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Calculate emissions
        emissions = self.analyzer._calculate_radiated_emissions(1e6)  # 1MHz
        
        # Check result
        self.assertIsInstance(emissions, float)
    
    def test_calculate_conducted_emissions(self):
        """Test conducted emissions calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Calculate emissions
        emissions = self.analyzer._calculate_conducted_emissions(1e6)  # 1MHz
        
        # Check result
        self.assertIsInstance(emissions, float)
    
    def test_calculate_susceptibility(self):
        """Test susceptibility calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        
        # Mock board
        self.board.GetTracks.return_value = [track]
        
        # Calculate susceptibility
        susceptibility = self.analyzer._calculate_susceptibility(1e6)  # 1MHz
        
        # Check result
        self.assertIsInstance(susceptibility, float)
    
    def test_calculate_compliance_margin(self):
        """Test compliance margin calculation."""
        # Calculate margin
        margin = self.analyzer._calculate_compliance_margin(
            radiated_emissions={1e6: 30.0},  # 1MHz
            conducted_emissions={1e6: 20.0}  # 1MHz
        )
        
        # Check result
        self.assertIsInstance(margin, float)
        self.assertGreaterEqual(margin, 0)
    
    def test_calculate_impedance(self):
        """Test impedance calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        
        # Calculate impedance
        impedance = self.analyzer._calculate_impedance(track)
        
        # Check result
        self.assertIsInstance(impedance, float)
        self.assertGreater(impedance, 0)
    
    def test_calculate_loop_area(self):
        """Test loop area calculation."""
        # Mock track
        track = Mock(spec=pcbnew.TRACK)
        track.GetType.return_value = pcbnew.PCB_TRACE_T
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetLength.return_value = 10e6  # 10mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        
        # Calculate loop area
        area = self.analyzer._calculate_loop_area(track)
        
        # Check result
        self.assertIsInstance(area, float)
        self.assertGreater(area, 0)
    
    def test_is_parallel(self):
        """Test parallel track detection."""
        # Mock tracks
        track1 = Mock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = Mock(x=0, y=0)
        track1.GetEnd.return_value = Mock(x=10e6, y=0)
        
        track2 = Mock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = Mock(x=0, y=1e6)
        track2.GetEnd.return_value = Mock(x=10e6, y=1e6)
        
        # Check if parallel
        is_parallel = self.analyzer._is_parallel(track1, track2)
        
        # Check result
        self.assertTrue(is_parallel)
    
    def test_calculate_min_distance(self):
        """Test minimum distance calculation."""
        # Mock tracks
        track1 = Mock(spec=pcbnew.TRACK)
        track1.GetStart.return_value = Mock(x=0, y=0)
        track1.GetEnd.return_value = Mock(x=10e6, y=0)
        
        track2 = Mock(spec=pcbnew.TRACK)
        track2.GetStart.return_value = Mock(x=0, y=1e6)
        track2.GetEnd.return_value = Mock(x=10e6, y=1e6)
        
        # Calculate minimum distance
        distance = self.analyzer._calculate_min_distance(track1, track2)
        
        # Check result
        self.assertIsInstance(distance, float)
        self.assertGreater(distance, 0)

if __name__ == '__main__':
    unittest.main() 