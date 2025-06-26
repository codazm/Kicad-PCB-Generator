"""Tests for template selection dialog."""
import pytest
import wx
from unittest.mock import MagicMock, patch

from kicad_pcb_generator.core.templates.rule_template import RuleTemplate, RuleTemplateData
from kicad_pcb_generator.core.validation.ui.template_selection_dialog import TemplateSelectionDialog

@pytest.fixture
def app():
    """Create wx application."""
    return wx.App()

@pytest.fixture
def frame(app):
    """Create test frame."""
    return wx.Frame(None)

@pytest.fixture
def rule_template():
    """Create rule template with test data."""
    template = RuleTemplate("test_path")
    
    # Add test templates
    template.create_rule_template(RuleTemplateData(
        name="test_rule1",
        description="Test rule 1",
        category="safety",
        type="constraint",
        severity="error",
        constraints={"min_width": 0.2},
        dependencies=[]
    ))
    
    template.create_rule_template(RuleTemplateData(
        name="test_rule2",
        description="Test rule 2",
        category="electrical",
        type="pattern",
        severity="warning",
        constraints={"max_current": 1.0},
        dependencies=[]
    ))
    
    return template

@pytest.fixture
def dialog(frame, rule_template):
    """Create template selection dialog."""
    return TemplateSelectionDialog(frame, rule_template)

def test_init(dialog):
    """Test dialog initialization."""
    assert dialog.rule_template is not None
    assert dialog.selected_template is None
    assert dialog.customized_rule is None

def test_load_templates(dialog):
    """Test loading templates."""
    # Check categories
    categories = dialog.category_list.GetStrings()
    assert "safety" in categories
    assert "electrical" in categories
    
    # Select category
    dialog.category_list.SetStringSelection("safety")
    dialog._on_category_selected(None)
    
    # Check templates
    templates = dialog.template_list.GetStrings()
    assert "test_rule1" in templates
    assert "test_rule2" not in templates

def test_template_selection(dialog):
    """Test template selection."""
    # Select category and template
    dialog.category_list.SetStringSelection("safety")
    dialog._on_category_selected(None)
    dialog.template_list.SetStringSelection("test_rule1")
    dialog._on_template_selected(None)
    
    # Check selected template
    assert dialog.selected_template is not None
    assert dialog.selected_template.name == "test_rule1"
    assert dialog.selected_template.description == "Test rule 1"
    
    # Check controls
    assert dialog.name_ctrl.GetValue() == "test_rule1"
    assert dialog.desc_ctrl.GetValue() == "Test rule 1"
    assert dialog.category_ctrl.GetStringSelection() == "safety"
    assert dialog.type_ctrl.GetStringSelection() == "constraint"
    assert dialog.severity_ctrl.GetStringSelection() == "error"
    
    # Check OK button
    assert dialog.ok_button.IsEnabled()

def test_get_selected_rule(dialog):
    """Test getting selected rule."""
    # Select template
    dialog.category_list.SetStringSelection("safety")
    dialog._on_category_selected(None)
    dialog.template_list.SetStringSelection("test_rule1")
    dialog._on_template_selected(None)
    
    # Customize rule
    dialog.name_ctrl.SetValue("custom_name")
    dialog.desc_ctrl.SetValue("custom description")
    dialog.category_ctrl.SetStringSelection("electrical")
    dialog.type_ctrl.SetStringSelection("pattern")
    dialog.severity_ctrl.SetStringSelection("warning")
    
    # Get rule
    rule = dialog.get_selected_rule()
    assert rule is not None
    assert rule.name == "custom_name"
    assert rule.description == "custom description"
    assert rule.category == "electrical"
    assert rule.type == "pattern"
    assert rule.severity == "warning"
    assert rule.constraints == {"min_width": 0.2}

def test_get_selected_rule_no_template(dialog):
    """Test getting selected rule with no template."""
    assert dialog.get_selected_rule() is None

def test_get_selected_rule_error(dialog):
    """Test getting selected rule with error."""
    # Select template
    dialog.category_list.SetStringSelection("safety")
    dialog._on_category_selected(None)
    dialog.template_list.SetStringSelection("test_rule1")
    dialog._on_template_selected(None)
    
    # Mock error
    with patch.object(dialog.rule_template, 'create_rule_from_template',
                     side_effect=Exception("Test error")):
        rule = dialog.get_selected_rule()
        assert rule is None 