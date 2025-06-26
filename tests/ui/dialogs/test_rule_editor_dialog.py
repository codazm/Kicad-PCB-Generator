"""
Tests for the rule editor dialog.
"""
import unittest
from unittest.mock import Mock, patch
import wx

from ....core.validation.validation_results import (
    ValidationCategory,
    ValidationSeverity
)
from ....core.validation.validation_rule import ValidationRule, RuleType
from ....ui.dialogs.rule_editor_dialog import RuleEditorDialog, RuleConstraint

class TestRuleEditorDialog(unittest.TestCase):
    """Test cases for RuleEditorDialog."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = wx.App()
        self.frame = wx.Frame(None)
        
        # Create test rule
        self.test_rule = ValidationRule(
            name="Test Rule",
            description="Test rule description",
            category=ValidationCategory.SAFETY,
            rule_type=RuleType.DESIGN_RULES,
            severity=ValidationSeverity.ERROR,
            enabled=True,
            constraints={
                "param1": RuleConstraint(
                    min_value=0,
                    max_value=100,
                    allowed_values=None,
                    regex_pattern=None,
                    custom_validator=None
                ),
                "param2": RuleConstraint(
                    min_value=None,
                    max_value=None,
                    allowed_values=["value1", "value2"],
                    regex_pattern=None,
                    custom_validator=None
                )
            },
            dependencies={"rule1", "rule2"}
        )
        
    def tearDown(self):
        """Clean up test environment."""
        self.frame.Destroy()
        self.app.Destroy()
        
    def test_init(self):
        """Test initialization."""
        # Test creating new rule
        dialog = RuleEditorDialog(self.frame)
        self.assertIsNotNone(dialog)
        self.assertIsNone(dialog.rule)
        self.assertEqual(dialog.GetTitle(), "Create Rule")
        
        # Test editing existing rule
        dialog = RuleEditorDialog(self.frame, self.test_rule)
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.rule, self.test_rule)
        self.assertEqual(dialog.GetTitle(), "Edit Rule")
        
    def test_load_rule(self):
        """Test loading rule into UI."""
        dialog = RuleEditorDialog(self.frame, self.test_rule)
        
        # Check basic info
        self.assertEqual(dialog.name_text.GetValue(), "Test Rule")
        self.assertEqual(dialog.desc_text.GetValue(), "Test rule description")
        self.assertEqual(
            dialog.category_choice.GetStringSelection(),
            ValidationCategory.SAFETY.value
        )
        self.assertEqual(
            dialog.type_choice.GetStringSelection(),
            RuleType.DESIGN_RULES.value
        )
        self.assertEqual(
            dialog.severity_choice.GetStringSelection(),
            ValidationSeverity.ERROR.value
        )
        self.assertTrue(dialog.enabled_check.GetValue())
        
        # Check constraints
        self.assertEqual(dialog.constraint_list.GetItemCount(), 2)
        self.assertEqual(
            dialog.constraint_list.GetItem(0, 0).GetText(),
            "param1"
        )
        self.assertEqual(
            dialog.constraint_list.GetItem(0, 1).GetText(),
            "Range"
        )
        self.assertEqual(
            dialog.constraint_list.GetItem(1, 0).GetText(),
            "param2"
        )
        self.assertEqual(
            dialog.constraint_list.GetItem(1, 1).GetText(),
            "Enum"
        )
        
        # Check dependencies
        self.assertEqual(dialog.dependency_list.GetItemCount(), 2)
        self.assertEqual(
            dialog.dependency_list.GetItem(0, 0).GetText(),
            "rule1"
        )
        self.assertEqual(
            dialog.dependency_list.GetItem(1, 0).GetText(),
            "rule2"
        )
        
    def test_add_constraint(self):
        """Test adding constraint."""
        dialog = RuleEditorDialog(self.frame)
        
        # Add constraint
        constraint = RuleConstraint(
            min_value=0,
            max_value=100
        )
        dialog.constraints["test_param"] = constraint
        dialog._add_constraint_to_list("test_param", constraint)
        
        # Check constraint list
        self.assertEqual(dialog.constraint_list.GetItemCount(), 1)
        self.assertEqual(
            dialog.constraint_list.GetItem(0, 0).GetText(),
            "test_param"
        )
        self.assertEqual(
            dialog.constraint_list.GetItem(0, 1).GetText(),
            "Range"
        )
        self.assertIn(
            "min=0",
            dialog.constraint_list.GetItem(0, 2).GetText()
        )
        self.assertIn(
            "max=100",
            dialog.constraint_list.GetItem(0, 2).GetText()
        )
        
    def test_remove_constraint(self):
        """Test removing constraint."""
        dialog = RuleEditorDialog(self.frame, self.test_rule)
        
        # Select first constraint
        dialog.constraint_list.Select(0)
        
        # Remove constraint
        dialog._on_remove_constraint(None)
        
        # Check constraint list
        self.assertEqual(dialog.constraint_list.GetItemCount(), 1)
        self.assertEqual(
            dialog.constraint_list.GetItem(0, 0).GetText(),
            "param2"
        )
        
    def test_add_dependency(self):
        """Test adding dependency."""
        dialog = RuleEditorDialog(self.frame)
        
        # Add dependency
        dialog._add_dependency_to_list("test_rule")
        
        # Check dependency list
        self.assertEqual(dialog.dependency_list.GetItemCount(), 1)
        self.assertEqual(
            dialog.dependency_list.GetItem(0, 0).GetText(),
            "test_rule"
        )
        
    def test_remove_dependency(self):
        """Test removing dependency."""
        dialog = RuleEditorDialog(self.frame, self.test_rule)
        
        # Select first dependency
        dialog.dependency_list.Select(0)
        
        # Remove dependency
        dialog._on_remove_dependency(None)
        
        # Check dependency list
        self.assertEqual(dialog.dependency_list.GetItemCount(), 1)
        self.assertEqual(
            dialog.dependency_list.GetItem(0, 0).GetText(),
            "rule2"
        )
        
    def test_save_rule(self):
        """Test saving rule."""
        dialog = RuleEditorDialog(self.frame)
        
        # Set basic info
        dialog.name_text.SetValue("New Rule")
        dialog.desc_text.SetValue("New rule description")
        dialog.category_choice.SetStringSelection(ValidationCategory.AUDIO.value)
        dialog.type_choice.SetStringSelection(RuleType.AUDIO.value)
        dialog.severity_choice.SetStringSelection(ValidationSeverity.WARNING.value)
        dialog.enabled_check.SetValue(True)
        
        # Add constraint
        constraint = RuleConstraint(
            min_value=0,
            max_value=100
        )
        dialog.constraints["test_param"] = constraint
        dialog._add_constraint_to_list("test_param", constraint)
        
        # Add dependency
        dialog._add_dependency_to_list("test_rule")
        
        # Save rule
        with patch.object(dialog, 'EndModal') as mock_end_modal:
            dialog._on_save(None)
            
            # Check rule creation
            self.assertEqual(dialog.name_text.GetValue(), "New Rule")
            self.assertEqual(dialog.desc_text.GetValue(), "New rule description")
            self.assertEqual(
                dialog.category_choice.GetStringSelection(),
                ValidationCategory.AUDIO.value
            )
            self.assertEqual(
                dialog.type_choice.GetStringSelection(),
                RuleType.AUDIO.value
            )
            self.assertEqual(
                dialog.severity_choice.GetStringSelection(),
                ValidationSeverity.WARNING.value
            )
            self.assertTrue(dialog.enabled_check.GetValue())
            
            # Check constraints
            self.assertEqual(len(dialog.constraints), 1)
            self.assertIn("test_param", dialog.constraints)
            
            # Check dependencies
            self.assertEqual(dialog.dependency_list.GetItemCount(), 1)
            self.assertEqual(
                dialog.dependency_list.GetItem(0, 0).GetText(),
                "test_rule"
            )
            
            # Check dialog close
            mock_end_modal.assert_called_once_with(wx.ID_SAVE) 