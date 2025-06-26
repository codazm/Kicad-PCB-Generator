"""
Tests for the export dialog.
"""

import unittest
from unittest.mock import Mock, patch
import wx
from datetime import datetime
from core.validation.validation_results import ValidationResult, Severity, Category
from ui.dialogs.export_dialog import ExportDialog, ExportOptions
from core.validation.report_generator import ReportFormat

class TestExportDialog(unittest.TestCase):
    """Test cases for the export dialog."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        
        # Create test results
        self.results = [
            ValidationResult(
                rule_id="test_rule_1",
                message="Test error",
                severity=Severity.ERROR,
                category=Category.DESIGN_RULES,
                location=(0, 0),
                timestamp=datetime.now()
            ),
            ValidationResult(
                rule_id="test_rule_2",
                message="Test warning",
                severity=Severity.WARNING,
                category=Category.AUDIO_SPECIFIC,
                location=(1, 1),
                timestamp=datetime.now()
            )
        ]
        
        self.dialog = ExportDialog(self.frame, self.results)
    
    def tearDown(self):
        """Clean up test environment."""
        self.dialog.Destroy()
        self.frame.Destroy()
        self.app.Destroy()
    
    def test_init(self):
        """Test dialog initialization."""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(len(self.dialog.results), 2)
        self.assertIsInstance(self.dialog.options, ExportOptions)
    
    def test_get_options(self):
        """Test getting export options."""
        # Set some options
        self.dialog.format_choice.SetSelection(0)  # JSON
        self.dialog.include_summary.SetValue(True)
        self.dialog.include_details.SetValue(False)
        self.dialog.sort_by_severity.SetValue(True)
        
        options = self.dialog._get_options()
        
        self.assertEqual(options.format, ReportFormat.JSON)
        self.assertTrue(options.include_summary)
        self.assertFalse(options.include_details)
        self.assertTrue(options.sort_by_severity)
    
    def test_filter_results(self):
        """Test filtering results."""
        # Set severity filter
        self.dialog.severity_list.Check(0)  # ERROR
        
        filtered = self.dialog._filter_results()
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].severity, Severity.ERROR)
    
    def test_filter_by_category(self):
        """Test filtering by category."""
        # Set category filter
        self.dialog.category_list.Check(1)  # AUDIO_SPECIFIC
        
        filtered = self.dialog._filter_results()
        
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].category, Category.AUDIO_SPECIFIC)
    
    def test_sort_results(self):
        """Test sorting results."""
        # Set sorting options
        self.dialog.sort_by_severity.SetValue(True)
        self.dialog.sort_by_category.SetValue(True)
        
        sorted_results = self.dialog._filter_results()
        
        # Results should be sorted by severity first, then category
        self.assertEqual(sorted_results[0].severity, Severity.ERROR)
        self.assertEqual(sorted_results[1].severity, Severity.WARNING)
    
    @patch('ui.dialogs.export_dialog.wx.FileDialog')
    @patch('ui.dialogs.export_dialog.ValidationReportGenerator')
    def test_export(self, mock_generator, mock_dialog):
        """Test exporting results."""
        # Mock file dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value.__enter__.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        mock_dialog_instance.GetPath.return_value = "test.json"
        
        # Mock report generator
        mock_generator_instance = Mock()
        mock_generator.return_value = mock_generator_instance
        mock_generator_instance.generate_report.return_value = "test report"
        
        # Trigger export
        self.dialog._on_export(None)
        
        # Verify generator was called
        mock_generator_instance.generate_report.assert_called_once()
    
    def test_cancel(self):
        """Test canceling export."""
        self.dialog._on_cancel(None)
        self.assertEqual(self.dialog.GetReturnCode(), wx.ID_CANCEL)
    
    def test_preview_update(self):
        """Test preview update."""
        # Change format
        self.dialog.format_choice.SetSelection(1)  # CSV
        
        # Trigger preview update
        self.dialog._on_format_change(None)
        
        # Preview should be updated
        self.assertNotEqual(self.dialog.preview.GetValue(), "")
    
    def test_error_handling(self):
        """Test error handling."""
        # Mock generator to raise exception
        with patch('ui.dialogs.export_dialog.ValidationReportGenerator') as mock_generator:
            mock_generator_instance = Mock()
            mock_generator.return_value = mock_generator_instance
            mock_generator_instance.generate_report.side_effect = Exception("Test error")
            
            # Trigger preview update
            self.dialog._update_preview()
            
            # Error should be shown in preview
            self.assertIn("Error generating preview", self.dialog.preview.GetValue()) 