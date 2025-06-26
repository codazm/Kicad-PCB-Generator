"""Tests for version compatibility scenarios."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)

class TestVersionCompatibility(unittest.TestCase):
    """Test version compatibility scenarios."""
    
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
    
    def test_version_compatibility_checks(self):
        """Test version compatibility checks."""
        # Create versions with different compatibility requirements
        v1_template = Mock()
        v1_template.metadata = {
            "name": "Test Template",
            "version": "1.0.0",
            "compatibility": {
                "min_version": "1.0.0",
                "max_version": "1.9.9"
            }
        }
        
        v2_template = Mock()
        v2_template.metadata = {
            "name": "Test Template",
            "version": "2.0.0",
            "compatibility": {
                "min_version": "2.0.0",
                "max_version": "2.9.9"
            }
        }
        
        # Add versions
        change1 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Version 1"
        )
        self.manager.add_version("test_template", v1_template, change1)
        
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="test_user",
            description="Version 2"
        )
        self.manager.add_version("test_template", v2_template, change2)
        
        # Test compatibility checks
        self.assertTrue(self.manager.check_version_compatibility("test_template", "v1", "1.5.0"))
        self.assertFalse(self.manager.check_version_compatibility("test_template", "v1", "2.0.0"))
        self.assertTrue(self.manager.check_version_compatibility("test_template", "v2", "2.5.0"))
        self.assertFalse(self.manager.check_version_compatibility("test_template", "v2", "1.5.0"))
    
    def test_cross_version_dependencies(self):
        """Test handling cross-version dependencies."""
        # Create dependent versions
        v1_template = Mock()
        v1_template.metadata = {
            "name": "Test Template",
            "version": "1.0.0",
            "dependencies": {
                "library": "1.0.0",
                "components": ["comp1", "comp2"]
            }
        }
        
        v2_template = Mock()
        v2_template.metadata = {
            "name": "Test Template",
            "version": "2.0.0",
            "dependencies": {
                "library": "2.0.0",
                "components": ["comp1", "comp2", "comp3"]
            }
        }
        
        # Add versions
        change1 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Version 1"
        )
        self.manager.add_version("test_template", v1_template, change1)
        
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="test_user",
            description="Version 2"
        )
        self.manager.add_version("test_template", v2_template, change2)
        
        # Test dependency resolution
        deps_v1 = self.manager.resolve_dependencies("test_template", "v1")
        self.assertEqual(deps_v1["library"], "1.0.0")
        self.assertEqual(len(deps_v1["components"]), 2)
        
        deps_v2 = self.manager.resolve_dependencies("test_template", "v2")
        self.assertEqual(deps_v2["library"], "2.0.0")
        self.assertEqual(len(deps_v2["components"]), 3)
    
    def test_version_upgrade_path(self):
        """Test version upgrade path resolution."""
        # Create versions with upgrade paths
        versions = []
        for i in range(3):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "upgrade_path": {
                    "from_version": f"{i}.0.0" if i > 0 else None,
                    "to_version": f"{i+2}.0.0" if i < 2 else None
                }
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            version = self.manager.add_version("test_template", template, change)
            versions.append(version)
        
        # Test upgrade path resolution
        path = self.manager.get_upgrade_path("test_template", "1.0.0", "3.0.0")
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0].version, "1.0.0")
        self.assertEqual(path[1].version, "2.0.0")
        self.assertEqual(path[2].version, "3.0.0")
    
    def test_version_compatibility_matrix(self):
        """Test version compatibility matrix generation."""
        # Create versions with compatibility info
        versions = []
        for i in range(3):
            template = Mock()
            template.metadata = {
                "name": f"Test Template v{i+1}",
                "version": f"{i+1}.0.0",
                "compatibility": {
                    "min_version": f"{i}.0.0",
                    "max_version": f"{i+2}.0.0"
                }
            }
            
            change = TemplateChange(
                timestamp=datetime.now(),
                change_type=ChangeType.CREATED,
                user="test_user",
                description=f"Version {i+1}"
            )
            
            version = self.manager.add_version("test_template", template, change)
            versions.append(version)
        
        # Generate compatibility matrix
        matrix = self.manager.generate_compatibility_matrix("test_template")
        
        # Verify matrix
        self.assertIn("1.0.0", matrix)
        self.assertIn("2.0.0", matrix)
        self.assertIn("3.0.0", matrix)
        
        # Check compatibility relationships
        self.assertTrue(matrix["1.0.0"]["2.0.0"])  # v1 compatible with v2
        self.assertFalse(matrix["1.0.0"]["3.0.0"])  # v1 not compatible with v3
        self.assertTrue(matrix["2.0.0"]["3.0.0"])  # v2 compatible with v3
    
    def test_version_feature_compatibility(self):
        """Test version feature compatibility checks."""
        # Create versions with different features
        v1_template = Mock()
        v1_template.metadata = {
            "name": "Test Template",
            "version": "1.0.0",
            "features": ["feature1", "feature2"]
        }
        
        v2_template = Mock()
        v2_template.metadata = {
            "name": "Test Template",
            "version": "2.0.0",
            "features": ["feature1", "feature2", "feature3"]
        }
        
        # Add versions
        change1 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.CREATED,
            user="test_user",
            description="Version 1"
        )
        self.manager.add_version("test_template", v1_template, change1)
        
        change2 = TemplateChange(
            timestamp=datetime.now(),
            change_type=ChangeType.MODIFIED,
            user="test_user",
            description="Version 2"
        )
        self.manager.add_version("test_template", v2_template, change2)
        
        # Test feature compatibility
        self.assertTrue(self.manager.check_feature_compatibility("test_template", "v1", ["feature1"]))
        self.assertTrue(self.manager.check_feature_compatibility("test_template", "v1", ["feature1", "feature2"]))
        self.assertFalse(self.manager.check_feature_compatibility("test_template", "v1", ["feature3"]))
        self.assertTrue(self.manager.check_feature_compatibility("test_template", "v2", ["feature1", "feature2", "feature3"]))

if __name__ == "__main__":
    unittest.main() 