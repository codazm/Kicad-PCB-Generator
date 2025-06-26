"""Tests for the validation report generator."""
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from kicad_pcb_generator.core.validation.report_generator import (
    ValidationReportGenerator,
    ReportFormat,
    ValidationSummary
)
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult,
    SafetyValidationResult,
    ManufacturingValidationResult
)

class TestValidationReportGenerator(unittest.TestCase):
    """Test cases for the validation report generator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = ValidationReportGenerator()
        
        # Create test results
        self.results = [
            ValidationResult(
                category=ValidationCategory.DESIGN_RULES,
                message="Test design rule violation",
                severity=ValidationSeverity.ERROR,
                location=(0.0, 0.0),
                details={"rule": "test_rule"}
            ),
            AudioValidationResult(
                category=ValidationCategory.AUDIO_SPECIFIC,
                message="Test audio validation",
                severity=ValidationSeverity.WARNING,
                frequency=1000.0,
                impedance=50.0
            ),
            SafetyValidationResult(
                category=ValidationCategory.POWER,
                message="Test safety validation",
                severity=ValidationSeverity.CRITICAL,
                voltage=12.0,
                current=1.0
            ),
            ManufacturingValidationResult(
                category=ValidationCategory.MANUFACTURING,
                message="Test manufacturing validation",
                severity=ValidationSeverity.INFO,
                manufacturing_cost=0.5,
                yield_impact=0.1
            )
        ]
    
    def test_generate_summary(self):
        """Test summary generation."""
        summary = self.generator._generate_summary(self.results)
        
        self.assertEqual(summary.total_issues, 4)
        self.assertEqual(summary.critical_issues, 1)
        self.assertEqual(summary.errors, 1)
        self.assertEqual(summary.warnings, 1)
        self.assertEqual(summary.info, 1)
        self.assertEqual(len(summary.categories), 4)
        self.assertIsInstance(summary.timestamp, datetime)
    
    def test_generate_json_report(self):
        """Test JSON report generation."""
        report = self.generator._generate_json_report(self.results, self.generator._generate_summary(self.results))
        
        # Parse JSON
        data = eval(report)  # Safe since we control the input
        
        # Check summary
        self.assertEqual(data["summary"]["total_issues"], 4)
        self.assertEqual(data["summary"]["critical_issues"], 1)
        self.assertEqual(data["summary"]["errors"], 1)
        self.assertEqual(data["summary"]["warnings"], 1)
        self.assertEqual(data["summary"]["info"], 1)
        
        # Check results
        self.assertEqual(len(data["results"]), 4)
    
    def test_generate_csv_report(self):
        """Test CSV report generation."""
        report = self.generator._generate_csv_report(self.results, self.generator._generate_summary(self.results))
        
        # Check header
        self.assertIn("Category,Severity,Message,Location,Details", report)
        
        # Check content
        self.assertIn("DESIGN_RULES,ERROR,Test design rule violation", report)
        self.assertIn("AUDIO_SPECIFIC,WARNING,Test audio validation", report)
        self.assertIn("POWER,CRITICAL,Test safety validation", report)
        self.assertIn("MANUFACTURING,INFO,Test manufacturing validation", report)
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        report = self.generator._generate_html_report(self.results, self.generator._generate_summary(self.results))
        
        # Check structure
        self.assertIn("<!DOCTYPE html>", report)
        self.assertIn("<html>", report)
        self.assertIn("<head>", report)
        self.assertIn("<body>", report)
        
        # Check content
        self.assertIn("Validation Report", report)
        self.assertIn("Summary", report)
        self.assertIn("Results", report)
        self.assertIn("Test design rule violation", report)
        self.assertIn("Test audio validation", report)
        self.assertIn("Test safety validation", report)
        self.assertIn("Test manufacturing validation", report)
    
    def test_generate_markdown_report(self):
        """Test Markdown report generation."""
        report = self.generator._generate_markdown_report(self.results, self.generator._generate_summary(self.results))
        
        # Check structure
        self.assertIn("# Validation Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("## Results", report)
        
        # Check content
        self.assertIn("Test design rule violation", report)
        self.assertIn("Test audio validation", report)
        self.assertIn("Test safety validation", report)
        self.assertIn("Test manufacturing validation", report)
    
    def test_generate_report_invalid_format(self):
        """Test report generation with invalid format."""
        with self.assertRaises(ValueError):
            self.generator.generate_report(self.results, "invalid_format")
    
    def test_generate_report_error_handling(self):
        """Test error handling during report generation."""
        with patch.object(self.generator, '_generate_summary', side_effect=Exception("Test error")):
            with self.assertRaises(Exception):
                self.generator.generate_report(self.results)
    
    def test_generate_report_empty_results(self):
        """Test report generation with empty results."""
        report = self.generator.generate_report([])
        
        # Parse JSON
        data = eval(report)  # Safe since we control the input
        
        # Check summary
        self.assertEqual(data["summary"]["total_issues"], 0)
        self.assertEqual(data["summary"]["critical_issues"], 0)
        self.assertEqual(data["summary"]["errors"], 0)
        self.assertEqual(data["summary"]["warnings"], 0)
        self.assertEqual(data["summary"]["info"], 0)
        
        # Check results
        self.assertEqual(len(data["results"]), 0) 