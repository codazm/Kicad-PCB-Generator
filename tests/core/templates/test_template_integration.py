"""Tests for template integration layer."""

import os
import json
import shutil
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pcbnew
from kicad_pcb_generator.core.templates.template_integration import TemplateIntegrationManager
from kicad_pcb_generator.core.templates.rule_template import RuleTemplateData
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory

class TestTemplateIntegration(unittest.TestCase):
    """Test cases for template integration layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.integration = TemplateIntegrationManager(self.base_path)
        
        # Create test board
        self.board = pcbnew.BOARD()
        
        # Create test rule template
        self.rule_template = RuleTemplateData(
            name="test_rule",
            description="Test rule template",
            category=ValidationCategory.SAFETY,
            severity="error",
            parameters={
                "min_distance": 0.1,
                "max_distance": 1.0
            }
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_create_template_version(self):
        """Test creating a template version with components."""
        # Create version
        metadata = {
            "author": "Test Author",
            "description": "Test version",
            "change": {
                "type": "create",
                "description": "Initial version"
            }
        }
        
        result = self.integration.create_template_version(
            template_id="test_template",
            board=self.board,
            metadata=metadata,
            rule_templates=[self.rule_template]
        )
        
        self.assertTrue(result)
        
        # Check version was created
        version_data = self.integration.get_template_version(
            "test_template",
            "v1"
        )
        self.assertIsNotNone(version_data)
        self.assertEqual(version_data["version"].version, "v1")
        
        # Check rule template was created
        self.assertEqual(len(version_data["rule_templates"]), 1)
        self.assertEqual(version_data["rule_templates"][0].name, "test_rule")
    
    def test_get_template_version(self):
        """Test getting a template version with components."""
        # Create version first
        metadata = {
            "author": "Test Author",
            "description": "Test version",
            "change": {
                "type": "create",
                "description": "Initial version"
            }
        }
        
        self.integration.create_template_version(
            template_id="test_template",
            board=self.board,
            metadata=metadata,
            rule_templates=[self.rule_template]
        )
        
        # Get version
        version_data = self.integration.get_template_version(
            "test_template",
            "v1"
        )
        
        self.assertIsNotNone(version_data)
        self.assertIn("version", version_data)
        self.assertIn("board", version_data)
        self.assertIn("rule_templates", version_data)
        self.assertIn("metadata", version_data)
    
    def test_import_template_version(self):
        """Test importing a template version."""
        # Create export file
        export_path = self.base_path / "test_template.json"
        with open(export_path, 'w') as f:
            json.dump({
                "test_template": {
                    "name": "Test Template",
                    "description": "Test template",
                    "metadata": {
                        "author": "Test Author",
                        "version": "1.0.0"
                    }
                }
            }, f)
        
        # Import template
        result = self.integration.import_template_version(export_path)
        
        self.assertIsNotNone(result)
        self.assertIn("template", result)
        self.assertIn("version", result)
        self.assertIn("metadata", result)
    
    def test_validate_template_version(self):
        """Test validating a template version."""
        # Create version first
        metadata = {
            "author": "Test Author",
            "description": "Test version",
            "change": {
                "type": "create",
                "description": "Initial version"
            }
        }
        
        self.integration.create_template_version(
            template_id="test_template",
            board=self.board,
            metadata=metadata,
            rule_templates=[self.rule_template]
        )
        
        # Validate version
        validation_results = self.integration.validate_template_version(
            "test_template",
            "v1"
        )
        
        self.assertIn("version", validation_results)
        self.assertIn("board_validation", validation_results)
        self.assertIn("rule_validation", validation_results)
        self.assertIn("overall_status", validation_results)
    
    def test_get_template_history(self):
        """Test getting template history."""
        # Create multiple versions
        for i in range(3):
            metadata = {
                "author": "Test Author",
                "description": f"Version {i+1}",
                "change": {
                    "type": "update",
                    "description": f"Update {i+1}"
                }
            }
            
            self.integration.create_template_version(
                template_id="test_template",
                board=self.board,
                metadata=metadata,
                rule_templates=[self.rule_template]
            )
        
        # Get history
        history = self.integration.get_template_history("test_template")
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["version"], "v1")
        self.assertEqual(history[1]["version"], "v2")
        self.assertEqual(history[2]["version"], "v3")
    
    def test_nonexistent_template(self):
        """Test operations with nonexistent template."""
        # Try to get version
        version_data = self.integration.get_template_version(
            "nonexistent",
            "v1"
        )
        self.assertIsNone(version_data)
        
        # Try to validate version
        validation_results = self.integration.validate_template_version(
            "nonexistent",
            "v1"
        )
        self.assertIn("error", validation_results)
        
        # Try to get history
        history = self.integration.get_template_history("nonexistent")
        self.assertEqual(len(history), 0)
    
    def test_invalid_import_file(self):
        """Test importing invalid template file."""
        # Create invalid export file
        export_path = self.base_path / "invalid.json"
        with open(export_path, 'w') as f:
            f.write("invalid json")
        
        # Try to import
        result = self.integration.import_template_version(export_path)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main() 