"""Tests for version migration scenarios."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import json
from pathlib import Path

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)

class TestVersionMigration(unittest.TestCase):
    """Test version migration scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("test_templates")
        self.test_dir.mkdir(exist_ok=True)
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
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_format_migration(self):
        """Test migrating between format versions."""
        # Create old format version
        old_version = TemplateVersion(
            version="v1",
            timestamp=datetime.now(),
            changes=[
                TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.CREATED,
                    user="test_user",
                    description="Old format version"
                )
            ],
            metadata={
                "format_version": "1.0",
                "name": "Test Template",
                "description": "Test template description"
            }
        )
        
        # Save old version
        self.manager.versions["test_template"] = [old_version]
        self.manager._save_versions("test_template")
        
        # Migrate to new format
        migrated = self.manager.migrate_version_format("test_template", "2.0")
        self.assertTrue(migrated)
        
        # Verify migration
        version = self.manager.get_version("test_template", "v1")
        self.assertEqual(version.metadata["format_version"], "2.0")
        self.assertIn("migration_timestamp", version.metadata)
    
    def test_schema_migration(self):
        """Test migrating between schema versions."""
        # Create old schema version
        old_version = TemplateVersion(
            version="v1",
            timestamp=datetime.now(),
            changes=[
                TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.CREATED,
                    user="test_user",
                    description="Old schema version"
                )
            ],
            metadata={
                "schema_version": "1.0",
                "name": "Test Template",
                "description": "Test template description",
                "old_field": "value"  # Field to be migrated
            }
        )
        
        # Save old version
        self.manager.versions["test_template"] = [old_version]
        self.manager._save_versions("test_template")
        
        # Define schema migration
        def migrate_schema(version):
            version.metadata["new_field"] = version.metadata.pop("old_field")
            version.metadata["schema_version"] = "2.0"
            return version
        
        # Migrate schema
        migrated = self.manager.migrate_schema("test_template", migrate_schema)
        self.assertTrue(migrated)
        
        # Verify migration
        version = self.manager.get_version("test_template", "v1")
        self.assertEqual(version.metadata["schema_version"], "2.0")
        self.assertIn("new_field", version.metadata)
        self.assertNotIn("old_field", version.metadata)
    
    def test_data_migration(self):
        """Test migrating template data between versions."""
        # Create old data version
        old_version = TemplateVersion(
            version="v1",
            timestamp=datetime.now(),
            changes=[
                TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.CREATED,
                    user="test_user",
                    description="Old data version"
                )
            ],
            metadata={
                "data_version": "1.0",
                "name": "Test Template",
                "description": "Test template description",
                "data": {
                    "old_format": "value"
                }
            }
        )
        
        # Save old version
        self.manager.versions["test_template"] = [old_version]
        self.manager._save_versions("test_template")
        
        # Define data migration
        def migrate_data(version):
            old_data = version.metadata["data"]
            version.metadata["data"] = {
                "new_format": old_data["old_format"]
            }
            version.metadata["data_version"] = "2.0"
            return version
        
        # Migrate data
        migrated = self.manager.migrate_data("test_template", migrate_data)
        self.assertTrue(migrated)
        
        # Verify migration
        version = self.manager.get_version("test_template", "v1")
        self.assertEqual(version.metadata["data_version"], "2.0")
        self.assertIn("new_format", version.metadata["data"])
        self.assertNotIn("old_format", version.metadata["data"])
    
    def test_rollback_migration(self):
        """Test rolling back a migration."""
        # Create initial version
        old_version = TemplateVersion(
            version="v1",
            timestamp=datetime.now(),
            changes=[
                TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.CREATED,
                    user="test_user",
                    description="Initial version"
                )
            ],
            metadata={
                "format_version": "1.0",
                "name": "Test Template",
                "description": "Test template description"
            }
        )
        
        # Save initial version
        self.manager.versions["test_template"] = [old_version]
        self.manager._save_versions("test_template")
        
        # Migrate to new format
        migrated = self.manager.migrate_version_format("test_template", "2.0")
        self.assertTrue(migrated)
        
        # Rollback migration
        rolled_back = self.manager.rollback_migration("test_template", "v1")
        self.assertTrue(rolled_back)
        
        # Verify rollback
        version = self.manager.get_version("test_template", "v1")
        self.assertEqual(version.metadata["format_version"], "1.0")
        self.assertNotIn("migration_timestamp", version.metadata)
    
    def test_migration_validation(self):
        """Test validating migrated versions."""
        # Create old format version
        old_version = TemplateVersion(
            version="v1",
            timestamp=datetime.now(),
            changes=[
                TemplateChange(
                    timestamp=datetime.now(),
                    change_type=ChangeType.CREATED,
                    user="test_user",
                    description="Old format version"
                )
            ],
            metadata={
                "format_version": "1.0",
                "name": "Test Template",
                "description": "Test template description"
            }
        )
        
        # Save old version
        self.manager.versions["test_template"] = [old_version]
        self.manager._save_versions("test_template")
        
        # Define validation function
        def validate_migration(version):
            return (
                version.metadata.get("format_version") == "2.0" and
                "migration_timestamp" in version.metadata
            )
        
        # Migrate and validate
        migrated = self.manager.migrate_version_format("test_template", "2.0")
        self.assertTrue(migrated)
        
        validation = self.manager.validate_migration("test_template", validate_migration)
        self.assertTrue(validation)

if __name__ == "__main__":
    unittest.main() 