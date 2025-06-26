"""Validation result display for the KiCad PCB Generator."""
import wx
import csv
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from ..validation_results import (
    ValidationResult,
    ValidationCategory,
    ValidationSeverity,
    AudioValidationResult,
    SafetyValidationResult,
    ManufacturingValidationResult
)
from ..report_generator import ValidationReportGenerator, ReportFormat
from ....utils.logging.logger import Logger

class ValidationResultDisplay(wx.Frame):
    """Display for validation results."""
    
    def __init__(self, parent: Optional[wx.Window] = None):
        """Initialize the validation result display.
        
        Args:
            parent: Optional parent window
        """
        super().__init__(parent, title="Validation Results", size=(1200, 800))
        self.logger = Logger(__name__)
        self.results: List[ValidationResult] = []
        self.report_generator = ValidationReportGenerator()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        # Add toolbar
        toolbar = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add search box
        self.search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        toolbar.Add(self.search_ctrl, 1, wx.EXPAND | wx.RIGHT, 5)
        
        # Add filter controls
        self.filter_choice = wx.Choice(panel, choices=["All", "Critical", "Error", "Warning", "Info"])
        self.filter_choice.SetSelection(0)
        self.filter_choice.Bind(wx.EVT_CHOICE, self.on_filter)
        toolbar.Add(self.filter_choice, 0, wx.RIGHT, 5)
        
        # Add sort controls
        self.sort_choice = wx.Choice(panel, choices=["Severity", "Category", "Message"])
        self.sort_choice.SetSelection(0)
        self.sort_choice.Bind(wx.EVT_CHOICE, self.on_sort)
        toolbar.Add(self.sort_choice, 0, wx.RIGHT, 5)
        
        vbox.Add(toolbar, 0, wx.EXPAND | wx.ALL, 5)
        
        # Split the window into two parts: results list and detailed view
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        # Add results list
        self.results_list = wx.ListCtrl(panel, style=wx.LC_REPORT)
        self.results_list.InsertColumn(0, "Severity", width=80)
        self.results_list.InsertColumn(1, "Category", width=120)
        self.results_list.InsertColumn(2, "Message", width=400)
        self.results_list.InsertColumn(3, "Location", width=120)
        self.results_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_item_selected)
        hbox.Add(self.results_list, 1, wx.EXPAND | wx.ALL, 5)
        
        # Add detailed view panel
        self.details_panel = wx.Panel(panel)
        details_box = wx.BoxSizer(wx.VERTICAL)
        
        # Add notebook for different types of information
        self.notebook = wx.Notebook(self.details_panel)
        
        # Message panel
        self.message_panel = wx.Panel(self.notebook)
        message_box = wx.BoxSizer(wx.VERTICAL)
        self.message_text = wx.TextCtrl(self.message_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        message_box.Add(self.message_text, 1, wx.EXPAND)
        self.message_panel.SetSizer(message_box)
        
        # Details panel
        self.details_text_panel = wx.Panel(self.notebook)
        details_text_box = wx.BoxSizer(wx.VERTICAL)
        self.details_text = wx.TextCtrl(self.details_text_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        details_text_box.Add(self.details_text, 1, wx.EXPAND)
        self.details_text_panel.SetSizer(details_text_box)
        
        # Location panel
        self.location_panel = wx.Panel(self.notebook)
        location_box = wx.BoxSizer(wx.VERTICAL)
        self.location_text = wx.TextCtrl(self.location_panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        location_box.Add(self.location_text, 1, wx.EXPAND)
        self.location_panel.SetSizer(location_box)
        
        # Add panels to notebook
        self.notebook.AddPage(self.message_panel, "Message")
        self.notebook.AddPage(self.details_text_panel, "Details")
        self.notebook.AddPage(self.location_panel, "Location")
        
        details_box.Add(self.notebook, 1, wx.EXPAND)
        self.details_panel.SetSizer(details_box)
        hbox.Add(self.details_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        vbox.Add(hbox, 1, wx.EXPAND)
        
        # Add export buttons
        export_box = wx.BoxSizer(wx.HORIZONTAL)
        
        self.export_json_btn = wx.Button(panel, label="Export to JSON")
        self.export_json_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_export(ReportFormat.JSON))
        export_box.Add(self.export_json_btn, 0, wx.ALL, 5)
        
        self.export_csv_btn = wx.Button(panel, label="Export to CSV")
        self.export_csv_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_export(ReportFormat.CSV))
        export_box.Add(self.export_csv_btn, 0, wx.ALL, 5)
        
        self.export_html_btn = wx.Button(panel, label="Export to HTML")
        self.export_html_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_export(ReportFormat.HTML))
        export_box.Add(self.export_html_btn, 0, wx.ALL, 5)
        
        self.export_md_btn = wx.Button(panel, label="Export to Markdown")
        self.export_md_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_export(ReportFormat.MARKDOWN))
        export_box.Add(self.export_md_btn, 0, wx.ALL, 5)
        
        vbox.Add(export_box, 0, wx.ALIGN_RIGHT)
        
        panel.SetSizer(vbox)
    
    def display_results(self, results: List[ValidationResult]):
        """Display validation results.
        
        Args:
            results: List of validation results
        """
        self.results = results
        self.update_results_list()
    
    def update_results_list(self):
        """Update the results list with current results."""
        self.results_list.DeleteAllItems()
        
        for result in self.results:
            index = self.results_list.GetItemCount()
            self.results_list.InsertItem(index, result.severity.value)
            self.results_list.SetItem(index, 1, result.category.value)
            self.results_list.SetItem(index, 2, result.message)
            self.results_list.SetItem(index, 3, str(result.location) if result.location else "")
            
            # Set item color based on severity
            if result.severity == ValidationSeverity.CRITICAL:
                self.results_list.SetItemBackgroundColour(index, wx.RED)
            elif result.severity == ValidationSeverity.ERROR:
                self.results_list.SetItemBackgroundColour(index, wx.Colour(255, 200, 200))
            elif result.severity == ValidationSeverity.WARNING:
                self.results_list.SetItemBackgroundColour(index, wx.Colour(255, 255, 200))
            elif result.severity == ValidationSeverity.INFO:
                self.results_list.SetItemBackgroundColour(index, wx.Colour(200, 255, 200))
    
    def on_item_selected(self, event):
        """Handle selection of a result item.
        
        Args:
            event: Selection event
        """
        index = event.GetIndex()
        result = self.results[index]
        
        # Update message panel
        self.message_text.SetValue(result.message)
        
        # Update details panel
        details = []
        if isinstance(result, AudioValidationResult):
            if result.frequency is not None:
                details.append(f"Frequency: {result.frequency} Hz")
            if result.impedance is not None:
                details.append(f"Impedance: {result.impedance} Ω")
            if result.crosstalk is not None:
                details.append(f"Crosstalk: {result.crosstalk:.1%}")
            if result.noise_level is not None:
                details.append(f"Noise Level: {result.noise_level} dB")
            if result.power_quality is not None:
                details.append(f"Power Quality: {result.power_quality:.1%}")
            if result.thermal_impact is not None:
                details.append(f"Thermal Impact: {result.thermal_impact}°C")
        elif isinstance(result, SafetyValidationResult):
            if result.voltage is not None:
                details.append(f"Voltage: {result.voltage} V")
            if result.current is not None:
                details.append(f"Current: {result.current} A")
            if result.power is not None:
                details.append(f"Power: {result.power} W")
            if result.temperature is not None:
                details.append(f"Temperature: {result.temperature}°C")
            if result.clearance is not None:
                details.append(f"Clearance: {result.clearance} mm")
            if result.creepage is not None:
                details.append(f"Creepage: {result.creepage} mm")
        elif isinstance(result, ManufacturingValidationResult):
            if result.min_feature_size is not None:
                details.append(f"Min Feature Size: {result.min_feature_size} mm")
            if result.max_feature_size is not None:
                details.append(f"Max Feature Size: {result.max_feature_size} mm")
            if result.recommended_size is not None:
                details.append(f"Recommended Size: {result.recommended_size} mm")
            if result.manufacturing_cost is not None:
                details.append(f"Manufacturing Cost: {result.manufacturing_cost:.1%}")
            if result.yield_impact is not None:
                details.append(f"Yield Impact: {result.yield_impact:.1%}")
        
        if result.details:
            details.extend(f"{k}: {v}" for k, v in result.details.items())
        
        self.details_text.SetValue("\n".join(details))
        
        # Update location panel
        if result.location:
            self.location_text.SetValue(f"X: {result.location[0]:.2f} mm\nY: {result.location[1]:.2f} mm")
        else:
            self.location_text.SetValue("No location data available")
    
    def on_search(self, event):
        """Handle search.
        
        Args:
            event: Search event
        """
        search_term = self.search_ctrl.GetValue().lower()
        filtered_results = [
            result for result in self.results
            if search_term in result.message.lower() or
               search_term in result.category.value.lower()
        ]
        self.results_list.DeleteAllItems()
        for result in filtered_results:
            index = self.results_list.GetItemCount()
            self.results_list.InsertItem(index, result.severity.value)
            self.results_list.SetItem(index, 1, result.category.value)
            self.results_list.SetItem(index, 2, result.message)
            self.results_list.SetItem(index, 3, str(result.location) if result.location else "")
    
    def on_filter(self, event):
        """Handle filter selection.
        
        Args:
            event: Filter event
        """
        filter_by = self.filter_choice.GetString(self.filter_choice.GetSelection())
        if filter_by == "All":
            filtered_results = self.results
        else:
            filtered_results = [
                result for result in self.results
                if result.severity.value.lower() == filter_by.lower()
            ]
        self.results_list.DeleteAllItems()
        for result in filtered_results:
            index = self.results_list.GetItemCount()
            self.results_list.InsertItem(index, result.severity.value)
            self.results_list.SetItem(index, 1, result.category.value)
            self.results_list.SetItem(index, 2, result.message)
            self.results_list.SetItem(index, 3, str(result.location) if result.location else "")
    
    def on_sort(self, event):
        """Handle sort selection.
        
        Args:
            event: Sort event
        """
        sort_by = self.sort_choice.GetString(self.sort_choice.GetSelection())
        if sort_by == "Severity":
            self.results.sort(key=lambda x: x.severity.value)
        elif sort_by == "Category":
            self.results.sort(key=lambda x: x.category.value)
        elif sort_by == "Message":
            self.results.sort(key=lambda x: x.message)
        self.update_results_list()
    
    def on_export(self, format: ReportFormat):
        """Handle export.
        
        Args:
            format: Report format
        """
        try:
            # Get file extension
            ext = format.value
            
            # Show file dialog
            with wx.FileDialog(
                self,
                f"Export to {format.value.upper()}",
                wildcard=f"{format.value.upper()} files (*.{ext})|*.{ext}",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as fileDialog:
                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                
                # Get file path
                pathname = fileDialog.GetPath()
                
                # Generate report
                report = self.report_generator.generate_report(self.results, format)
                
                # Write to file
                with open(pathname, 'w') as file:
                    file.write(report)
                
                # Show success message
                wx.MessageBox(
                    f"Successfully exported to {pathname}",
                    "Export Successful",
                    wx.OK | wx.ICON_INFORMATION
                )
                
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            wx.MessageBox(
                f"Error exporting report: {str(e)}",
                "Export Error",
                wx.OK | wx.ICON_ERROR
            )

def show_validation_results(results: List[ValidationResult]):
    """Show validation results in a new window.
    
    Args:
        results: List of validation results
    """
    app = wx.App()
    frame = ValidationResultDisplay()
    frame.display_results(results)
    frame.Show()
    app.MainLoop() 