"""Tests for the validation result display."""
import unittest
from unittest.mock import MagicMock, patch
import wx
from kicad_pcb_generator.core.validation.ui.validation_result_display import (
    ValidationResultDisplay,
    show_validation_results
)
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult,
    SafetyValidationResult,
    ManufacturingValidationResult
)

class TestValidationResultDisplay(unittest.TestCase):
    """Test cases for the validation result display."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.frame = ValidationResultDisplay()
        self.test_results = [
            ValidationResult(
                message="Test message 1",
                category=ValidationCategory.DESIGN,
                severity=ValidationSeverity.ERROR,
                location=(10.0, 20.0),
                details={"key1": "value1"}
            ),
            AudioValidationResult(
                message="Audio test message",
                category=ValidationCategory.AUDIO,
                severity=ValidationSeverity.WARNING,
                location=(30.0, 40.0),
                frequency=1000,
                impedance=50,
                crosstalk=0.1,
                noise_level=-60,
                power_quality=0.95,
                thermal_impact=25
            ),
            SafetyValidationResult(
                message="Safety test message",
                category=ValidationCategory.SAFETY,
                severity=ValidationSeverity.CRITICAL,
                location=(50.0, 60.0),
                voltage=12,
                current=1.5,
                power=18,
                temperature=45,
                clearance=2.5,
                creepage=5.0
            ),
            ManufacturingValidationResult(
                message="Manufacturing test message",
                category=ValidationCategory.MANUFACTURING,
                severity=ValidationSeverity.INFO,
                location=(70.0, 80.0),
                min_feature_size=0.1,
                max_feature_size=10.0,
                recommended_size=1.0,
                manufacturing_cost=0.8,
                yield_impact=0.95
            )
        ]
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.frame.Destroy()
        self.app.Destroy()
    
    def test_initialization(self):
        """Test initialization of the display."""
        self.assertIsNotNone(self.frame)
        self.assertEqual(self.frame.GetTitle(), "Validation Results")
        self.assertEqual(len(self.frame.results), 0)
    
    def test_display_results(self):
        """Test displaying results."""
        self.frame.display_results(self.test_results)
        self.assertEqual(len(self.frame.results), 4)
        self.assertEqual(self.frame.results_list.GetItemCount(), 4)
    
    def test_search(self):
        """Test search functionality."""
        self.frame.display_results(self.test_results)
        
        # Search for "audio"
        self.frame.search_ctrl.SetValue("audio")
        self.frame.on_search(MagicMock())
        self.assertEqual(self.frame.results_list.GetItemCount(), 1)
        
        # Search for "test"
        self.frame.search_ctrl.SetValue("test")
        self.frame.on_search(MagicMock())
        self.assertEqual(self.frame.results_list.GetItemCount(), 4)
    
    def test_filter(self):
        """Test filter functionality."""
        self.frame.display_results(self.test_results)
        
        # Filter by critical
        self.frame.filter_choice.SetSelection(1)  # Critical
        self.frame.on_filter(MagicMock())
        self.assertEqual(self.frame.results_list.GetItemCount(), 1)
        
        # Filter by all
        self.frame.filter_choice.SetSelection(0)  # All
        self.frame.on_filter(MagicMock())
        self.assertEqual(self.frame.results_list.GetItemCount(), 4)
    
    def test_sort(self):
        """Test sort functionality."""
        self.frame.display_results(self.test_results)
        
        # Sort by severity
        self.frame.sort_choice.SetSelection(0)  # Severity
        self.frame.on_sort(MagicMock())
        first_item = self.frame.results_list.GetItem(0, 0).GetText()
        self.assertEqual(first_item, ValidationSeverity.CRITICAL.value)
        
        # Sort by category
        self.frame.sort_choice.SetSelection(1)  # Category
        self.frame.on_sort(MagicMock())
        first_item = self.frame.results_list.GetItem(0, 1).GetText()
        self.assertEqual(first_item, ValidationCategory.AUDIO.value)
    
    def test_item_selection(self):
        """Test item selection."""
        self.frame.display_results(self.test_results)
        
        # Select first item
        self.frame.results_list.Select(0)
        event = MagicMock()
        event.GetIndex.return_value = 0
        self.frame.on_item_selected(event)
        
        # Check message panel
        self.assertEqual(self.frame.message_text.GetValue(), "Test message 1")
        
        # Check details panel
        details = self.frame.details_text.GetValue()
        self.assertIn("key1: value1", details)
        
        # Check location panel
        location = self.frame.location_text.GetValue()
        self.assertIn("X: 10.00 mm", location)
        self.assertIn("Y: 20.00 mm", location)
    
    @patch('wx.FileDialog')
    def test_export_json(self, mock_dialog):
        """Test JSON export."""
        self.frame.display_results(self.test_results)
        
        # Mock file dialog
        mock_dialog.return_value.ShowModal.return_value = wx.ID_OK
        mock_dialog.return_value.GetPath.return_value = "test.json"
        
        # Mock file writing
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.frame.on_export(ReportFormat.JSON)
            mock_file.assert_called_once_with("test.json", 'w')
    
    @patch('wx.FileDialog')
    def test_export_csv(self, mock_dialog):
        """Test CSV export."""
        self.frame.display_results(self.test_results)
        
        # Mock file dialog
        mock_dialog.return_value.ShowModal.return_value = wx.ID_OK
        mock_dialog.return_value.GetPath.return_value = "test.csv"
        
        # Mock file writing
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.frame.on_export(ReportFormat.CSV)
            mock_file.assert_called_once_with("test.csv", 'w')
    
    def test_show_validation_results(self):
        """Test show_validation_results function."""
        with patch('wx.App') as mock_app:
            mock_frame = MagicMock()
            with patch('kicad_pcb_generator.core.validation.ui.validation_result_display.ValidationResultDisplay',
                      return_value=mock_frame):
                show_validation_results(self.test_results)
                mock_app.assert_called_once()
                mock_frame.display_results.assert_called_once_with(self.test_results)
                mock_frame.Show.assert_called_once()
                mock_app.return_value.MainLoop.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
