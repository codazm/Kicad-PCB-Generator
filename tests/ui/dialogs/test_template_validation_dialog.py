"""Tests for template validation dialogs."""

import unittest
from unittest.mock import Mock, patch
import wx
from datetime import datetime

from kicad_pcb_generator.core.templates.template_validation import (
    TemplateValidator,
    ValidationResult,
    ValidationSummary,
    ValidationSeverity
)
from kicad_pcb_generator.ui.dialogs.template_validation_dialog import (
    ValidationResultPanel,
    TemplateValidationDialog,
    ValidationHistoryDialog
)

class TestValidationResultPanel(unittest.TestCase):
    """Test validation result panel."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.panel = ValidationResultPanel(self.frame)
        
        # Create test results
        self.test_results = [
            ValidationResult(
                success=True,
                message="Test info message",
                severity=ValidationSeverity.INFO
            ),
            ValidationResult(
                success=False,
                message="Test warning message",
                severity=ValidationSeverity.WARNING,
                details={"key": "value"}
            ),
            ValidationResult(
                success=False,
                message="Test error message",
                severity=ValidationSeverity.ERROR
            )
        ]
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.frame.Destroy()
        self.app.Destroy()
    
    def test_update_results(self):
        """Test updating validation results."""
        self.panel.update_results(self.test_results)
        
        # Check item count
        self.assertEqual(self.panel.result_list.GetItemCount(), 3)
        
        # Check first item (info)
        self.assertEqual(self.panel.result_list.GetItem(0, 0).GetText(), "Info")
        self.assertEqual(self.panel.result_list.GetItem(0, 1).GetText(), "Test info message")
        self.assertEqual(self.panel.result_list.GetItem(0, 2).GetText(), "")
        
        # Check second item (warning)
        self.assertEqual(self.panel.result_list.GetItem(1, 0).GetText(), "Warning")
        self.assertEqual(self.panel.result_list.GetItem(1, 1).GetText(), "Test warning message")
        self.assertEqual(self.panel.result_list.GetItem(1, 2).GetText(), "{'key': 'value'}")
        
        # Check third item (error)
        self.assertEqual(self.panel.result_list.GetItem(2, 0).GetText(), "Error")
        self.assertEqual(self.panel.result_list.GetItem(2, 1).GetText(), "Test error message")
        self.assertEqual(self.panel.result_list.GetItem(2, 2).GetText(), "")

class TestTemplateValidationDialog(unittest.TestCase):
    """Test template validation dialog."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        
        # Create mock validator
        self.validator = Mock(spec=TemplateValidator)
        
        # Create test summary
        self.test_summary = ValidationSummary(
            template_id="test_template",
            version="v1",
            timestamp=datetime.now(),
            overall_success=True,
            results=[
                ValidationResult(
                    success=True,
                    message="Test message",
                    severity=ValidationSeverity.INFO
                )
            ],
            metadata={}
        )
        
        # Mock validate_template method
        self.validator.validate_template.return_value = self.test_summary
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.app.Destroy()
    
    def test_init(self):
        """Test dialog initialization."""
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check title
        self.assertEqual(dialog.GetTitle(), "Template Validation")
        
        # Check template text
        self.assertEqual(dialog.template_text.GetLabel(), "test_template")
        
        # Check version text
        self.assertEqual(dialog.version_text.GetLabel(), "v1")
        
        # Check validation was called
        self.validator.validate_template.assert_called_once_with(
            "test_template",
            version="v1"
        )
        
        dialog.Destroy()
    
    def test_init_without_version(self):
        """Test dialog initialization without version."""
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template"
        )
        
        # Check version text doesn't exist
        self.assertFalse(hasattr(dialog, "version_text"))
        
        # Check validation was called
        self.validator.validate_template.assert_called_once_with(
            "test_template",
            version=None
        )
        
        dialog.Destroy()
    
    def test_validation_success(self):
        """Test successful validation."""
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check status text
        self.assertEqual(dialog.status_text.GetLabel(), "Validation successful")
        self.assertEqual(dialog.status_text.GetForegroundColour(), wx.GREEN)
        
        # Check results
        self.assertEqual(dialog.result_panel.result_list.GetItemCount(), 1)
        
        dialog.Destroy()
    
    def test_validation_failure(self):
        """Test failed validation."""
        # Create failure summary
        failure_summary = ValidationSummary(
            template_id="test_template",
            version="v1",
            timestamp=datetime.now(),
            overall_success=False,
            results=[
                ValidationResult(
                    success=False,
                    message="Test error",
                    severity=ValidationSeverity.ERROR
                )
            ],
            metadata={}
        )
        
        # Update mock
        self.validator.validate_template.return_value = failure_summary
        
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check status text
        self.assertEqual(dialog.status_text.GetLabel(), "Validation failed")
        self.assertEqual(dialog.status_text.GetForegroundColour(), wx.RED)
        
        # Check results
        self.assertEqual(dialog.result_panel.result_list.GetItemCount(), 1)
        
        dialog.Destroy()
    
    def test_validation_error(self):
        """Test validation error."""
        # Mock validation error
        self.validator.validate_template.side_effect = Exception("Test error")
        
        # Create dialog
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check dialog was closed
        self.assertFalse(dialog.IsShown())
        
        dialog.Destroy()
    
    def test_validate_again(self):
        """Test validate again button."""
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Click validate again
        event = wx.CommandEvent(wx.wxEVT_BUTTON)
        dialog._on_validate_again(event)
        
        # Check validation was called twice
        self.assertEqual(self.validator.validate_template.call_count, 2)
        
        dialog.Destroy()
    
    def test_on_validate_callback(self):
        """Test on_validate callback."""
        callback = Mock()
        
        dialog = TemplateValidationDialog(
            None,
            self.validator,
            "test_template",
            version="v1",
            on_validate=callback
        )
        
        # Check callback was called
        callback.assert_called_once_with(self.test_summary)
        
        dialog.Destroy()

class TestValidationHistoryDialog(unittest.TestCase):
    """Test validation history dialog."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        
        # Create mock validator
        self.validator = Mock(spec=TemplateValidator)
        
        # Create test history
        self.test_history = [
            ValidationSummary(
                template_id="test_template",
                version="v1",
                timestamp=datetime.now(),
                overall_success=True,
                results=[
                    ValidationResult(
                        success=True,
                        message="Test message",
                        severity=ValidationSeverity.INFO
                    )
                ],
                metadata={}
            ),
            ValidationSummary(
                template_id="test_template",
                version="v2",
                timestamp=datetime.now(),
                overall_success=False,
                results=[
                    ValidationResult(
                        success=False,
                        message="Test error",
                        severity=ValidationSeverity.ERROR
                    )
                ],
                metadata={}
            )
        ]
        
        # Mock get_validation_history method
        self.validator.get_validation_history.return_value = self.test_history
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.app.Destroy()
    
    def test_init(self):
        """Test dialog initialization."""
        dialog = ValidationHistoryDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check title
        self.assertEqual(dialog.GetTitle(), "Validation History")
        
        # Check template text
        self.assertEqual(dialog.template_text.GetLabel(), "test_template")
        
        # Check version text
        self.assertEqual(dialog.version_text.GetLabel(), "v1")
        
        # Check history was loaded
        self.validator.get_validation_history.assert_called_once_with(
            "test_template",
            version="v1"
        )
        
        # Check list items
        self.assertEqual(dialog.history_list.GetItemCount(), 2)
        
        dialog.Destroy()
    
    def test_init_without_version(self):
        """Test dialog initialization without version."""
        dialog = ValidationHistoryDialog(
            None,
            self.validator,
            "test_template"
        )
        
        # Check version text doesn't exist
        self.assertFalse(hasattr(dialog, "version_text"))
        
        # Check history was loaded
        self.validator.get_validation_history.assert_called_once_with(
            "test_template",
            version=None
        )
        
        dialog.Destroy()
    
    def test_load_history_error(self):
        """Test history loading error."""
        # Mock history error
        self.validator.get_validation_history.side_effect = Exception("Test error")
        
        # Create dialog
        dialog = ValidationHistoryDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Check dialog was closed
        self.assertFalse(dialog.IsShown())
        
        dialog.Destroy()
    
    def test_history_selection(self):
        """Test history item selection."""
        dialog = ValidationHistoryDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Select first item
        event = wx.ListEvent(wx.wxEVT_LIST_ITEM_ACTIVATED)
        event.SetIndex(0)
        dialog._on_history_selected(event)
        
        # Check validation dialog was created
        self.assertTrue(dialog.IsShown())
        
        dialog.Destroy()
    
    def test_view_details(self):
        """Test view details button."""
        dialog = ValidationHistoryDialog(
            None,
            self.validator,
            "test_template",
            version="v1"
        )
        
        # Select first item
        dialog.history_list.Select(0)
        
        # Click view details
        event = wx.CommandEvent(wx.wxEVT_BUTTON)
        dialog._on_view_details(event)
        
        # Check validation dialog was created
        self.assertTrue(dialog.IsShown())
        
        dialog.Destroy()

if __name__ == "__main__":
    unittest.main() 