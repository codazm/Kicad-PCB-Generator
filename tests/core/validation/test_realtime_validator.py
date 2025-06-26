"""
Tests for the real-time validation system.
"""
import unittest
from unittest.mock import Mock, patch
import time
from typing import List

import pcbnew
from kicad_pcb_generator.core.validation.realtime_validator import RealtimeValidator, ValidationIssue, ValidationSeverity
from kicad_pcb_generator.utils.logging.logger import Logger
from kicad_pcb_generator.utils.config.settings import Settings

class TestRealtimeValidator(unittest.TestCase):
    """Test cases for the RealtimeValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock(spec=Logger)
        self.settings = Mock(spec=Settings)
        self.validator = RealtimeValidator(
            logger=self.logger,
            settings=self.settings,
            validation_interval=0.1  # Short interval for testing
        )
        self.board = Mock(spec=pcbnew.BOARD)
        self.validator.set_board(self.board)
        
    def test_start_stop_validation(self):
        """Test starting and stopping validation."""
        # Start validation
        self.validator.start_validation()
        self.assertIsNotNone(self.validator._validation_thread)
        self.assertTrue(self.validator._validation_thread.is_alive())
        
        # Stop validation
        self.validator.stop_validation()
        self.assertFalse(self.validator._validation_thread.is_alive())
        
    def test_callback_registration(self):
        """Test registering and removing callbacks."""
        callback = Mock()
        
        # Add callback
        self.validator.add_callback(callback)
        self.assertEqual(len(self.validator._callbacks), 1)
        
        # Remove callback
        self.validator.remove_callback(callback)
        self.assertEqual(len(self.validator._callbacks), 0)
        
    def test_callback_filtering(self):
        """Test callback filtering functionality."""
        callback = Mock()
        issues = [
            ValidationIssue(
                message="Test error",
                severity=ValidationSeverity.ERROR,
                component_id="R1"
            ),
            ValidationIssue(
                message="Test warning",
                severity=ValidationSeverity.WARNING,
                component_id="R2"
            )
        ]
        
        # Add callback with filters
        self.validator.add_callback(
            callback,
            severity_filter=[ValidationSeverity.ERROR],
            component_filter=["R1"]
        )
        
        # Simulate validation results
        self.validator._notify_callbacks(issues)
        
        # Verify callback was called with filtered issues
        callback.assert_called_once()
        filtered_issues = callback.call_args[0][0]
        self.assertEqual(len(filtered_issues), 1)
        self.assertEqual(filtered_issues[0].severity, ValidationSeverity.ERROR)
        self.assertEqual(filtered_issues[0].component_id, "R1")
        
    def test_validation_loop(self):
        """Test the validation loop functionality."""
        callback = Mock()
        self.validator.add_callback(callback)
        
        # Start validation
        self.validator.start_validation()
        
        # Wait for at least one validation cycle
        time.sleep(0.2)
        
        # Stop validation
        self.validator.stop_validation()
        
        # Verify callback was called
        self.assertTrue(callback.call_count > 0)
        
    def test_error_handling(self):
        """Test error handling in validation loop."""
        # Mock validator to raise an exception
        self.validator.validator.validate_board = Mock(side_effect=Exception("Test error"))
        
        # Start validation
        self.validator.start_validation()
        
        # Wait for at least one validation cycle
        time.sleep(0.2)
        
        # Stop validation
        self.validator.stop_validation()
        
        # Verify error was logged
        self.logger.error.assert_called()
        
if __name__ == '__main__':
    unittest.main() 