"""Integration tests for versioning components."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import json
import os
import shutil

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)
from kicad_pcb_generator.core.templates.template_validation import (
    TemplateValidator,
    ValidationResult,
    ValidationSeverity
)
from kicad_pcb_generator.core.templates.template_export import (
    TemplateExporter,
    ExportFormat
)

class TestVersionIntegration(unittest.TestCase):
    """Test integration between versioning components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = "test_templates"
        self.manager = TemplateVersionManager(self.test_dir)
        self.validator = TemplateValidator()
        self.exporter = TemplateExporter()
        
        # Create test template
        self.template = Mock()
        self.template.name = "Test Template"
        self.template.description = "Test template description"
        self.template.metadata = {
            "name": "Test Template",
            "description": "Test template description",
            "version": "1.0.0",
            "format_version": "1.0",
            "schema_version": "1.0"
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_version_validation_export_workflow(self):
        """Test complete workflow of version creation, validation, and export."""
        # Create initial version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Initial version"
        )
        
        version = self.manager.add_version("test_template", self.template, change)
        
        # Validate version
        validation_results = self.validator.validate_template(version)
        self.assertTrue(validation_results.is_valid)
        
        # Export version
        export_data = self.exporter.export_template(
            version,
            format=ExportFormat.JSON,
            include_validation=True
        )
        
        # Verify export data
        self.assertIn("version", export_data)
        self.assertIn("validation_results", export_data)
        self.assertEqual(export_data["version"]["metadata"]["version"], "1.0.0")
    
    def test_version_migration_validation_workflow(self):
        """Test workflow of version migration and validation."""
        # Create old format version
        old_template = Mock()
        old_template.metadata = {
            "name": "Old Template",
            "version": "1.0.0",
            "format_version": "0.9",
            "schema_version": "0.9"
        }
        
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Old format version"
        )
        
        old_version = self.manager.add_version("test_template", old_template, change)
        
        # Migrate to new format
        new_version = self.manager.migrate_version(
            "test_template",
            old_version.version_id,
            target_format="1.0",
            target_schema="1.0"
        )
        
        # Validate migrated version
        validation_results = self.validator.validate_template(new_version)
        self.assertTrue(validation_results.is_valid)
        
        # Verify migration
        self.assertEqual(new_version.metadata["format_version"], "1.0")
        self.assertEqual(new_version.metadata["schema_version"], "1.0")
    
    def test_version_conflict_resolution_workflow(self):
        """Test workflow of version conflict resolution."""
        # Create initial version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="user1",
            description="Initial version"
        )
        
        version1 = self.manager.add_version("test_template", self.template, change)
        
        # Create conflicting version
        template2 = Mock()
        template2.metadata = {
            "name": "Test Template",
            "version": "1.0.0",
            "format_version": "1.0",
            "schema_version": "1.0",
            "data": {"key": "value2"}
        }
        
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="user2",
            description="Conflicting change"
        )
        
        version2 = self.manager.add_version("test_template", template2, change2)
        
        # Resolve conflict
        resolved_version = self.manager.resolve_version_conflict(
            "test_template",
            version1.version_id,
            version2.version_id,
            resolution_strategy="merge"
        )
        
        # Validate resolved version
        validation_results = self.validator.validate_template(resolved_version)
        self.assertTrue(validation_results.is_valid)
        
        # Verify resolution
        self.assertIn("key", resolved_version.metadata["data"])
        self.assertEqual(resolved_version.metadata["data"]["key"], "value2")
    
    def test_version_rollback_workflow(self):
        """Test workflow of version rollback."""
        # Create multiple versions
        versions = []
        for i in range(3):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "format_version": "1.0",
                "schema_version": "1.0",
                "data": {"key": f"value{i+1}"}
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.MODIFIED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            version = self.manager.add_version("test_template", template, change)
            versions.append(version)
        
        # Rollback to first version
        rolled_back = self.manager.rollback_version(
            "test_template",
            versions[0].version_id
        )
        
        # Validate rolled back version
        validation_results = self.validator.validate_template(rolled_back)
        self.assertTrue(validation_results.is_valid)
        
        # Verify rollback
        self.assertEqual(rolled_back.metadata["version"], "1.0.0")
        self.assertEqual(rolled_back.metadata["data"]["key"], "value1")
    
    def test_version_export_import_workflow(self):
        """Test workflow of version export and import."""
        # Create version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Initial version"
        )
        
        version = self.manager.add_version("test_template", self.template, change)
        
        # Export version
        export_data = self.exporter.export_template(
            version,
            format=ExportFormat.JSON,
            include_validation=True
        )
        
        # Create new manager for import
        new_manager = TemplateVersionManager("new_test_templates")
        
        # Import version
        imported_version = new_manager.import_version(
            "imported_template",
            export_data
        )
        
        # Validate imported version
        validation_results = self.validator.validate_template(imported_version)
        self.assertTrue(validation_results.is_valid)
        
        # Verify import
        self.assertEqual(imported_version.metadata["version"], "1.0.0")
        self.assertEqual(imported_version.metadata["name"], "Test Template")
    
    def test_version_validation_history_workflow(self):
        """Test workflow of version validation history."""
        # Create version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Initial version"
        )
        
        version = self.manager.add_version("test_template", self.template, change)
        
        # Perform multiple validations
        validation_results = []
        for i in range(3):
            results = self.validator.validate_template(version)
            validation_results.append(results)
            
            # Update template for next validation
            version.metadata["version"] = f"1.0.{i+1}"
        
        # Get validation history
        history = self.manager.get_validation_history("test_template", version.version_id)
        
        # Verify history
        self.assertEqual(len(history), 3)
        for i, entry in enumerate(history):
            self.assertEqual(entry["version"], f"1.0.{i+1}")
            self.assertTrue(entry["is_valid"])

if __name__ == "__main__":
    unittest.main() 