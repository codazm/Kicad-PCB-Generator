"""Unit tests for EnhancedValidationResultDisplay."""
import unittest
import wx
import os
import csv
import json
from kicad_pcb_generator.audio.validation.schematic.validator import SchematicValidationResult, SchematicValidationSeverity
from kicad_pcb_generator.audio.validation.ui.validation_result_display import EnhancedValidationResultDisplay

class TestEnhancedValidationResultDisplay(unittest.TestCase):
    def setUp(self):
        self.app = wx.App()
        self.frame = EnhancedValidationResultDisplay()
        self.results = [
            SchematicValidationResult(
                message="Test error",
                severity=SchematicValidationSeverity.ERROR,
                component_ref="U1"
            ),
            SchematicValidationResult(
                message="Test warning",
                severity=SchematicValidationSeverity.WARNING,
                component_ref="U2"
            ),
            SchematicValidationResult(
                message="Test info",
                severity=SchematicValidationSeverity.INFO,
                component_ref="U3"
            )
        ]
        self.frame.display_results(self.results)

    def tearDown(self):
        self.frame.Destroy()
        self.app.Destroy()

    def test_sorting(self):
        # Test sorting by severity
        self.frame.sort_choice.SetSelection(0)  # Severity
        self.frame.on_sort(None)
        self.assertEqual(self.frame.results_list.GetItem(0, 0).GetText(), "error")
        self.assertEqual(self.frame.results_list.GetItem(1, 0).GetText(), "warning")
        self.assertEqual(self.frame.results_list.GetItem(2, 0).GetText(), "info")

        # Test sorting by component
        self.frame.sort_choice.SetSelection(1)  # Component
        self.frame.on_sort(None)
        self.assertEqual(self.frame.results_list.GetItem(0, 2).GetText(), "U1")
        self.assertEqual(self.frame.results_list.GetItem(1, 2).GetText(), "U2")
        self.assertEqual(self.frame.results_list.GetItem(2, 2).GetText(), "U3")

        # Test sorting by message
        self.frame.sort_choice.SetSelection(2)  # Message
        self.frame.on_sort(None)
        self.assertEqual(self.frame.results_list.GetItem(0, 1).GetText(), "Test error")
        self.assertEqual(self.frame.results_list.GetItem(1, 1).GetText(), "Test info")
        self.assertEqual(self.frame.results_list.GetItem(2, 1).GetText(), "Test warning")

    def test_searching(self):
        # Test searching by message
        self.frame.search_ctrl.SetValue("error")
        self.frame.on_search(None)
        self.assertEqual(self.frame.results_list.GetItemCount(), 1)
        self.assertEqual(self.frame.results_list.GetItem(0, 1).GetText(), "Test error")

        # Test searching by component
        self.frame.search_ctrl.SetValue("U2")
        self.frame.on_search(None)
        self.assertEqual(self.frame.results_list.GetItemCount(), 1)
        self.assertEqual(self.frame.results_list.GetItem(0, 2).GetText(), "U2")

    def test_export_csv(self):
        # Create a temporary file for testing
        with wx.FileDialog(self.frame, "Export to CSV", wildcard="CSV files (*.csv)|*.csv", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            fileDialog.SetPath("test_export.csv")
            if fileDialog.ShowModal() == wx.ID_OK:
                self.frame.on_export_csv(None)

        # Verify the CSV file
        with open("test_export.csv", 'r', newline='') as file:
            reader = csv.reader(file)
            header = next(reader)
            self.assertEqual(header, ["Severity", "Message", "Component", "Net"])
            rows = list(reader)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], ["ERROR", "Test error", "U1", ""])
            self.assertEqual(rows[1], ["WARNING", "Test warning", "U2", ""])
            self.assertEqual(rows[2], ["INFO", "Test info", "U3", ""])

        # Clean up
        os.remove("test_export.csv")

    def test_export_json(self):
        # Create a temporary file for testing
        with wx.FileDialog(self.frame, "Export to JSON", wildcard="JSON files (*.json)|*.json", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            fileDialog.SetPath("test_export.json")
            if fileDialog.ShowModal() == wx.ID_OK:
                self.frame.on_export_json(None)

        # Verify the JSON file
        with open("test_export.json", 'r') as file:
            data = json.load(file)
            self.assertEqual(len(data), 3)
            self.assertEqual(data[0], {"severity": "ERROR", "message": "Test error", "component": "U1", "net": ""})
            self.assertEqual(data[1], {"severity": "WARNING", "message": "Test warning", "component": "U2", "net": ""})
            self.assertEqual(data[2], {"severity": "INFO", "message": "Test info", "component": "U3", "net": ""})

        # Clean up
        os.remove("test_export.json")

if __name__ == "__main__":
    unittest.main() 
