"""Tests for template version view."""

import unittest
from unittest.mock import Mock, patch
import wx
from datetime import datetime

from kicad_pcb_generator.core.templates.template_integration import TemplateIntegrationManager
from kicad_pcb_generator.ui.views.template_version_view import TemplateVersionView

class TestTemplateVersionView(unittest.TestCase):
    """Test cases for template version view."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.integration_manager = Mock(spec=TemplateIntegrationManager)
        self.view = TemplateVersionView(self.frame, self.integration_manager)
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.frame.Destroy()
        self.app.Destroy()
        
    def test_init(self):
        """Test view initialization."""
        self.assertIsNotNone(self.view.version_grid)
        self.assertIsNotNone(self.view.changes_text)
        self.assertIsNotNone(self.view.deps_list)
        self.assertIsNotNone(self.view.validation_text)
        
    def test_load_versions(self):
        """Test loading versions into grid."""
        # Mock version history
        versions = [
            Mock(
                version="v1",
                author="Test Author",
                date=datetime.now(),
                description="Test version",
                validation_status=True,
                changes=[],
                dependencies=[]
            )
        ]
        self.integration_manager.get_template_history.return_value = versions
        
        # Load versions
        self.view._load_versions()
        
        # Check grid
        self.assertEqual(self.view.version_grid.GetNumberRows(), 1)
        self.assertEqual(self.view.version_grid.GetCellValue(0, 0), "v1")
        self.assertEqual(self.view.version_grid.GetCellValue(0, 1), "Test Author")
        self.assertEqual(self.view.version_grid.GetCellValue(0, 3), "Test version")
        self.assertEqual(self.view.version_grid.GetCellValue(0, 4), "Valid")
        
    def test_version_selection(self):
        """Test version selection."""
        # Mock version data
        version_data = {
            "version": Mock(
                changes=[
                    Mock(type="create", description="Initial version")
                ],
                dependencies=[
                    Mock(name="dep1", version="1.0", type="library")
                ]
            ),
            "validation_results": {
                "board_validation": ["Board is valid"],
                "rule_validation": ["Rules are valid"]
            }
        }
        self.integration_manager.get_template_version.return_value = version_data
        
        # Select version
        self.view.version_grid.AppendRows(1)
        self.view.version_grid.SetCellValue(0, 0, "v1")
        self.view._on_version_selected(Mock(GetRow=lambda: 0))
        
        # Check details
        self.assertEqual(
            self.view.changes_text.GetValue(),
            "create: Initial version"
        )
        self.assertEqual(self.view.deps_list.GetItemCount(), 1)
        self.assertEqual(self.view.deps_list.GetItem(0, 0).GetText(), "dep1")
        self.assertEqual(self.view.deps_list.GetItem(0, 1).GetText(), "1.0")
        self.assertEqual(self.view.deps_list.GetItem(0, 2).GetText(), "library")
        self.assertIn("Board Validation:", self.view.validation_text.GetValue())
        self.assertIn("Board is valid", self.view.validation_text.GetValue())
        self.assertIn("Rule Validation:", self.view.validation_text.GetValue())
        self.assertIn("Rules are valid", self.view.validation_text.GetValue())
        
    @patch("kicad_pcb_generator.ui.views.template_version_view.CreateVersionDialog")
    def test_create_version(self, mock_dialog):
        """Test creating a new version."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_OK
        
        # Create version
        self.view._on_create_version(Mock())
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check versions were reloaded
        self.integration_manager.get_template_history.assert_called()
        
    @patch("kicad_pcb_generator.ui.views.template_version_view.CompareVersionsDialog")
    def test_compare_versions(self, mock_dialog):
        """Test comparing versions."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Add versions to grid
        self.view.version_grid.AppendRows(2)
        self.view.version_grid.SetCellValue(0, 0, "v1")
        self.view.version_grid.SetCellValue(1, 0, "v2")
        
        # Compare versions
        self.view._on_compare_versions(Mock())
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
    @patch("kicad_pcb_generator.ui.views.template_version_view.RollbackDialog")
    def test_rollback_version(self, mock_dialog):
        """Test rolling back to a version."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.ShowModal.return_value = wx.ID_YES
        
        # Add versions to grid
        self.view.version_grid.AppendRows(2)
        self.view.version_grid.SetCellValue(0, 0, "v1")
        self.view.version_grid.SetCellValue(1, 0, "v2")
        
        # Rollback version
        self.view._on_rollback(Mock())
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check versions were reloaded
        self.integration_manager.get_template_history.assert_called()
        
    @patch("kicad_pcb_generator.ui.views.template_version_view.ValidateVersionDialog")
    def test_validate_version(self, mock_dialog):
        """Test validating a version."""
        # Mock dialog
        mock_dialog_instance = Mock()
        mock_dialog.return_value = mock_dialog_instance
        
        # Add version to grid
        self.view.version_grid.AppendRows(1)
        self.view.version_grid.SetCellValue(0, 0, "v1")
        self.view.version_grid.SelectRow(0)
        
        # Validate version
        self.view._on_validate(Mock())
        
        # Check dialog was shown
        mock_dialog.assert_called_once()
        mock_dialog_instance.ShowModal.assert_called_once()
        
        # Check versions were reloaded
        self.integration_manager.get_template_history.assert_called()
        
    def test_validate_no_selection(self):
        """Test validation with no version selected."""
        # Validate without selection
        self.view._on_validate(Mock())
        
        # Check error message was shown
        self.integration_manager.get_template_history.assert_not_called()

if __name__ == "__main__":
    unittest.main() 