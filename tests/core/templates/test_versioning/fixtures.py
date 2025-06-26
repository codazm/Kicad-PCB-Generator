"""Test fixtures for versioning tests."""

import os
import shutil
import json
from datetime import datetime
from unittest.mock import Mock
from typing import Dict, List, Any, Optional, Tuple

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)

class VersionTestFixture:
    """Fixture for versioning tests."""
    
    def __init__(self, test_dir: str = "test_templates"):
        """Initialize the fixture.
        
        Args:
            test_dir: Directory for test data
        """
        self.test_dir = test_dir
        self.manager = TemplateVersionManager(test_dir)
        self._setup_test_environment()
    
    def _setup_test_environment(self):
        """Set up the test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)
    
    def create_template(self, 
                       name: str = "Test Template",
                       version: str = "1.0.0",
                       format_version: str = "1.0",
                       schema_version: str = "1.0",
                       data: Optional[Dict[str, Any]] = None) -> Mock:
        """Create a mock template.
        
        Args:
            name: Template name
            version: Template version
            format_version: Format version
            schema_version: Schema version
            data: Additional template data
            
        Returns:
            Mock template object
        """
        template = Mock()
        template.name = name
        template.description = f"Description for {name}"
        template.metadata = {
            "name": name,
            "description": f"Description for {name}",
            "version": version,
            "format_version": format_version,
            "schema_version": schema_version
        }
        
        if data:
            template.metadata.update(data)
            
        return template
    
    def create_change(self,
                     change_type: ChangeType = ChangeType.CREATED,
                     user: str = "test_user",
                     description: str = "Test change") -> TemplateChange:
        """Create a template change.
        
        Args:
            change_type: Type of change
            user: User making the change
            description: Change description
            
        Returns:
            TemplateChange object
        """
        return TemplateChange(
            timestamp=datetime.now(),
            change_type=change_type,
            user=user,
            description=description
        )
    
    def create_version_chain(self,
                           template_id: str,
                           num_versions: int,
                           base_version: str = "1.0.0") -> List[TemplateVersion]:
        """Create a chain of versions.
        
        Args:
            template_id: Template identifier
            num_versions: Number of versions to create
            base_version: Base version number
            
        Returns:
            List of created versions
        """
        versions = []
        for i in range(num_versions):
            template = self.create_template(
                name=f"Test Template v{i+1}",
                version=f"{base_version}.{i}",
                data={"data": f"value{i+1}"}
            )
            
            change = self.create_change(
                change_type=ChangeType.MODIFIED if i > 0 else ChangeType.CREATED,
                description=f"Version {i+1}"
            )
            
            version = self.manager.add_version(template_id, template, change)
            versions.append(version)
            
        return versions
    
    def create_conflicting_versions(self,
                                  template_id: str,
                                  base_version: str = "1.0.0") -> List[TemplateVersion]:
        """Create conflicting versions.
        
        Args:
            template_id: Template identifier
            base_version: Base version number
            
        Returns:
            List of conflicting versions
        """
        # Create initial version
        template1 = self.create_template(
            name="Test Template",
            version=base_version,
            data={"key": "value1"}
        )
        
        change1 = self.create_change(
            change_type=ChangeType.CREATED,
            user="user1",
            description="Initial version"
        )
        
        version1 = self.manager.add_version(template_id, template1, change1)
        
        # Create conflicting version
        template2 = self.create_template(
            name="Test Template",
            version=base_version,
            data={"key": "value2"}
        )
        
        change2 = self.create_change(
            change_type=ChangeType.MODIFIED,
            user="user2",
            description="Conflicting change"
        )
        
        version2 = self.manager.add_version(template_id, template2, change2)
        
        return [version1, version2]
    
    def create_migration_chain(self,
                             template_id: str,
                             start_format: str = "0.9",
                             target_format: str = "1.0") -> List[TemplateVersion]:
        """Create a chain of versions for migration testing.
        
        Args:
            template_id: Template identifier
            start_format: Starting format version
            target_format: Target format version
            
        Returns:
            List of versions in migration chain
        """
        # Create old format version
        old_template = self.create_template(
            name="Old Template",
            version="1.0.0",
            format_version=start_format,
            schema_version=start_format
        )
        
        change = self.create_change(
            change_type=ChangeType.CREATED,
            description="Old format version"
        )
        
        old_version = self.manager.add_version(template_id, old_template, change)
        
        # Migrate to new format
        new_version = self.manager.migrate_version(
            template_id,
            old_version.version_id,
            target_format=target_format,
            target_schema=target_format
        )
        
        return [old_version, new_version]
    
    def create_validation_history(self,
                                template_id: str,
                                version_id: str,
                                num_validations: int) -> List[Dict[str, Any]]:
        """Create validation history for a version.
        
        Args:
            template_id: Template identifier
            version_id: Version identifier
            num_validations: Number of validations to create
            
        Returns:
            List of validation results
        """
        history = []
        for i in range(num_validations):
            result = {
                "timestamp": datetime.now().isoformat(),
                "version": f"1.0.{i}",
                "is_valid": True,
                "results": [
                    {
                        "severity": "info",
                        "message": f"Validation {i+1}",
                        "details": f"Details for validation {i+1}"
                    }
                ]
            }
            history.append(result)
            
        return history
    
    def create_branch_versions(self,
                             template_id: str,
                             base_version: str = "1.0.0") -> Tuple[List[TemplateVersion], List[TemplateVersion]]:
        """Create branched versions.
        
        Args:
            template_id: Template identifier
            base_version: Base version number
            
        Returns:
            Tuple of (main branch versions, feature branch versions)
        """
        # Create main branch versions
        main_versions = []
        for i in range(3):
            template = self.create_template(
                name=f"Main Branch v{i+1}",
                version=f"{base_version}.{i}",
                data={"branch": "main", "data": f"main{i+1}"}
            )
            
            change = self.create_change(
                change_type=ChangeType.MODIFIED if i > 0 else ChangeType.CREATED,
                description=f"Main branch version {i+1}"
            )
            
            version = self.manager.add_version(template_id, template, change)
            main_versions.append(version)
        
        # Create feature branch versions
        feature_versions = []
        for i in range(2):
            template = self.create_template(
                name=f"Feature Branch v{i+1}",
                version=f"{base_version}.0-feature.{i}",
                data={"branch": "feature", "data": f"feature{i+1}"}
            )
            
            change = self.create_change(
                change_type=ChangeType.MODIFIED,
                description=f"Feature branch version {i+1}"
            )
            
            version = self.manager.add_version(template_id, template, change)
            feature_versions.append(version)
        
        return main_versions, feature_versions
    
    def create_merge_scenario(self,
                            template_id: str,
                            base_version: str = "1.0.0") -> Tuple[TemplateVersion, TemplateVersion, TemplateVersion]:
        """Create a merge scenario with three versions.
        
        Args:
            template_id: Template identifier
            base_version: Base version number
            
        Returns:
            Tuple of (base version, feature version, merge version)
        """
        # Create base version
        base_template = self.create_template(
            name="Base Version",
            version=base_version,
            data={"key": "base_value"}
        )
        
        base_change = self.create_change(
            change_type=ChangeType.CREATED,
            description="Base version"
        )
        
        base_version = self.manager.add_version(template_id, base_template, base_change)
        
        # Create feature version
        feature_template = self.create_template(
            name="Feature Version",
            version=f"{base_version}-feature",
            data={"key": "feature_value", "new_key": "new_value"}
        )
        
        feature_change = self.create_change(
            change_type=ChangeType.MODIFIED,
            description="Feature version"
        )
        
        feature_version = self.manager.add_version(template_id, feature_template, feature_change)
        
        # Create merge version
        merge_template = self.create_template(
            name="Merge Version",
            version=f"{base_version}.1",
            data={
                "key": "merged_value",
                "new_key": "new_value",
                "merged": True
            }
        )
        
        merge_change = self.create_change(
            change_type=ChangeType.MODIFIED,
            description="Merge version"
        )
        
        merge_version = self.manager.add_version(template_id, merge_template, merge_change)
        
        return base_version, feature_version, merge_version
    
    def create_rollback_scenario(self,
                               template_id: str,
                               base_version: str = "1.0.0") -> List[TemplateVersion]:
        """Create a rollback scenario with multiple versions.
        
        Args:
            template_id: Template identifier
            base_version: Base version number
            
        Returns:
            List of versions in rollback scenario
        """
        versions = []
        for i in range(4):
            template = self.create_template(
                name=f"Version {i+1}",
                version=f"{base_version}.{i}",
                data={
                    "key": f"value{i+1}",
                    "changes": [f"change{j+1}" for j in range(i+1)]
                }
            )
            
            change = self.create_change(
                change_type=ChangeType.MODIFIED if i > 0 else ChangeType.CREATED,
                description=f"Version {i+1}"
            )
            
            version = self.manager.add_version(template_id, template, change)
            versions.append(version)
        
        return versions
    
    def create_validation_scenario(self,
                                 template_id: str,
                                 base_version: str = "1.0.0") -> Tuple[TemplateVersion, List[Dict[str, Any]]]:
        """Create a validation scenario with a version and its validation history.
        
        Args:
            template_id: Template identifier
            base_version: Base version number
            
        Returns:
            Tuple of (version, validation history)
        """
        # Create version with validation rules
        template = self.create_template(
            name="Validation Test",
            version=base_version,
            data={
                "validation_rules": [
                    {"name": "rule1", "severity": "error"},
                    {"name": "rule2", "severity": "warning"}
                ]
            }
        )
        
        change = self.create_change(
            change_type=ChangeType.CREATED,
            description="Validation test version"
        )
        
        version = self.manager.add_version(template_id, template, change)
        
        # Create validation history
        history = []
        for i in range(3):
            result = {
                "timestamp": datetime.now().isoformat(),
                "version": f"{base_version}.{i}",
                "is_valid": i > 0,  # First validation fails
                "results": [
                    {
                        "severity": "error" if i == 0 else "info",
                        "message": f"Validation {i+1}",
                        "details": f"Details for validation {i+1}"
                    }
                ]
            }
            history.append(result)
        
        return version, history
    
    def cleanup(self):
        """Clean up test environment."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

class VersionTestData:
    """Test data for versioning tests."""
    
    @staticmethod
    def get_sample_template_data() -> Dict[str, Any]:
        """Get sample template data.
        
        Returns:
            Sample template data
        """
        return {
            "name": "Sample Template",
            "description": "Sample template description",
            "version": "1.0.0",
            "format_version": "1.0",
            "schema_version": "1.0",
            "data": {
                "key1": "value1",
                "key2": "value2",
                "nested": {
                    "key3": "value3"
                }
            }
        }
    
    @staticmethod
    def get_sample_validation_rules() -> List[Dict[str, Any]]:
        """Get sample validation rules.
        
        Returns:
            Sample validation rules
        """
        return [
            {
                "name": "rule1",
                "description": "First validation rule",
                "severity": "error",
                "condition": "template.version >= '1.0.0'"
            },
            {
                "name": "rule2",
                "description": "Second validation rule",
                "severity": "warning",
                "condition": "template.format_version == '1.0'"
            }
        ]
    
    @staticmethod
    def get_sample_export_data() -> Dict[str, Any]:
        """Get sample export data.
        
        Returns:
            Sample export data
        """
        return {
            "version": {
                "metadata": {
                    "name": "Exported Template",
                    "version": "1.0.0",
                    "format_version": "1.0",
                    "schema_version": "1.0"
                },
                "data": {
                    "key": "value"
                }
            },
            "validation_results": {
                "is_valid": True,
                "results": [
                    {
                        "severity": "info",
                        "message": "Export validation",
                        "details": "Export validation details"
                    }
                ]
            }
        }
    
    @staticmethod
    def get_sample_branch_data() -> Dict[str, Any]:
        """Get sample branch data.
        
        Returns:
            Sample branch data
        """
        return {
            "main": {
                "name": "main",
                "versions": [
                    {"version": "1.0.0", "data": "main1"},
                    {"version": "1.0.1", "data": "main2"}
                ]
            },
            "feature": {
                "name": "feature",
                "versions": [
                    {"version": "1.0.0-feature.0", "data": "feature1"},
                    {"version": "1.0.0-feature.1", "data": "feature2"}
                ]
            }
        }
    
    @staticmethod
    def get_sample_merge_data() -> Dict[str, Any]:
        """Get sample merge data.
        
        Returns:
            Sample merge data
        """
        return {
            "base": {
                "version": "1.0.0",
                "data": {"key": "base_value"}
            },
            "feature": {
                "version": "1.0.0-feature",
                "data": {
                    "key": "feature_value",
                    "new_key": "new_value"
                }
            },
            "merged": {
                "version": "1.0.1",
                "data": {
                    "key": "merged_value",
                    "new_key": "new_value",
                    "merged": True
                }
            }
        }
    
    @staticmethod
    def get_sample_rollback_data() -> Dict[str, Any]:
        """Get sample rollback data.
        
        Returns:
            Sample rollback data
        """
        return {
            "versions": [
                {
                    "version": "1.0.0",
                    "data": {"key": "value1", "changes": ["change1"]}
                },
                {
                    "version": "1.0.1",
                    "data": {"key": "value2", "changes": ["change1", "change2"]}
                },
                {
                    "version": "1.0.2",
                    "data": {"key": "value3", "changes": ["change1", "change2", "change3"]}
                }
            ],
            "rollback_target": "1.0.0"
        } 
