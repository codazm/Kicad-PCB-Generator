"""Tests for bulk version operations."""

import unittest
from unittest.mock import Mock
from datetime import datetime

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateChange,
    ChangeType
)

class TestBulkOperations(unittest.TestCase):
    """Test bulk version operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = "test_templates"
        self.manager = TemplateVersionManager(self.test_dir)
        
        # Create test template
        self.template = Mock()
        self.template.name = "Test Template"
        self.template.description = "Test template description"
        self.template.metadata = {
            "name": "Test Template",
            "description": "Test template description",
            "version": "1.0.0"
        }
    
    def test_bulk_version_creation(self):
        """Test creating multiple versions in bulk."""
        # Create multiple versions in bulk
        changes = [
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i}"
            )
            for i in range(5)
        ]
        
        # Add versions in bulk
        versions = self.manager.add_versions("test_template", self.template, changes)
        
        # Verify all versions were created
        self.assertEqual(len(versions), 5)
        self.assertEqual(versions[0].version, "v1")
        self.assertEqual(versions[-1].version, "v5")
        
        # Verify version history
        history = self.manager.get_version_history("test_template")
        self.assertEqual(len(history), 5)
    
    def test_bulk_version_update(self):
        """Test updating multiple versions in bulk."""
        # Create initial versions
        changes = [
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i}"
            )
            for i in range(3)
        ]
        versions = self.manager.add_versions("test_template", self.template, changes)
        
        # Update versions in bulk
        updated_versions = []
        for version in versions:
            version.metadata["updated"] = True
            version.metadata["update_timestamp"] = datetime.now().isoformat()
            updated_versions.append(version)
        
        # Perform bulk update
        result = self.manager.update_versions("test_template", updated_versions)
        self.assertTrue(result)
        
        # Verify updates were applied
        history = self.manager.get_version_history("test_template")
        for version in history:
            self.assertTrue(version.metadata.get("updated", False))
            self.assertIn("update_timestamp", version.metadata)
    
    def test_bulk_version_deletion(self):
        """Test deleting multiple versions in bulk."""
        # Create versions to delete
        changes = [
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i}"
            )
            for i in range(5)
        ]
        versions = self.manager.add_versions("test_template", self.template, changes)
        
        # Delete versions in bulk
        version_ids = [v.version for v in versions[1:4]]  # Delete middle versions
        result = self.manager.delete_versions("test_template", version_ids)
        self.assertTrue(result)
        
        # Verify deletions
        history = self.manager.get_version_history("test_template")
        self.assertEqual(len(history), 2)  # Only first and last versions remain
        self.assertEqual(history[0].version, "v5")
        self.assertEqual(history[1].version, "v1")
    
    def test_bulk_version_validation(self):
        """Test validating multiple versions in bulk."""
        # Create versions to validate
        changes = [
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i}"
            )
            for i in range(3)
        ]
        versions = self.manager.add_versions("test_template", self.template, changes)
        
        # Validate versions in bulk
        version_ids = [v.version for v in versions]
        results = self.manager.validate_versions("test_template", version_ids)
        
        # Verify validation results
        self.assertEqual(len(results), 3)
        for version_id, result in results.items():
            self.assertIn("validation_status", result)
            self.assertIn("validation_timestamp", result)
    
    def test_bulk_version_export(self):
        """Test exporting multiple versions in bulk."""
        # Create versions to export
        changes = [
            TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i}"
            )
            for i in range(3)
        ]
        versions = self.manager.add_versions("test_template", self.template, changes)
        
        # Export versions in bulk
        version_ids = [v.version for v in versions]
        export_data = self.manager.export_versions("test_template", version_ids)
        
        # Verify export data
        self.assertIn("template_id", export_data)
        self.assertIn("versions", export_data)
        self.assertEqual(len(export_data["versions"]), 3)
        for version_data in export_data["versions"]:
            self.assertIn("version", version_data)
            self.assertIn("metadata", version_data)
            self.assertIn("changes", version_data)

if __name__ == "__main__":
    unittest.main() 