"""Template selection dialog for validation rules."""
import wx
from typing import Optional, Dict, Any, List

from ...templates.rule_template import RuleTemplate, RuleTemplateData
from ..validation_rule import ValidationRule

class TemplateSelectionDialog(wx.Dialog):
    """Dialog for selecting and customizing rule templates."""
    
    def __init__(self, parent: wx.Window, rule_template: RuleTemplate,
                 title: str = "Select Rule Template"):
        """Initialize dialog.
        
        Args:
            parent: Parent window
            rule_template: Rule template instance
            title: Dialog title
        """
        super().__init__(parent, title=title, size=(600, 400))
        self.rule_template = rule_template
        self.selected_template: Optional[RuleTemplateData] = None
        self.customized_rule: Optional[ValidationRule] = None
        
        self._init_ui()
        self._load_templates()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Template list
        list_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Template categories
        self.category_list = wx.ListBox(self, choices=[], size=(150, -1))
        self.category_list.Bind(wx.EVT_LISTBOX, self._on_category_selected)
        list_sizer.Add(self.category_list, 0, wx.EXPAND | wx.ALL, 5)
        
        # Template list
        self.template_list = wx.ListBox(self, choices=[], size=(200, -1))
        self.template_list.Bind(wx.EVT_LISTBOX, self._on_template_selected)
        list_sizer.Add(self.template_list, 0, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(list_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Template details
        details_sizer = wx.StaticBoxSizer(wx.VERTICAL, self, "Template Details")
        
        # Name
        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(wx.StaticText(self, label="Name:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.name_ctrl = wx.TextCtrl(self)
        name_sizer.Add(self.name_ctrl, 1, wx.EXPAND | wx.LEFT, 5)
        details_sizer.Add(name_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Description
        desc_sizer = wx.BoxSizer(wx.HORIZONTAL)
        desc_sizer.Add(wx.StaticText(self, label="Description:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.desc_ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 60))
        desc_sizer.Add(self.desc_ctrl, 1, wx.EXPAND | wx.LEFT, 5)
        details_sizer.Add(desc_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Category
        category_sizer = wx.BoxSizer(wx.HORIZONTAL)
        category_sizer.Add(wx.StaticText(self, label="Category:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.category_ctrl = wx.Choice(self, choices=[])
        category_sizer.Add(self.category_ctrl, 1, wx.EXPAND | wx.LEFT, 5)
        details_sizer.Add(category_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Type
        type_sizer = wx.BoxSizer(wx.HORIZONTAL)
        type_sizer.Add(wx.StaticText(self, label="Type:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.type_ctrl = wx.Choice(self, choices=[])
        type_sizer.Add(self.type_ctrl, 1, wx.EXPAND | wx.LEFT, 5)
        details_sizer.Add(type_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Severity
        severity_sizer = wx.BoxSizer(wx.HORIZONTAL)
        severity_sizer.Add(wx.StaticText(self, label="Severity:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.severity_ctrl = wx.Choice(self, choices=["error", "warning", "info"])
        severity_sizer.Add(self.severity_ctrl, 1, wx.EXPAND | wx.LEFT, 5)
        details_sizer.Add(severity_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        main_sizer.Add(details_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.ok_button = wx.Button(self, wx.ID_OK, "OK")
        self.ok_button.Disable()
        button_sizer.Add(self.ok_button, 0, wx.ALL, 5)
        
        cancel_button = wx.Button(self, wx.ID_CANCEL, "Cancel")
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
    
    def _load_templates(self):
        """Load available templates."""
        # Get unique categories
        categories = set()
        for template in self.rule_template.rule_templates.values():
            categories.add(template.category)
        
        self.category_list.Set(sorted(categories))
    
    def _on_category_selected(self, event):
        """Handle category selection."""
        category = self.category_list.GetStringSelection()
        if not category:
            return
        
        # Filter templates by category
        templates = [
            template.name
            for template in self.rule_template.rule_templates.values()
            if template.category == category
        ]
        
        self.template_list.Set(sorted(templates))
    
    def _on_template_selected(self, event):
        """Handle template selection."""
        template_name = self.template_list.GetStringSelection()
        if not template_name:
            return
        
        # Get template data
        template = self.rule_template.get_rule_template(template_name)
        if not template:
            return
        
        self.selected_template = template
        
        # Update controls
        self.name_ctrl.SetValue(template.name)
        self.desc_ctrl.SetValue(template.description)
        
        # Update category choice
        categories = self.category_list.GetStrings()
        self.category_ctrl.Set(categories)
        self.category_ctrl.SetStringSelection(template.category)
        
        # Update type choice
        types = ["constraint", "pattern", "custom"]
        self.type_ctrl.Set(types)
        self.type_ctrl.SetStringSelection(template.type)
        
        # Update severity choice
        self.severity_ctrl.SetStringSelection(template.severity)
        
        self.ok_button.Enable()
    
    def get_selected_rule(self) -> Optional[ValidationRule]:
        """Get the selected rule with customizations.
        
        Returns:
            Validation rule if successful
        """
        if not self.selected_template:
            return None
        
        try:
            # Create rule with customizations
            rule = self.rule_template.create_rule_from_template(
                self.selected_template.name,
                name=self.name_ctrl.GetValue(),
                description=self.desc_ctrl.GetValue(),
                category=self.category_ctrl.GetStringSelection(),
                type=self.type_ctrl.GetStringSelection(),
                severity=self.severity_ctrl.GetStringSelection()
            )
            
            return rule
            
        except Exception as e:
            wx.MessageBox(f"Failed to create rule: {e}", "Error",
                         wx.OK | wx.ICON_ERROR)
            return None 
