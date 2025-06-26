"""
Tests for the constraint editor dialog.
"""

import unittest
from unittest.mock import Mock, patch
import wx
from core.rules.rule_management import RuleConstraint
from ui.dialogs.constraint_editor_dialog import ConstraintEditorDialog

class TestConstraintEditorDialog(unittest.TestCase):
    """Test cases for the constraint editor dialog."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        self.dialog = ConstraintEditorDialog(self.frame)
    
    def tearDown(self):
        """Clean up test environment."""
        self.dialog.Destroy()
        self.frame.Destroy()
        self.app.Destroy()
    
    def test_init(self):
        """Test dialog initialization."""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.GetTitle(), "Edit Constraint")
        self.assertIsNone(self.dialog.get_constraint())
    
    def test_load_range_constraint(self):
        """Test loading a range constraint."""
        constraint = RuleConstraint(min_value=0.0, max_value=10.0)
        dialog = ConstraintEditorDialog(self.frame, constraint)
        
        # Check that range page is selected
        self.assertEqual(dialog.notebook.GetSelection(), 0)
        
        # Check values
        self.assertEqual(dialog.min_value.GetValue(), "0.0")
        self.assertEqual(dialog.max_value.GetValue(), "10.0")
    
    def test_load_enum_constraint(self):
        """Test loading an enum constraint."""
        constraint = RuleConstraint(allowed_values=["A", "B", "C"])
        dialog = ConstraintEditorDialog(self.frame, constraint)
        
        # Check that enum page is selected
        self.assertEqual(dialog.notebook.GetSelection(), 1)
        
        # Check values
        self.assertEqual(dialog.values_list.GetItems(), ["A", "B", "C"])
    
    def test_load_pattern_constraint(self):
        """Test loading a pattern constraint."""
        constraint = RuleConstraint(regex_pattern=r"\d+")
        dialog = ConstraintEditorDialog(self.frame, constraint)
        
        # Check that pattern page is selected
        self.assertEqual(dialog.notebook.GetSelection(), 2)
        
        # Check value
        self.assertEqual(dialog.pattern.GetValue(), r"\d+")
    
    def test_load_custom_constraint(self):
        """Test loading a custom constraint."""
        validator = "def validate(value): return value > 0"
        constraint = RuleConstraint(custom_validator=validator)
        dialog = ConstraintEditorDialog(self.frame, constraint)
        
        # Check that custom page is selected
        self.assertEqual(dialog.notebook.GetSelection(), 3)
        
        # Check value
        self.assertEqual(dialog.validator.GetValue(), validator)
    
    def test_save_range_constraint(self):
        """Test saving a range constraint."""
        # Set values
        self.dialog.notebook.SetSelection(0)
        self.dialog.min_value.SetValue("0.0")
        self.dialog.max_value.SetValue("10.0")
        
        # Trigger save
        self.dialog._on_save(Mock())
        
        # Check result
        constraint = self.dialog.get_constraint()
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.min_value, 0.0)
        self.assertEqual(constraint.max_value, 10.0)
    
    def test_save_enum_constraint(self):
        """Test saving an enum constraint."""
        # Set values
        self.dialog.notebook.SetSelection(1)
        self.dialog.values_list.SetItems(["A", "B", "C"])
        
        # Trigger save
        self.dialog._on_save(Mock())
        
        # Check result
        constraint = self.dialog.get_constraint()
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.allowed_values, ["A", "B", "C"])
    
    def test_save_pattern_constraint(self):
        """Test saving a pattern constraint."""
        # Set values
        self.dialog.notebook.SetSelection(2)
        self.dialog.pattern.SetValue(r"\d+")
        
        # Trigger save
        self.dialog._on_save(Mock())
        
        # Check result
        constraint = self.dialog.get_constraint()
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.regex_pattern, r"\d+")
    
    def test_save_custom_constraint(self):
        """Test saving a custom constraint."""
        # Set values
        self.dialog.notebook.SetSelection(3)
        validator = "def validate(value): return value > 0"
        self.dialog.validator.SetValue(validator)
        
        # Trigger save
        self.dialog._on_save(Mock())
        
        # Check result
        constraint = self.dialog.get_constraint()
        self.assertIsNotNone(constraint)
        self.assertEqual(constraint.custom_validator, validator)
    
    def test_add_enum_value(self):
        """Test adding a value to the enum list."""
        with patch('wx.GetTextFromUser', return_value="D"):
            self.dialog._on_add_value(Mock())
            self.assertEqual(self.dialog.values_list.GetItems(), ["D"])
    
    def test_remove_enum_value(self):
        """Test removing values from the enum list."""
        # Add values
        self.dialog.values_list.SetItems(["A", "B", "C"])
        
        # Select and remove
        self.dialog.values_list.SetSelection(1)  # Select "B"
        self.dialog._on_remove_value(Mock())
        
        # Check result
        self.assertEqual(self.dialog.values_list.GetItems(), ["A", "C"])
    
    def test_test_pattern(self):
        """Test pattern testing functionality."""
        # Set pattern and test value
        self.dialog.pattern.SetValue(r"\d+")
        self.dialog.test_value.SetValue("123")
        
        # Test pattern
        self.dialog._on_test_pattern(Mock())
        
        # Check result
        self.assertEqual(self.dialog.test_result.GetLabel(), "Pattern matches!")
        self.assertEqual(self.dialog.test_result.GetForegroundColour(), wx.GREEN)
    
    def test_test_custom_validator(self):
        """Test custom validator testing functionality."""
        # Set validator and test value
        validator = "def validate(value): return value > 0"
        self.dialog.validator.SetValue(validator)
        self.dialog.custom_test_value.SetValue("5")
        
        # Test validator
        self.dialog._on_test_custom(Mock())
        
        # Check result
        self.assertEqual(self.dialog.custom_test_result.GetLabel(), "Validation passed!")
        self.assertEqual(self.dialog.custom_test_result.GetForegroundColour(), wx.GREEN)
    
    def test_cancel(self):
        """Test canceling the dialog."""
        # Trigger cancel
        self.dialog._on_cancel(Mock())
        
        # Check result
        self.assertIsNone(self.dialog.get_constraint())
    
    def test_validation_errors(self):
        """Test validation error handling."""
        # Test empty range
        self.dialog.notebook.SetSelection(0)
        self.dialog._on_save(Mock())
        self.assertIsNone(self.dialog.get_constraint())
        
        # Test empty enum
        self.dialog.notebook.SetSelection(1)
        self.dialog._on_save(Mock())
        self.assertIsNone(self.dialog.get_constraint())
        
        # Test empty pattern
        self.dialog.notebook.SetSelection(2)
        self.dialog._on_save(Mock())
        self.assertIsNone(self.dialog.get_constraint())
        
        # Test empty custom validator
        self.dialog.notebook.SetSelection(3)
        self.dialog._on_save(Mock())
        self.assertIsNone(self.dialog.get_constraint())
    
    def test_invalid_values(self):
        """Test handling of invalid values."""
        # Test invalid range values
        self.dialog.notebook.SetSelection(0)
        self.dialog.min_value.SetValue("invalid")
        self.dialog._on_save(Mock())
        self.assertIsNone(self.dialog.get_constraint())
        
        # Test invalid pattern
        self.dialog.notebook.SetSelection(2)
        self.dialog.pattern.SetValue("[invalid")
        self.dialog._on_test_pattern(Mock())
        self.assertEqual(
            self.dialog.test_result.GetLabel(),
            "Invalid pattern: unterminated character set"
        )
        
        # Test invalid custom validator
        self.dialog.notebook.SetSelection(3)
        self.dialog.validator.SetValue("invalid python code")
        self.dialog._on_test_custom(Mock())
        self.assertTrue(
            self.dialog.custom_test_result.GetLabel().startswith("Error:")
        ) 