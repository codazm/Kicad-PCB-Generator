"""Tests for rule template system."""

import unittest
from unittest.mock import Mock, patch
import json
from pathlib import Path
from datetime import datetime

from kicad_pcb_generator.core.templates.rule_template import (
    RuleTemplate,
    RuleTemplateData
)
from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion
)

class TestRuleTemplate(unittest.TestCase):
    """Test cases for rule template system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_templates")
        self.test_dir.mkdir(exist_ok=True)
        
        # Create version manager mock
        self.version_manager = Mock(spec=TemplateVersionManager)
        
        # Create rule template manager
        self.rule_template = RuleTemplate(
            str(self.test_dir),
            version_manager=self.version_manager
        )
        
        # Create test template data
        self.template_data = RuleTemplateData(
            name="Minimum Trace Width",
            description="Minimum trace width constraint",
            category="safety",
            type="constraint",
            severity="error",
            constraints={
                "min_width": {
                    "min_value": 0.2,
                    "max_value": 1.0
                }
            },
            dependencies=[],
            metadata={
                "author": "Test User",
                "tags": ["safety", "trace"]
            }
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
        
    def test_create_rule_template(self):
        """Test creating a rule template."""
        # Create template
        template_id = self.rule_template.create_rule_template(self.template_data)
        
        # Check result
        self.assertIsNotNone(template_id)
        self.assertTrue(template_id.startswith("minimum_trace_width_"))
        
        # Check template file
        template_file = self.test_dir / f"{template_id}.json"
        self.assertTrue(template_file.exists())
        
        # Check template data
        with open(template_file) as f:
            template = json.load(f)
            self.assertEqual(template['name'], self.template_data.name)
            self.assertEqual(template['description'], self.template_data.description)
            self.assertEqual(template['category'], self.template_data.category)
            self.assertEqual(template['type'], self.template_data.type)
            self.assertEqual(template['severity'], self.template_data.severity)
            self.assertEqual(template['constraints'], self.template_data.constraints)
            self.assertEqual(template['dependencies'], self.template_data.dependencies)
            self.assertEqual(template['metadata'], self.template_data.metadata)
        
        # Check version was created
        self.version_manager.add_version.assert_called_once()
        call_args = self.version_manager.add_version.call_args[1]
        self.assertEqual(call_args['template_id'], template_id)
        self.assertEqual(call_args['change']['type'], 'create')
        self.assertEqual(call_args['change']['description'], 'Initial version')
        
    def test_create_rule_template_with_versioning_failure(self):
        """Test handling version creation failure."""
        # Mock version creation failure
        self.version_manager.add_version.return_value = None
        
        # Create template
        template_id = self.rule_template.create_rule_template(self.template_data)
        
        # Check result
        self.assertIsNotNone(template_id)
        self.assertTrue(template_id.startswith("minimum_trace_width_"))
        
        # Check template file
        template_file = self.test_dir / f"{template_id}.json"
        self.assertTrue(template_file.exists())
        
    def test_get_rule_template(self):
        """Test getting a rule template."""
        # Create template
        template_id = self.rule_template.create_rule_template(self.template_data)
        
        # Get template
        template = self.rule_template.get_rule_template(template_id)
        
        # Check result
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], self.template_data.name)
        self.assertEqual(template['description'], self.template_data.description)
        self.assertEqual(template['category'], self.template_data.category)
        self.assertEqual(template['type'], self.template_data.type)
        self.assertEqual(template['severity'], self.template_data.severity)
        self.assertEqual(template['constraints'], self.template_data.constraints)
        self.assertEqual(template['dependencies'], self.template_data.dependencies)
        self.assertEqual(template['metadata'], self.template_data.metadata)
        
    def test_get_rule_template_with_version(self):
        """Test getting a specific version of a rule template."""
        # Mock version data
        version_data = Mock(spec=TemplateVersion)
        version_data.template = {
            'name': 'Test Template',
            'description': 'Test description',
            'category': 'test',
            'type': 'test',
            'severity': 'test',
            'constraints': {},
            'dependencies': [],
            'metadata': {}
        }
        self.version_manager.get_version.return_value = version_data
        
        # Get template version
        template = self.rule_template.get_rule_template('test_template', version='v1')
        
        # Check result
        self.assertIsNotNone(template)
        self.assertEqual(template['name'], 'Test Template')
        self.assertEqual(template['description'], 'Test description')
        
        # Check version manager was called
        self.version_manager.get_version.assert_called_once_with('test_template', 'v1')
        
    def test_update_rule_template(self):
        """Test updating a rule template."""
        # Create template
        template_id = self.rule_template.create_rule_template(self.template_data)
        
        # Update template
        updates = {
            'description': 'Updated description',
            'metadata': {
                'author': 'Test User',
                'tags': ['safety', 'trace', 'updated']
            }
        }
        success = self.rule_template.update_rule_template(template_id, updates)
        
        # Check result
        self.assertTrue(success)
        
        # Check template data
        template = self.rule_template.get_rule_template(template_id)
        self.assertEqual(template['description'], 'Updated description')
        self.assertEqual(template['metadata']['tags'], ['safety', 'trace', 'updated'])
        
        # Check version was created
        self.version_manager.add_version.assert_called()
        call_args = self.version_manager.add_version.call_args[1]
        self.assertEqual(call_args['template_id'], template_id)
        self.assertEqual(call_args['change']['type'], 'update')
        self.assertEqual(call_args['change']['description'], 'Template updated')
        
    def test_delete_rule_template(self):
        """Test deleting a rule template."""
        # Create template
        template_id = self.rule_template.create_rule_template(self.template_data)
        
        # Delete template
        success = self.rule_template.delete_rule_template(template_id)
        
        # Check result
        self.assertTrue(success)
        
        # Check template file
        template_file = self.test_dir / f"{template_id}.json"
        self.assertFalse(template_file.exists())
        
        # Check version was created
        self.version_manager.add_version.assert_called()
        call_args = self.version_manager.add_version.call_args[1]
        self.assertEqual(call_args['template_id'], template_id)
        self.assertEqual(call_args['change']['type'], 'delete')
        self.assertEqual(call_args['change']['description'], 'Template deleted')
        
    def test_list_rule_templates(self):
        """Test listing rule templates."""
        # Create templates
        template1 = RuleTemplateData(
            name="Template 1",
            description="Test template 1",
            category="safety",
            type="constraint",
            severity="error",
            constraints={},
            dependencies=[],
            metadata={}
        )
        template2 = RuleTemplateData(
            name="Template 2",
            description="Test template 2",
            category="performance",
            type="constraint",
            severity="warning",
            constraints={},
            dependencies=[],
            metadata={}
        )
        
        self.rule_template.create_rule_template(template1)
        self.rule_template.create_rule_template(template2)
        
        # List all templates
        templates = self.rule_template.list_rule_templates()
        self.assertEqual(len(templates), 2)
        
        # List safety templates
        templates = self.rule_template.list_rule_templates(category="safety")
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], "Template 1")
        
        # List performance templates
        templates = self.rule_template.list_rule_templates(category="performance")
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]['name'], "Template 2")
        
        # List constraint templates
        templates = self.rule_template.list_rule_templates(type="constraint")
        self.assertEqual(len(templates), 2)

if __name__ == "__main__":
    unittest.main() 