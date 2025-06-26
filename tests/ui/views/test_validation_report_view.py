"""
Tests for the validation report viewer.
"""
import unittest
from unittest.mock import Mock, patch
import wx

from ....core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity
)
from ....ui.views.validation_report_view import ValidationReportView, ReportSummary

class TestValidationReportView(unittest.TestCase):
    """Test cases for ValidationReportView."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.view = ValidationReportView(self.frame)
        
    def tearDown(self):
        """Clean up test environment."""
        self.frame.Destroy()
        self.app.Destroy()
        
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.view)
        self.assertEqual(len(self.view.results), 0)
        self.assertIsNone(self.view.summary)
        
    def test_set_results(self):
        """Test setting validation results."""
        # Create test results
        results = [
            ValidationResult(
                message="Test error",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SAFETY,
                location=(0, 0),
                details={"test": "details"}
            ),
            ValidationResult(
                message="Test warning",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.AUDIO,
                location=(1, 1)
            ),
            ValidationResult(
                message="Test info",
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.MANUFACTURING
            )
        ]
        
        # Set results
        self.view.set_results(results)
        
        # Check results
        self.assertEqual(len(self.view.results), 3)
        self.assertIsNotNone(self.view.summary)
        self.assertEqual(self.view.summary.total_issues, 3)
        self.assertEqual(self.view.summary.errors, 1)
        self.assertEqual(self.view.summary.warnings, 1)
        self.assertEqual(self.view.summary.info, 1)
        
    def test_filter_by_severity(self):
        """Test filtering by severity."""
        # Create test results
        results = [
            ValidationResult(
                message="Test error",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SAFETY
            ),
            ValidationResult(
                message="Test warning",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.AUDIO
            ),
            ValidationResult(
                message="Test info",
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.MANUFACTURING
            )
        ]
        
        # Set results
        self.view.set_results(results)
        
        # Filter by error severity
        self.view.severity_choice.SetStringSelection(ValidationSeverity.ERROR.value)
        self.view._on_filter_change(None)
        
        # Check filtered results
        self.assertEqual(self.view.results_grid.GetNumberRows(), 1)
        self.assertEqual(
            self.view.results_grid.GetCellValue(0, 0),
            ValidationSeverity.ERROR.value
        )
        
    def test_filter_by_category(self):
        """Test filtering by category."""
        # Create test results
        results = [
            ValidationResult(
                message="Test safety",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SAFETY
            ),
            ValidationResult(
                message="Test audio",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.AUDIO
            ),
            ValidationResult(
                message="Test manufacturing",
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.MANUFACTURING
            )
        ]
        
        # Set results
        self.view.set_results(results)
        
        # Filter by safety category
        self.view._filter_by_category(ValidationCategory.SAFETY)
        
        # Check filtered results
        self.assertEqual(self.view.results_grid.GetNumberRows(), 1)
        self.assertEqual(
            self.view.results_grid.GetCellValue(0, 1),
            ValidationCategory.SAFETY.value
        )
        
    def test_search(self):
        """Test search functionality."""
        # Create test results
        results = [
            ValidationResult(
                message="Test error message",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SAFETY,
                details={"key": "error details"}
            ),
            ValidationResult(
                message="Test warning message",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.AUDIO,
                details={"key": "warning details"}
            )
        ]
        
        # Set results
        self.view.set_results(results)
        
        # Search for "error"
        self.view.search_text.SetValue("error")
        self.view._on_filter_change(None)
        
        # Check filtered results
        self.assertEqual(self.view.results_grid.GetNumberRows(), 1)
        self.assertEqual(
            self.view.results_grid.GetCellValue(0, 2),
            "Test error message"
        )
        
    def test_empty_results(self):
        """Test handling of empty results."""
        # Set empty results
        self.view.set_results([])
        
        # Check summary
        self.assertEqual(self.view.summary_text.GetLabel(), "No validation results")
        self.assertEqual(self.view.results_grid.GetNumberRows(), 0)
        
    def test_cell_colors(self):
        """Test cell background colors based on severity."""
        # Create test results
        results = [
            ValidationResult(
                message="Test error",
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.SAFETY
            ),
            ValidationResult(
                message="Test warning",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.AUDIO
            ),
            ValidationResult(
                message="Test info",
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.MANUFACTURING
            )
        ]
        
        # Set results
        self.view.set_results(results)
        
        # Check colors
        self.assertEqual(
            self.view.results_grid.GetCellBackgroundColour(0, 0),
            wx.RED
        )
        self.assertEqual(
            self.view.results_grid.GetCellBackgroundColour(1, 0),
            wx.YELLOW
        )
        self.assertEqual(
            self.view.results_grid.GetCellBackgroundColour(2, 0),
            wx.GREEN
        ) 