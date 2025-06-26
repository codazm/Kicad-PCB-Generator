"""Enhanced ValidationResultDisplay with detailed view panel."""

import wx
import csv
import json
from typing import List, Optional
from kicad_pcb_generator.audio.validation.schematic.validator import SchematicValidationResult, SchematicValidationSeverity

class EnhancedValidationResultDisplay(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Validation Results", size=(1000, 800))
        self.results = []
        self.init_ui()

    def init_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Add search box
        search_box = wx.BoxSizer(wx.HORIZONTAL)
        self.search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        search_box.Add(self.search_ctrl, 1, wx.EXPAND)
        vbox.Add(search_box, 0, wx.EXPAND | wx.ALL, 5)

        # Add sort controls
        sort_box = wx.BoxSizer(wx.HORIZONTAL)
        self.sort_choice = wx.Choice(panel, choices=["Severity", "Component", "Message"])
        self.sort_choice.Bind(wx.EVT_CHOICE, self.on_sort)
        sort_box.Add(self.sort_choice, 0, wx.ALL, 5)
        vbox.Add(sort_box, 0, wx.EXPAND)

        # Split the window into two parts: results list and detailed view
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        # Add results list
        self.results_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.results_list.InsertColumn(0, "Severity")
        self.results_list.InsertColumn(1, "Message")
        self.results_list.InsertColumn(2, "Component")
        self.results_list.InsertColumn(3, "Net")
        self.results_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        hbox.Add(self.results_list, 1, wx.EXPAND | wx.ALL, 5)

        # Add detailed view panel
        self.details_panel = wx.Panel(panel)
        details_box = wx.BoxSizer(wx.VERTICAL)

        # Add notebook for different types of information
        self.notebook = wx.Notebook(self.details_panel)
        self.message_panel = wx.Panel(self.notebook)
        self.suggestion_panel = wx.Panel(self.notebook)
        self.documentation_panel = wx.Panel(self.notebook)
        self.example_panel = wx.Panel(self.notebook)
        self.affected_panel = wx.Panel(self.notebook)

        self.notebook.AddPage(self.message_panel, "Message")
        self.notebook.AddPage(self.suggestion_panel, "Suggestion")
        self.notebook.AddPage(self.documentation_panel, "Documentation")
        self.notebook.AddPage(self.example_panel, "Example")
        self.notebook.AddPage(self.affected_panel, "Affected")

        # Add text controls for each panel
        self.message_text = wx.TextCtrl(self.message_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.suggestion_text = wx.TextCtrl(self.suggestion_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.documentation_text = wx.TextCtrl(self.documentation_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.example_text = wx.TextCtrl(self.example_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.affected_text = wx.TextCtrl(self.affected_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)

        # Add text controls to panels
        message_box = wx.BoxSizer(wx.VERTICAL)
        message_box.Add(self.message_text, 1, wx.EXPAND)
        self.message_panel.SetSizer(message_box)

        suggestion_box = wx.BoxSizer(wx.VERTICAL)
        suggestion_box.Add(self.suggestion_text, 1, wx.EXPAND)
        self.suggestion_panel.SetSizer(suggestion_box)

        documentation_box = wx.BoxSizer(wx.VERTICAL)
        documentation_box.Add(self.documentation_text, 1, wx.EXPAND)
        self.documentation_panel.SetSizer(documentation_box)

        example_box = wx.BoxSizer(wx.VERTICAL)
        example_box.Add(self.example_text, 1, wx.EXPAND)
        self.example_panel.SetSizer(example_box)

        affected_box = wx.BoxSizer(wx.VERTICAL)
        affected_box.Add(self.affected_text, 1, wx.EXPAND)
        self.affected_panel.SetSizer(affected_box)

        details_box.Add(self.notebook, 1, wx.EXPAND)
        self.details_panel.SetSizer(details_box)
        hbox.Add(self.details_panel, 1, wx.EXPAND | wx.ALL, 5)

        vbox.Add(hbox, 1, wx.EXPAND)

        # Add export buttons
        export_box = wx.BoxSizer(wx.HORIZONTAL)
        self.export_csv_btn = wx.Button(panel, label="Export to CSV")
        self.export_csv_btn.Bind(wx.EVT_BUTTON, self.on_export_csv)
        self.export_json_btn = wx.Button(panel, label="Export to JSON")
        self.export_json_btn.Bind(wx.EVT_BUTTON, self.on_export_json)
        export_box.Add(self.export_csv_btn, 0, wx.ALL, 5)
        export_box.Add(self.export_json_btn, 0, wx.ALL, 5)
        vbox.Add(export_box, 0, wx.ALIGN_RIGHT)

        panel.SetSizer(vbox)

    def display_results(self, results):
        self.results = results
        self.update_results_list()

    def update_results_list(self):
        self.results_list.DeleteAllItems()
        for result in self.results:
            index = self.results_list.GetItemCount()
            self.results_list.InsertItem(index, result.severity.name.lower())
            self.results_list.SetItem(index, 1, result.message)
            self.results_list.SetItem(index, 2, result.component_ref or "")
            self.results_list.SetItem(index, 3, result.net_name or "")

    def on_item_selected(self, event):
        index = event.GetIndex()
        result = self.results[index]
        self.message_text.SetValue(result.detailed_message or result.message)
        self.suggestion_text.SetValue(result.suggestion or "No suggestion available.")
        self.documentation_text.SetValue(result.documentation_ref or "No documentation reference available.")
        self.example_text.SetValue(result.example_solution or "No example solution available.")
        affected_text = "Affected Components:\n" + "\n".join(result.affected_components) + "\n\nAffected Nets:\n" + "\n".join(result.affected_nets)
        self.affected_text.SetValue(affected_text)

    def on_search(self, event):
        search_term = self.search_ctrl.GetValue().lower()
        filtered_results = [result for result in self.results if search_term in result.message.lower() or search_term in (result.component_ref or "").lower()]
        self.results_list.DeleteAllItems()
        for result in filtered_results:
            index = self.results_list.GetItemCount()
            self.results_list.InsertItem(index, result.severity.name.lower())
            self.results_list.SetItem(index, 1, result.message)
            self.results_list.SetItem(index, 2, result.component_ref or "")
            self.results_list.SetItem(index, 3, result.net_name or "")

    def on_sort(self, event):
        sort_by = self.sort_choice.GetString(self.sort_choice.GetSelection())
        if sort_by == "Severity":
            self.results.sort(key=lambda x: x.severity.value)
        elif sort_by == "Component":
            self.results.sort(key=lambda x: x.component_ref or "")
        elif sort_by == "Message":
            self.results.sort(key=lambda x: x.message)
        self.update_results_list()

    def on_export_csv(self, event):
        with wx.FileDialog(self, "Export to CSV", wildcard="CSV files (*.csv)|*.csv", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            with open(pathname, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Severity", "Message", "Component", "Net", "Suggestion", "Documentation", "Example", "Affected Components", "Affected Nets"])
                for result in self.results:
                    writer.writerow([
                        result.severity.name,
                        result.message,
                        result.component_ref or "",
                        result.net_name or "",
                        result.suggestion or "",
                        result.documentation_ref or "",
                        result.example_solution or "",
                        ", ".join(result.affected_components),
                        ", ".join(result.affected_nets)
                    ])

    def on_export_json(self, event):
        with wx.FileDialog(self, "Export to JSON", wildcard="JSON files (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            with open(pathname, 'w') as file:
                json.dump([{
                    "severity": result.severity.name,
                    "message": result.message,
                    "component": result.component_ref or "",
                    "net": result.net_name or "",
                    "suggestion": result.suggestion or "",
                    "documentation": result.documentation_ref or "",
                    "example": result.example_solution or "",
                    "affected_components": result.affected_components,
                    "affected_nets": result.affected_nets
                } for result in self.results], file, indent=4)

def show_validation_results(results: List[SchematicValidationResult]):
    """Show the validation results in a new window."""
    app = wx.App()
    frame = EnhancedValidationResultDisplay()
    frame.display_results(results)
    frame.Show()
    app.MainLoop() 
