"""Unit tests for AudioSchematicValidator."""
import unittest
import pcbnew
from kicad_pcb_generator.audio.validation.schematic.validator import AudioSchematicValidator, SchematicValidationResult, SchematicValidationSeverity, EnhancedAudioSchematicValidator

class TestAudioSchematicValidator(unittest.TestCase):
    def setUp(self):
        self.validator = AudioSchematicValidator()
        self.schematic = pcbnew.SCHEMATIC()
        self.board = pcbnew.BOARD()

    def test_check_off_board_components(self):
        # Create a mock schematic symbol with PanelMount field set to 'true'
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("J1")
        symbol.SetField("PanelMount", "true")
        self.schematic.Add(symbol)

        # Create a mock footprint on the board
        fp = pcbnew.FOOTPRINT(self.board)
        fp.SetReference("J1")
        fp.SetFPID(pcbnew.FPID("", "Jack_3.5mm"))
        self.board.Add(fp)

        # Run the check
        results = self.validator.check_off_board_components(self.schematic, self.board)
        self.assertEqual(len(results), 0, "No warnings expected for valid panel-mount component.")

        # Remove the footprint and check again
        self.board.Remove(fp)
        results = self.validator.check_off_board_components(self.schematic, self.board)
        self.assertEqual(len(results), 1, "Warning expected for missing panel-mount footprint.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.WARNING)

    def test_check_power_headers(self):
        # Create a mock power header symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("PWR1")
        self.schematic.Add(symbol)

        # Run the check
        results = self.validator.check_power_headers(self.schematic)
        self.assertEqual(len(results), 0, "No errors expected for valid power header.")

        # Remove the symbol and check again
        self.schematic.Remove(symbol)
        results = self.validator.check_power_headers(self.schematic)
        self.assertEqual(len(results), 1, "Error expected for missing power header.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.ERROR)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("power header", results[0].suggestion.lower())

    def test_check_power_connections(self):
        # Create a mock power header symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("PWR1")
        self.schematic.Add(symbol)

        # Create a mock net
        net = pcbnew.NET(self.schematic)
        net.SetName("+12V")
        self.schematic.Add(net)

        # Connect the symbol to the net
        pin = symbol.GetPin(0)
        pin.SetNet(net)

        # Run the check
        results = self.validator.check_power_connections(self.schematic)
        self.assertEqual(len(results), 0, "No errors expected for valid power connection.")

        # Change the net name and check again
        net.SetName("INVALID")
        results = self.validator.check_power_connections(self.schematic)
        self.assertEqual(len(results), 1, "Error expected for invalid power connection.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.ERROR)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("power rails", results[0].suggestion.lower())

    def test_check_audio_signal_paths(self):
        # Create a mock audio component symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("U1")
        self.schematic.Add(symbol)

        # Run the check
        results = self.validator.check_audio_signal_paths(self.schematic)
        self.assertEqual(len(results), 0, "No errors expected for valid audio component.")

        # Remove the symbol and check again
        self.schematic.Remove(symbol)
        results = self.validator.check_audio_signal_paths(self.schematic)
        self.assertEqual(len(results), 1, "Error expected for missing audio component.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.ERROR)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("audio component", results[0].suggestion.lower())

    def test_check_audio_signal_optimization(self):
        # Create a mock audio component symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("U1")
        self.schematic.Add(symbol)

        # Create a mock net
        net = pcbnew.NET(self.schematic)
        net.SetName("AUDIO1")
        self.schematic.Add(net)

        # Connect the symbol to the net
        pin = symbol.GetPin(0)
        pin.SetNet(net)

        # Run the check
        results = self.validator.check_audio_signal_optimization(self.schematic)
        self.assertEqual(len(results), 0, "No warnings expected for valid audio signal optimization.")

        # Remove the symbol and check again
        self.schematic.Remove(symbol)
        results = self.validator.check_audio_signal_optimization(self.schematic)
        self.assertEqual(len(results), 1, "Warning expected for missing audio signal optimization.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.WARNING)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("signal conditioning", results[0].suggestion.lower())

    def test_check_cv_gate_signals(self):
        # Create a mock CV/gate component symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("U3")
        self.schematic.Add(symbol)

        # Run the check
        results = self.validator.check_cv_gate_signals(self.schematic)
        self.assertEqual(len(results), 0, "No errors expected for valid CV/gate component.")

        # Remove the symbol and check again
        self.schematic.Remove(symbol)
        results = self.validator.check_cv_gate_signals(self.schematic)
        self.assertEqual(len(results), 1, "Error expected for missing CV/gate component.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.ERROR)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("cv/gate component", results[0].suggestion.lower())

    def test_check_cv_signal_isolation(self):
        # Create a mock CV component symbol
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("U3")
        self.schematic.Add(symbol)

        # Create a mock net
        net = pcbnew.NET(self.schematic)
        net.SetName("CV1")
        self.schematic.Add(net)

        # Connect the symbol to the net
        pin = symbol.GetPin(0)
        pin.SetNet(net)

        # Run the check
        results = self.validator.check_cv_signal_isolation(self.schematic)
        self.assertEqual(len(results), 0, "No warnings expected for valid CV signal isolation.")

        # Remove the symbol and check again
        self.schematic.Remove(symbol)
        results = self.validator.check_cv_signal_isolation(self.schematic)
        self.assertEqual(len(results), 1, "Warning expected for missing CV signal isolation.")
        self.assertEqual(results[0].severity, SchematicValidationSeverity.WARNING)
        self.assertIsNotNone(results[0].suggestion, "Suggestion should be present")
        self.assertIsNotNone(results[0].documentation_ref, "Documentation reference should be present")
        self.assertIn("signal isolation", results[0].suggestion.lower())

    def test_multiple_validation_issues(self):
        # Create a mock power header symbol with incorrect net
        symbol = pcbnew.COMPONENT(self.schematic)
        symbol.SetReference("PWR1")
        self.schematic.Add(symbol)

        # Create a mock net with incorrect name
        net = pcbnew.NET(self.schematic)
        net.SetName("INVALID")
        self.schematic.Add(net)

        # Connect the symbol to the net
        pin = symbol.GetPin(0)
        pin.SetNet(net)

        # Run the validate method
        results = self.validator.validate_schematic(self.schematic, self.board)
        self.assertGreater(len(results), 0, "Multiple validation issues expected")
        
        # Verify that each result has appropriate fields
        for result in results:
            self.assertIsNotNone(result.suggestion, "Suggestion should be present")
            self.assertIsNotNone(result.documentation_ref, "Documentation reference should be present")

    def test_validate_schematic(self):
        # Create mock symbols for power header, audio component, and CV/gate component
        pwr_symbol = pcbnew.COMPONENT(self.schematic)
        pwr_symbol.SetReference("PWR1")
        self.schematic.Add(pwr_symbol)

        audio_symbol = pcbnew.COMPONENT(self.schematic)
        audio_symbol.SetReference("U1")
        self.schematic.Add(audio_symbol)

        cv_symbol = pcbnew.COMPONENT(self.schematic)
        cv_symbol.SetReference("U3")
        self.schematic.Add(cv_symbol)

        # Run the validate method
        results = self.validator.validate_schematic(self.schematic, self.board)
        self.assertEqual(len(results), 0, "No errors expected for valid schematic and board.")

        # Remove the symbols and check again
        self.schematic.Remove(pwr_symbol)
        self.schematic.Remove(audio_symbol)
        self.schematic.Remove(cv_symbol)
        results = self.validator.validate_schematic(self.schematic, self.board)
        self.assertEqual(len(results), 3, "Errors expected for missing components.")
        
        # Verify that each result has appropriate fields
        for result in results:
            self.assertIsNotNone(result.suggestion, "Suggestion should be present")
            self.assertIsNotNone(result.documentation_ref, "Documentation reference should be present")

if __name__ == "__main__":
    unittest.main() 