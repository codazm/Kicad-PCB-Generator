"""Integration tests for versioning and UI components."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import wx
import os
import shutil
from datetime import datetime

from kicad_pcb_generator.core.templates.template_versioning import (
    TemplateVersionManager,
    TemplateVersion,
    TemplateChange,
    ChangeType
)
from kicad_pcb_generator.ui.dialogs.template_validation_dialog import (
    TemplateValidationDialog,
    ValidationResultPanel,
    ValidationHistoryDialog
)
from kicad_pcb_generator.ui.dialogs.template_version_dialog import (
    TemplateVersionDialog,
    VersionHistoryPanel
)
from kicad_pcb_generator.tests.core.templates.test_versioning.fixtures import (
    VersionTestFixture,
    VersionTestData
)

class TestVersionUIIntegration(unittest.TestCase):
    """Test integration between versioning and UI components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.fixture = VersionTestFixture()
        self.test_data = VersionTestData()
        
        # Create test template and version
        self.template = self.fixture.create_template()
        self.change = self.fixture.create_change()
        self.version = self.fixture.manager.add_version(
            "test_template",
            self.template,
            self.change
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.fixture.cleanup()
        self.app.Destroy()
    
    def test_validation_dialog_integration(self):
        """Test integration with validation dialog."""
        # Create validation results
        validation_results = [
            {
                "severity": "error",
                "message": "Validation error",
                "details": "Error details"
            },
            {
                "severity": "warning",
                "message": "Validation warning",
                "details": "Warning details"
            }
        ]
        
        # Create and show validation dialog
        dialog = TemplateValidationDialog(
            None,
            "Test Template",
            self.version.version_id,
            validation_results
        )
        
        # Test dialog components
        self.assertIsNotNone(dialog.result_panel)
        self.assertEqual(dialog.GetTitle(), "Template Validation")
        
        # Test result panel
        result_panel = dialog.result_panel
        self.assertEqual(len(result_panel.results), 2)
        self.assertEqual(result_panel.results[0]["severity"], "error")
        self.assertEqual(result_panel.results[1]["severity"], "warning")
    
    def test_version_dialog_integration(self):
        """Test integration with version dialog."""
        # Create version chain
        versions = self.fixture.create_version_chain("test_template", 3)
        
        # Create and show version dialog
        dialog = TemplateVersionDialog(
            None,
            "Test Template",
            versions
        )
        
        # Test dialog components
        self.assertIsNotNone(dialog.history_panel)
        self.assertEqual(dialog.GetTitle(), "Template Versions")
        
        # Test history panel
        history_panel = dialog.history_panel
        self.assertEqual(len(history_panel.versions), 3)
        self.assertEqual(history_panel.versions[0].metadata["version"], "1.0.0")
    
    def test_validation_history_dialog_integration(self):
        """Test integration with validation history dialog."""
        # Create validation history
        history = self.fixture.create_validation_history(
            "test_template",
            self.version.version_id,
            3
        )
        
        # Create and show history dialog
        dialog = ValidationHistoryDialog(
            None,
            "Test Template",
            self.version.version_id,
            history
        )
        
        # Test dialog components
        self.assertIsNotNone(dialog.history_list)
        self.assertEqual(dialog.GetTitle(), "Validation History")
        
        # Test history list
        self.assertEqual(dialog.history_list.GetItemCount(), 3)
    
    def test_version_conflict_dialog_integration(self):
        """Test integration with version conflict dialog."""
        # Create conflicting versions
        versions = self.fixture.create_conflicting_versions("test_template")
        
        # Mock conflict resolution
        with patch.object(
            self.fixture.manager,
            'resolve_version_conflict',
            return_value=versions[1]
        ):
            # Create and show conflict dialog
            dialog = TemplateVersionDialog(
                None,
                "Test Template",
                versions,
                show_conflict=True
            )
            
            # Test dialog components
            self.assertIsNotNone(dialog.conflict_panel)
            self.assertEqual(dialog.GetTitle(), "Version Conflict")
            
            # Test conflict resolution
            dialog.conflict_panel.resolve_conflict("merge")
            self.assertEqual(
                self.fixture.manager.resolve_version_conflict.call_count,
                1
            )
    
    def test_version_migration_dialog_integration(self):
        """Test integration with version migration dialog."""
        # Create migration chain
        versions = self.fixture.create_migration_chain("test_template")
        
        # Mock migration
        with patch.object(
            self.fixture.manager,
            'migrate_version',
            return_value=versions[1]
        ):
            # Create and show migration dialog
            dialog = TemplateVersionDialog(
                None,
                "Test Template",
                versions,
                show_migration=True
            )
            
            # Test dialog components
            self.assertIsNotNone(dialog.migration_panel)
            self.assertEqual(dialog.GetTitle(), "Version Migration")
            
            # Test migration
            dialog.migration_panel.migrate_version()
            self.assertEqual(
                self.fixture.manager.migrate_version.call_count,
                1
            )
    
    def test_version_export_dialog_integration(self):
        """Test integration with version export dialog."""
        # Create export data
        export_data = self.test_data.get_sample_export_data()
        
        # Mock export
        with patch.object(
            self.fixture.manager,
            'export_version',
            return_value=export_data
        ):
            # Create and show export dialog
            dialog = TemplateVersionDialog(
                None,
                "Test Template",
                [self.version],
                show_export=True
            )
            
            # Test dialog components
            self.assertIsNotNone(dialog.export_panel)
            self.assertEqual(dialog.GetTitle(), "Export Version")
            
            # Test export
            dialog.export_panel.export_version()
            self.assertEqual(
                self.fixture.manager.export_version.call_count,
                1
            )
    
    def test_version_import_dialog_integration(self):
        """Test integration with version import dialog."""
        # Create import data
        import_data = self.test_data.get_sample_export_data()
        
        # Mock import
        with patch.object(
            self.fixture.manager,
            'import_version',
            return_value=self.version
        ):
            # Create and show import dialog
            dialog = TemplateVersionDialog(
                None,
                "Test Template",
                [],
                show_import=True
            )
            
            # Test dialog components
            self.assertIsNotNone(dialog.import_panel)
            self.assertEqual(dialog.GetTitle(), "Import Version")
            
            # Test import
            dialog.import_panel.import_version(import_data)
            self.assertEqual(
                self.fixture.manager.import_version.call_count,
                1
            )

if __name__ == "__main__":
    unittest.main() 