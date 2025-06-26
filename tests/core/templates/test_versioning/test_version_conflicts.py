"""Tests for version conflict scenarios."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateChange,
    ChangeType
)

class TestVersionConflicts(unittest.TestCase):
    """Test version conflict scenarios."""
    
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
    
    def test_concurrent_version_creation(self):
        """Test handling concurrent version creation."""
        # Create initial version
        change1 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="user1",
            description="Initial version"
        )
        self.manager.add_version("test_template", self.template, change1)
        
        # Simulate concurrent version creation
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="user2",
            description="Concurrent modification"
        )
        
        # Mock file system operations to simulate conflict
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = [True, False]  # First check succeeds, second fails
            
            # Attempt to add version
            result = self.manager.add_version("test_template", self.template, change2)
            
            # Verify conflict was handled
            self.assertIsNotNone(result)
            self.assertEqual(result.version, "v2")
            
            # Verify both changes are preserved
            history = self.manager.get_version_history("test_template")
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0].changes[0].user, "user1")
            self.assertEqual(history[1].changes[0].user, "user2")
    
    def test_concurrent_version_update(self):
        """Test handling concurrent version updates."""
        # Create initial version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Initial version"
        )
        version = self.manager.add_version("test_template", self.template, change)
        
        # Simulate concurrent updates
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = [True, False]  # First check succeeds, second fails
            
            # First update
            version.metadata["updated_by"] = "user1"
            result1 = self.manager.update_version("test_template", version)
            
            # Second update
            version.metadata["updated_by"] = "user2"
            result2 = self.manager.update_version("test_template", version)
            
            # Verify both updates were handled
            self.assertTrue(result1)
            self.assertTrue(result2)
            
            # Check final state
            final_version = self.manager.get_version("test_template", version.version)
            self.assertEqual(final_version.metadata["updated_by"], "user2")
    
    def test_version_merge_conflict(self):
        """Test handling version merge conflicts."""
        # Create base version
        base_change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Base version"
        )
        base_version = self.manager.add_version("test_template", self.template, base_change)
        
        # Create two divergent versions
        template1 = Mock()
        template1.metadata = {"name": "Template 1"}
        template2 = Mock()
        template2.metadata = {"name": "Template 2"}
        
        change1 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="user1",
            description="First modification"
        )
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="user2",
            description="Second modification"
        )
        
        # Add divergent versions
        version1 = self.manager.add_version("test_template", template1, change1)
        version2 = self.manager.add_version("test_template", template2, change2)
        
        # Attempt to merge
        merged = self.manager.merge_versions(
            "test_template",
            version1.version,
            version2.version,
            "test_user"
        )
        
        # Verify merge was handled
        self.assertIsNotNone(merged)
        self.assertIn("merge_conflict", merged.metadata)
        self.assertIn("resolved_by", merged.metadata)
    
    def test_version_lock_conflict(self):
        """Test handling version lock conflicts."""
        # Create initial version
        change = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Initial version"
        )
        version = self.manager.add_version("test_template", self.template, change)
        
        # Simulate lock conflict
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = [True, False]  # First check succeeds, second fails
            
            # First lock attempt
            lock1 = self.manager.lock_version("test_template", version.version, "user1")
            
            # Second lock attempt
            lock2 = self.manager.lock_version("test_template", version.version, "user2")
            
            # Verify lock conflict was handled
            self.assertTrue(lock1)
            self.assertFalse(lock2)
            
            # Check lock state
            locked_version = self.manager.get_version("test_template", version.version)
            self.assertEqual(locked_version.metadata.get("locked_by"), "user1")

if __name__ == "__main__":
    unittest.main() 