"""Tests for template validation system."""

import unittest
from unittest.mock import Mock, patch
import json
from pathlib import Path
from datetime import datetime

from kicad_pcb_generator.core.templates.template_validation import (
    TemplateValidator,
    ValidationResult,
    ValidationSummary,
    ValidationSeverity
)
from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion
)
from kicad_pcb_generator.core.templates.rule_template import RuleTemplate

class TestTemplateValidator(unittest.TestCase):
    """Test template validator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_templates")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create mock version manager
        self.version_manager = Mock(spec=TemplateVersionManager)
        
        # Create mock rule template
        self.rule_template = Mock(spec=RuleTemplate)
        
        # Create validator
        self.validator = TemplateValidator(
            self.test_dir,
            version_manager=self.version_manager,
            rule_template=self.rule_template
        )
        
        # Create test template
        self.test_template = {
            "name": "Test Template",
            "description": "A test template for validation",
            "category": "safety",
            "type": "constraint",
            "severity": "error",
            "constraints": {
                "param1": {
                    "min_value": 0,
                    "max_value": 100
                },
                "param2": {
                    "allowed_values": ["value1", "value2"]
                }
            },
            "dependencies": ["rule1", "rule2"],
            "metadata": {
                "author": "Test User",
                "created": "2024-01-01"
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_validate_template_structure(self):
        """Test template structure validation."""
        result = self.validator._validate_template_structure(self.test_template)
        self.assertTrue(result.success)
        self.assertEqual(result.severity, ValidationSeverity.INFO)
    
    def test_validate_template_structure_missing_fields(self):
        """Test template structure validation with missing fields."""
        template = self.test_template.copy()
        del template["name"]
        
        result = self.validator._validate_template_structure(template)
        self.assertFalse(result.success)
        self.assertEqual(result.severity, ValidationSeverity.ERROR)
        self.assertIn("Missing required fields", result.message)
    
    def test_validate_template_structure_invalid_types(self):
        """Test template structure validation with invalid types."""
        template = self.test_template.copy()
        template["dependencies"] = "not a list"
        
        result = self.validator._validate_template_structure(template)
        self.assertFalse(result.success)
        self.assertEqual(result.severity, ValidationSeverity.ERROR)
        self.assertIn("Invalid type", result.message)
    
    def test_validate_template_content(self):
        """Test template content validation."""
        result = self.validator._validate_template_content(self.test_template)
        self.assertTrue(result.success)
        self.assertEqual(result.severity, ValidationSeverity.INFO)
    
    def test_validate_template_content_invalid_name(self):
        """Test template content validation with invalid name."""
        template = self.test_template.copy()
        template["name"] = "A"
        
        result = self.validator._validate_template_content(template)
        self.assertFalse(result.success)
        self.assertEqual(result.severity, ValidationSeverity.ERROR)
        self.assertIn("Name must be at least 3 characters", result.message)
    
    def test_validate_template_content_invalid_category(self):
        """Test template content validation with invalid category."""
        template = self.test_template.copy()
        template["category"] = "invalid"
        
        result = self.validator._validate_template_content(template)
        self.assertFalse(result.success)
        self.assertEqual(result.severity, ValidationSeverity.ERROR)
        self.assertIn("Invalid category", result.message)
    
    def test_validate_rule_templates(self):
        """Test rule template validation."""
        # Mock rule template data
        rule1 = {
            "name": "Rule 1",
            "description": "Test rule 1",
            "category": "safety",
            "type": "rule",
            "severity": "error",
            "constraints": {},
            "dependencies": []
        }
        rule2 = {
            "name": "Rule 2",
            "description": "Test rule 2",
            "category": "performance",
            "type": "rule",
            "severity": "warning",
            "constraints": {},
            "dependencies": []
        }
        
        # Mock rule template getter
        self.rule_template.get_rule_template.side_effect = [rule1, rule2]
        
        results = self.validator._validate_rule_templates(self.test_template)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.success for r in results))
    
    def test_validate_rule_templates_missing_rule(self):
        """Test rule template validation with missing rule."""
        # Mock rule template getter to return None
        self.rule_template.get_rule_template.return_value = None
        
        results = self.validator._validate_rule_templates(self.test_template)
        self.assertEqual(len(results), 2)
        self.assertFalse(all(r.success for r in results))
        self.assertIn("not found", results[0].message)
    
    def test_validate_template_with_version(self):
        """Test template validation with version."""
        # Mock version data
        version_data = TemplateVersion(
            template_id="test_template",
            version="v1",
            timestamp=datetime.now(),
            template=self.test_template,
            changes="Initial version",
            dependencies=[],
            validation_results=[]
        )
        
        # Mock version manager
        self.version_manager.get_version.return_value = version_data
        
        summary = self.validator.validate_template("test_template", version="v1")
        self.assertTrue(summary.overall_success)
        self.assertEqual(summary.version, "v1")
    
    def test_validate_template_without_version(self):
        """Test template validation without version."""
        # Save test template
        template_file = self.test_dir / "test_template.json"
        with open(template_file, 'w') as f:
            json.dump(self.test_template, f)
        
        summary = self.validator.validate_template("test_template")
        self.assertTrue(summary.overall_success)
        self.assertIsNone(summary.version)
    
    def test_validate_template_version_not_found(self):
        """Test template validation with non-existent version."""
        # Mock version manager to return None
        self.version_manager.get_version.return_value = None
        
        summary = self.validator.validate_template("test_template", version="v1")
        self.assertFalse(summary.overall_success)
        self.assertIn("Version not found", summary.results[0].message)
    
    def test_get_validation_history(self):
        """Test getting validation history."""
        # Create validation directory
        validation_dir = self.test_dir / "test_template"
        validation_dir.mkdir(exist_ok=True)
        
        # Create validation files
        validation_data = {
            "template_id": "test_template",
            "version": "v1",
            "timestamp": datetime.now().isoformat(),
            "overall_success": True,
            "results": [
                {
                    "success": True,
                    "message": "Template is valid",
                    "severity": "info",
                    "details": None
                }
            ],
            "metadata": {
                "template_name": "Test Template",
                "template_category": "safety",
                "template_type": "constraint",
                "validation_rules": 1
            }
        }
        
        validation_file = validation_dir / "validation_v1_20240101_120000.json"
        with open(validation_file, 'w') as f:
            json.dump(validation_data, f)
        
        history = self.validator.get_validation_history("test_template")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].template_id, "test_template")
        self.assertEqual(history[0].version, "v1")
    
    def test_get_validation_history_with_version(self):
        """Test getting validation history for specific version."""
        # Create validation directory
        validation_dir = self.test_dir / "test_template"
        validation_dir.mkdir(exist_ok=True)
        
        # Create validation files for different versions
        for version in ["v1", "v2"]:
            validation_data = {
                "template_id": "test_template",
                "version": version,
                "timestamp": datetime.now().isoformat(),
                "overall_success": True,
                "results": [
                    {
                        "success": True,
                        "message": "Template is valid",
                        "severity": "info",
                        "details": None
                    }
                ],
                "metadata": {
                    "template_name": "Test Template",
                    "template_category": "safety",
                    "template_type": "constraint",
                    "validation_rules": 1
                }
            }
            
            validation_file = validation_dir / f"validation_{version}_20240101_120000.json"
            with open(validation_file, 'w') as f:
                json.dump(validation_data, f)
        
        history = self.validator.get_validation_history("test_template", version="v1")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].version, "v1")
    
    def test_validation_result_serialization(self):
        """Test validation result serialization."""
        result = ValidationResult(
            success=True,
            message="Test message",
            severity=ValidationSeverity.INFO,
            details={"key": "value"}
        )
        
        # Test serialization
        data = {
            "success": result.success,
            "message": result.message,
            "severity": result.severity.value,
            "details": result.details
        }
        
        # Test deserialization
        loaded_result = ValidationResult(
            success=data["success"],
            message=data["message"],
            severity=ValidationSeverity(data["severity"]),
            details=data["details"]
        )
        
        self.assertEqual(result.success, loaded_result.success)
        self.assertEqual(result.message, loaded_result.message)
        self.assertEqual(result.severity, loaded_result.severity)
        self.assertEqual(result.details, loaded_result.details)
    
    def test_validation_summary_serialization(self):
        """Test validation summary serialization."""
        summary = ValidationSummary(
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
            metadata={"key": "value"}
        )
        
        # Test serialization
        data = self.validator._format_validation_summary(summary)
        
        # Test deserialization
        loaded_summary = self.validator._load_validation_summary(data)
        
        self.assertEqual(summary.template_id, loaded_summary.template_id)
        self.assertEqual(summary.version, loaded_summary.version)
        self.assertEqual(summary.overall_success, loaded_summary.overall_success)
        self.assertEqual(len(summary.results), len(loaded_summary.results))
        self.assertEqual(summary.metadata, loaded_summary.metadata)

if __name__ == "__main__":
    unittest.main() 