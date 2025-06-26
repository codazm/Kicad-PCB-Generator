"""Unit tests for RealTimeValidator."""
import unittest
from unittest.mock import MagicMock, patch
import pcbnew
import time
import threading
from kicad_pcb_generator.validation.real_time_validator import (
    RealTimeValidator,
    ValidationType,
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)
from kicad_pcb_generator.utils.config.settings import Settings
from kicad_pcb_generator.utils.logging.logger import Logger

class TestRealTimeValidator(unittest.TestCase):
    """Test cases for the RealTimeValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.settings = Settings()
        self.logger = Logger(__name__)
        self.validator = RealTimeValidator(settings=self.settings, logger=self.logger)
        self.mock_board = MagicMock(spec=pcbnew.BOARD)
        
        # Mock board methods
        self.mock_board.GetFootprints.return_value = []
        self.mock_board.GetTracks.return_value = []
        self.mock_board.GetVias.return_value = []
        self.mock_board.Zones.return_value = []
        self.mock_board.GetPads.return_value = []
        self.mock_board.GetLayerName.return_value = "Test Layer"
        
        # Mock pcbnew.GetBoard
        self.pcbnew_patch = patch('pcbnew.GetBoard', return_value=self.mock_board)
        self.mock_get_board = self.pcbnew_patch.start()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.pcbnew_patch.stop()
        if self.validator._validation_thread and self.validator._validation_thread.is_alive():
            self.validator.stop_validation()
    
    def test_initialization(self):
        """Test validator initialization."""
        self.assertIsNotNone(self.validator)
        self.assertEqual(self.validator._validation_interval, 1.0)
        self.assertFalse(self.validator._stop_validation)
        self.assertIsNone(self.validator._validation_thread)
        self.assertIsNone(self.validator._callback)
    
    def test_start_stop_validation(self):
        """Test starting and stopping validation."""
        # Start validation
        self.validator.start_validation()
        self.assertIsNotNone(self.validator._validation_thread)
        self.assertTrue(self.validator._validation_thread.is_alive())
        
        # Stop validation
        self.validator.stop_validation()
        self.assertFalse(self.validator._validation_thread.is_alive())
    
    def test_callback_functionality(self):
        """Test callback functionality."""
        callback_results = []
        def callback(results):
            callback_results.extend(results)
        
        self.validator.set_callback(callback)
        self.assertEqual(self.validator._callback, callback)
        
        # Create mock validation results
        mock_results = [
            ValidationResult(
                category=ValidationCategory.DESIGN_RULES,
                message="Test error",
                severity=ValidationSeverity.ERROR
            )
        ]
        
        # Simulate validation
        self.validator._callback(mock_results)
        self.assertEqual(callback_results, mock_results)
    
    def test_validation_interval(self):
        """Test validation interval timing."""
        self.validator._validation_interval = 0.1  # 100ms for faster testing
        
        # Start validation
        self.validator.start_validation()
        time.sleep(0.2)  # Wait for two intervals
        
        # Check that validation was performed
        self.assertGreater(self.validator._last_validation_time, 0)
    
    def test_board_change_detection(self):
        """Test board change detection."""
        # Mock board state
        initial_state = {
            'footprints': [],
            'tracks': [],
            'vias': []
        }
        self.validator._last_board_state = initial_state
        
        # Simulate board change
        self.mock_board.GetFootprints.return_value = [MagicMock()]
        self.assertTrue(self.validator._has_board_changed())
    
    def test_validation_rules(self):
        """Test validation rules."""
        # Enable all rules
        for rule_type in ValidationType:
            self.validator.enable_rule(rule_type.value)
        
        # Create mock components and tracks
        mock_footprint = MagicMock()
        mock_footprint.GetReference.return_value = "R1"
        mock_footprint.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        mock_track = MagicMock()
        mock_track.GetClass.return_value = 'TRACK'
        mock_track.GetWidth.return_value = 50000  # 0.05mm
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_track.GetEnd.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        
        self.mock_board.GetFootprints.return_value = [mock_footprint]
        self.mock_board.GetTracks.return_value = [mock_track]
        
        # Run validation
        results = self.validator.validate()
        
        # Check results
        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, ValidationResult) for result in results))
    
    def test_error_handling(self):
        """Test error handling during validation."""
        # Simulate an error during validation
        self.mock_board.GetFootprints.side_effect = Exception("Test error")
        
        # Run validation
        results = self.validator.validate()
        
        # Check that error was caught and reported
        self.assertTrue(any(
            result.severity == ValidationSeverity.ERROR and
            "Test error" in result.message
            for result in results
        ))
    
    def test_validation_categories(self):
        """Test validation categories."""
        # Enable specific categories
        self.validator.enable_rule(ValidationType.DESIGN_RULES.value)
        self.validator.enable_rule(ValidationType.COMPONENT_PLACEMENT.value)
        
        # Run validation
        results = self.validator.validate()
        
        # Check that only enabled categories were validated
        categories = {result.category for result in results}
        self.assertIn(ValidationCategory.DESIGN_RULES, categories)
        self.assertIn(ValidationCategory.COMPONENT_PLACEMENT, categories)
    
    def test_concurrent_validation(self):
        """Test concurrent validation requests."""
        # Start validation
        self.validator.start_validation()
        
        # Try to start validation again
        self.validator.start_validation()
        
        # Check that only one thread is running
        self.assertEqual(threading.active_count(), 2)  # Main thread + validation thread
        
        # Stop validation
        self.validator.stop_validation()
    
    def test_validation_cache(self):
        """Test validation result caching."""
        # Run validation
        results1 = self.validator.validate()
        
        # Run validation again without changes
        results2 = self.validator.validate()
        
        # Check that results were cached
        self.assertEqual(results1, results2)
        
        # Simulate board change
        self.mock_board.GetFootprints.return_value = [MagicMock()]
        
        # Run validation again
        results3 = self.validator.validate()
        
        # Check that results were updated
        self.assertNotEqual(results1, results3)
    
    def test_board_state_tracking(self):
        """Test board state tracking functionality."""
        # Mock board state
        mock_board = MagicMock()
        
        # Mock components
        mock_footprint1 = MagicMock()
        mock_footprint1.GetReference.return_value = "R1"
        mock_footprint1.GetPosition.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        
        mock_footprint2 = MagicMock()
        mock_footprint2.GetReference.return_value = "R2"
        mock_footprint2.GetPosition.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        
        mock_board.GetFootprints.return_value = [mock_footprint1, mock_footprint2]
        
        # Mock tracks
        mock_track = MagicMock()
        mock_track.IsTrack.return_value = True
        mock_track.GetNetname.return_value = "Net1"
        mock_track.GetLayer.return_value = pcbnew.F_Cu
        mock_track.GetWidth.return_value = 100000
        mock_track.GetStart.return_value = pcbnew.VECTOR2I(1000000, 1000000)
        mock_track.GetEnd.return_value = pcbnew.VECTOR2I(2000000, 2000000)
        
        mock_board.GetTracks.return_value = [mock_track]
        
        # Mock vias
        mock_via = MagicMock()
        mock_via.GetNetname.return_value = "Net1"
        mock_via.GetPosition.return_value = pcbnew.VECTOR2I(1500000, 1500000)
        mock_via.GetWidth.return_value = 200000
        mock_via.GetDrill.return_value = 100000
        
        mock_board.GetVias.return_value = [mock_via]
        
        # Mock zones
        mock_zone = MagicMock()
        mock_zone.GetNetname.return_value = "GND"
        mock_zone.GetLayer.return_value = pcbnew.F_Cu
        mock_zone.GetArea.return_value = 1000000
        
        mock_board.Zones.return_value = [mock_zone]
        
        # Mock board edges
        mock_box = MagicMock()
        mock_box.GetWidth.return_value = 100000000
        mock_box.GetHeight.return_value = 100000000
        mock_board.GetBoardEdgesBoundingBox.return_value = mock_box
        
        # Mock design settings
        mock_settings = MagicMock()
        mock_settings.GetTrackWidth.return_value = 100000
        mock_settings.GetMinClearance.return_value = 100000
        mock_settings.GetViasDimensions.return_value = 200000
        mock_settings.GetViasDrill.return_value = 100000
        mock_board.GetDesignSettings.return_value = mock_settings
        
        # Mock layers
        mock_board.GetCopperLayerCount.return_value = 2
        mock_board.GetLayerName.side_effect = lambda i: ["F.Cu", "B.Cu"][i]
        mock_board.IsLayerEnabled.return_value = True
        mock_board.IsLayerVisible.return_value = True
        
        # Get initial board state
        initial_state = self.validator._get_board_state(mock_board)
        
        # Verify initial state
        self.assertIn('components', initial_state)
        self.assertIn('dimensions', initial_state)
        self.assertIn('tracks', initial_state)
        self.assertIn('vias', initial_state)
        self.assertIn('zones', initial_state)
        self.assertIn('design_rules', initial_state)
        self.assertIn('layers', initial_state)
        self.assertIn('timestamp', initial_state)
        
        # Verify component positions
        self.assertEqual(len(initial_state['components']), 2)
        self.assertEqual(initial_state['components']['R1'], (1.0, 1.0))
        self.assertEqual(initial_state['components']['R2'], (2.0, 2.0))
        
        # Verify dimensions
        self.assertEqual(initial_state['dimensions'], (100.0, 100.0))
        
        # Verify tracks
        self.assertEqual(len(initial_state['tracks']), 1)
        track = initial_state['tracks'][0]
        self.assertEqual(track['net'], 'Net1')
        self.assertEqual(track['layer'], 'F.Cu')
        self.assertEqual(track['width'], 100000)
        self.assertEqual(track['start'], (1000000, 1000000))
        self.assertEqual(track['end'], (2000000, 2000000))
        
        # Verify vias
        self.assertEqual(len(initial_state['vias']), 1)
        via = initial_state['vias'][0]
        self.assertEqual(via['net'], 'Net1')
        self.assertEqual(via['position'], (1500000, 1500000))
        self.assertEqual(via['width'], 200000)
        self.assertEqual(via['drill'], 100000)
        
        # Verify zones
        self.assertEqual(len(initial_state['zones']), 1)
        zone = initial_state['zones'][0]
        self.assertEqual(zone['net'], 'GND')
        self.assertEqual(zone['layer'], 'F.Cu')
        self.assertEqual(zone['area'], 1000000)
        
        # Verify design rules
        rules = initial_state['design_rules']
        self.assertEqual(rules['min_track_width'], 100000)
        self.assertEqual(rules['min_clearance'], 100000)
        self.assertEqual(rules['via_diameter'], 200000)
        self.assertEqual(rules['via_drill'], 100000)
        
        # Verify layers
        self.assertEqual(len(initial_state['layers']), 2)
        self.assertEqual(initial_state['layers'][0]['name'], 'F.Cu')
        self.assertEqual(initial_state['layers'][1]['name'], 'B.Cu')
        
        # Test change detection
        self.validator._last_board_state = initial_state
        
        # No changes
        self.assertFalse(self.validator._has_board_changed(initial_state))
        
        # Change component position
        mock_footprint1.GetPosition.return_value = pcbnew.VECTOR2I(3000000, 3000000)
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state))
        
        # Change track
        mock_track.GetWidth.return_value = 200000
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state))
        
        # Change via
        mock_via.GetWidth.return_value = 300000
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state))
        
        # Change zone
        mock_zone.GetArea.return_value = 2000000
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state))
        
        # Change design rules
        mock_settings.GetTrackWidth.return_value = 200000
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state))
        
        # Change layer visibility
        mock_board.IsLayerVisible.return_value = False
        new_state = self.validator._get_board_state(mock_board)
        self.assertTrue(self.validator._has_board_changed(new_state)) 