"""
Tests for the validation settings dialog.
"""
import unittest
from unittest.mock import Mock, patch
import wx

from kicad_pcb_generator.ui.dialogs.validation_settings_dialog import ValidationSettingsDialog, RuleConfig
from kicad_pcb_generator.utils.config.settings import Settings, ValidationSeverity
from kicad_pcb_generator.utils.logging.logger import Logger

class TestValidationSettingsDialog(unittest.TestCase):
    """Test cases for the ValidationSettingsDialog class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = wx.App()
        self.settings = Mock(spec=Settings)
        self.logger = Mock(spec=Logger)
        
        # Mock settings data
        self.settings.get.return_value = {
            "safety": {
                "min_clearance": {
                    "enabled": True,
                    "severity": "error",
                    "parameters": {
                        "min_clearance": 0.2
                    },
                    "description": "Minimum clearance between components and traces",
                    "category": "safety"
                }
            },
            "audio": {
                "signal_isolation": {
                    "enabled": True,
                    "severity": "error",
                    "parameters": {
                        "min_spacing": 0.2,
                        "require_ground_plane": True
                    },
                    "description": "Signal isolation requirements for audio traces",
                    "category": "audio"
                }
            },
            "manufacturing": {
                "drill_sizes": {
                    "enabled": True,
                    "severity": "error",
                    "parameters": {
                        "min_drill": 0.2,
                        "max_drill": 6.0
                    },
                    "description": "Drill size requirements for manufacturing",
                    "category": "manufacturing"
                }
            }
        }
        
        self.dialog = ValidationSettingsDialog(
            parent=None,
            settings=self.settings,
            logger=self.logger
        )
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.dialog.Destroy()
        self.app.Destroy()
        
    def test_init(self):
        """Test dialog initialization."""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(len(self.dialog.rule_configs), 3)
        
    def test_rule_configs(self):
        """Test rule configuration loading."""
        # Check safety rule
        safety_rule = self.dialog.rule_configs.get("safety.min_clearance")
        self.assertIsNotNone(safety_rule)
        self.assertEqual(safety_rule.name, "min_clearance")
        self.assertEqual(safety_rule.category, "safety")
        self.assertTrue(safety_rule.enabled)
        self.assertEqual(safety_rule.severity, ValidationSeverity.ERROR)
        self.assertEqual(safety_rule.parameters["min_clearance"], 0.2)
        
        # Check audio rule
        audio_rule = self.dialog.rule_configs.get("audio.signal_isolation")
        self.assertIsNotNone(audio_rule)
        self.assertEqual(audio_rule.name, "signal_isolation")
        self.assertEqual(audio_rule.category, "audio")
        self.assertTrue(audio_rule.enabled)
        self.assertEqual(audio_rule.severity, ValidationSeverity.ERROR)
        self.assertEqual(audio_rule.parameters["min_spacing"], 0.2)
        self.assertTrue(audio_rule.parameters["require_ground_plane"])
        
    def test_save_settings(self):
        """Test saving settings."""
        # Mock save_config method
        self.settings.save_config = Mock()
        
        # Trigger save
        event = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_SAVE)
        self.dialog._on_save(event)
        
        # Verify settings were updated
        self.settings.set.assert_called()
        self.settings.save_config.assert_called_once()
        
    def test_reset_settings(self):
        """Test resetting settings."""
        # Mock reset_to_defaults method
        self.settings.reset_to_defaults = Mock()
        
        # Mock message box to return YES
        with patch('wx.MessageBox', return_value=wx.YES):
            # Trigger reset
            event = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_RESET)
            self.dialog._on_reset(event)
            
            # Verify settings were reset
            self.settings.reset_to_defaults.assert_called_once()
            
    def test_cancel(self):
        """Test canceling dialog."""
        # Trigger cancel
        event = wx.CommandEvent(wx.wxEVT_BUTTON, wx.ID_CANCEL)
        self.dialog._on_cancel(event)
        
        # Verify dialog was closed
        self.assertFalse(self.dialog.IsShown())
        
if __name__ == '__main__':
    unittest.main() 