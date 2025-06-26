"""Tests for template version integration."""

import unittest
from unittest.mock import Mock, patch
import wx
from datetime import datetime

from kicad_pcb_generator.core.templates.template_integration import TemplateIntegrationManager
from kicad_pcb_generator.core.templates.template_versioning import TemplateVersion
from kicad_pcb_generator.ui.integration.template_version_integration import TemplateVersionIntegration

class TestTemplateVersionIntegration(unittest.TestCase):
    """Test cases for template version integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.integration_manager = Mock(spec=TemplateIntegrationManager)
        self.integration = TemplateVersionIntegration(self.integration_manager)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.frame.Destroy()
        self.app.Destroy()
        
    def test_init(self):
        """Test initialization."""
        self.assertIsNotNone(self.integration.integration_manager)
        self.assertIsNotNone(self.integration.logger)
        
    @patch("kicad_pcb_generator.ui.integration.template_version_integration.CreateVersionDialog")
    def test_create_version_dialog(self, mock_dialog):
        """Test version creation dialog."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        mock_dialog_instance.get_version_data.return_value = {
            "author": "Test Author",
            "description": "Test version"
        }
        
        # Mock version
        version = Mock(spec=TemplateVersion)
        self.integration_manager.create_template_version.return_value = version
        
        # Create version
        callback = Mock()
        self.integration.create_version_dialog(self.frame, "test_template", callback)
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check version was created
        self.integration_manager.create_template_version.assert_called_once()
        callback.assert_called_once_with(version)
        
    @patch("kicad_pcb_generator.ui.integration.template_version_integration.CompareVersionsDialog")
    def test_compare_versions_dialog(self, mock_dialog):
        """Test version comparison dialog."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Mock versions
        versions = [
            Mock(spec=TemplateVersion),
            Mock(spec=TemplateVersion)
        ]
        
        # Compare versions
        self.integration.compare_versions_dialog(self.frame, "test_template", versions)
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
    @patch("kicad_pcb_generator.ui.integration.template_version_integration.RollbackDialog")
    def test_rollback_dialog(self, mock_dialog):
        """Test version rollback dialog."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_YES
        
        # Mock version
        version = Mock(spec=TemplateVersion)
        version.version = "v1"
        
        # Rollback version
        callback = Mock()
        self.integration.rollback_dialog(self.frame, "test_template", version, callback)
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check version was rolled back
        self.integration_manager.rollback_version.assert_called_once_with("test_template", "v1")
        callback.assert_called_once()
        
    @patch("kicad_pcb_generator.ui.integration.template_version_integration.ValidateVersionDialog")
    def test_validate_version_dialog(self, mock_dialog):
        """Test version validation dialog."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        
        # Mock version
        version = Mock(spec=TemplateVersion)
        version.version = "v1"
        
        # Mock validation results
        results = {
            "board_validation": ["Board is valid"],
            "rule_validation": ["Rules are valid"]
        }
        self.integration_manager.validate_template_version.return_value = results
        
        # Validate version
        callback = Mock()
        self.integration.validate_version_dialog(self.frame, "test_template", version, callback)
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check version was validated
        self.integration_manager.validate_template_version.assert_called_once_with(
            "test_template",
            "v1"
        )
        callback.assert_called_once_with(results)
        
    def test_get_version_data(self):
        """Test getting version data."""
        # Mock version data
        version = Mock(spec=TemplateVersion)
        version.changes = [Mock(type="create", description="Initial version")]
        version.dependencies = [Mock(name="dep1", version="1.0", type="library")]
        
        validation_results = {
            "board_validation": ["Board is valid"],
            "rule_validation": ["Rules are valid"]
        }
        
        self.integration_manager.get_template_version.return_value = {
            "version": version,
            "validation_results": validation_results
        }
        
        # Get version data
        data = self.integration.get_version_data("test_template", "v1")
        
        # Check data
        self.assertEqual(data["version"], version)
        self.assertEqual(data["changes"], version.changes)
        self.assertEqual(data["dependencies"], version.dependencies)
        self.assertEqual(data["validation_results"], validation_results)
        
    def test_get_version_history(self):
        """Test getting version history."""
        # Mock versions
        versions = [
            Mock(
                spec=TemplateVersion,
                version="v1",
                author="Test Author",
                date=datetime.now(),
                description="Test version",
                validation_status=True
            )
        ]
        self.integration_manager.get_template_history.return_value = versions
        
        # Get version history
        history = self.integration.get_version_history("test_template")
        
        # Check history
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["version"], "v1")
        self.assertEqual(history[0]["author"], "Test Author")
        self.assertEqual(history[0]["description"], "Test version")
        self.assertTrue(history[0]["validation_status"])
        
    def test_update_version_grid(self):
        """Test updating version grid."""
        # Create grid
        grid = wx.grid.Grid(self.frame)
        grid.CreateGrid(0, 5)
        
        # Set column labels
        grid.SetColLabelValue(0, "Version")
        grid.SetColLabelValue(1, "Author")
        grid.SetColLabelValue(2, "Date")
        grid.SetColLabelValue(3, "Description")
        grid.SetColLabelValue(4, "Status")
        
        # Mock versions
        versions = [
            {
                "version": "v1",
                "author": "Test Author",
                "date": datetime.now(),
                "description": "Test version",
                "validation_status": True
            }
        ]
        
        # Update grid
        self.integration.update_version_grid(grid, versions)
        
        # Check grid
        self.assertEqual(grid.GetNumberRows(), 1)
        self.assertEqual(grid.GetCellValue(0, 0), "v1")
        self.assertEqual(grid.GetCellValue(0, 1), "Test Author")
        self.assertEqual(grid.GetCellValue(0, 3), "Test version")
        self.assertEqual(grid.GetCellValue(0, 4), "Valid")
        
    def test_update_version_details(self):
        """Test updating version details."""
        # Create controls
        changes_text = wx.TextCtrl(self.frame)
        deps_list = wx.ListCtrl(self.frame, style=wx.LC_REPORT)
        deps_list.InsertColumn(0, "Name")
        deps_list.InsertColumn(1, "Version")
        deps_list.InsertColumn(2, "Type")
        validation_text = wx.TextCtrl(self.frame, style=wx.TE_MULTILINE)
        
        # Mock version data
        version_data = {
            "changes": [
                Mock(type="create", description="Initial version")
            ],
            "dependencies": [
                Mock(name="dep1", version="1.0", type="library")
            ],
            "validation_results": {
                "board_validation": ["Board is valid"],
                "rule_validation": ["Rules are valid"]
            }
        }
        
        # Update details
        self.integration.update_version_details(
            changes_text,
            deps_list,
            validation_text,
            version_data
        )
        
        # Check changes
        self.assertEqual(changes_text.GetValue(), "create: Initial version")
        
        # Check dependencies
        self.assertEqual(deps_list.GetItemCount(), 1)
        self.assertEqual(deps_list.GetItem(0, 0).GetText(), "dep1")
        self.assertEqual(deps_list.GetItem(0, 1).GetText(), "1.0")
        self.assertEqual(deps_list.GetItem(0, 2).GetText(), "library")
        
        # Check validation
        validation = validation_text.GetValue()
        self.assertIn("Board Validation:", validation)
        self.assertIn("Board is valid", validation)
        self.assertIn("Rule Validation:", validation)
        self.assertIn("Rules are valid", validation)

if __name__ == "__main__":
    unittest.main() 
