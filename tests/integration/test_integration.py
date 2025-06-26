"""Integration tests for the validation system."""
import unittest
import os
from kicad_pcb_generator.audio.validation.schematic.validator import AudioSchematicValidator
from kicad_pcb_generator.audio.validation.schematic.validator import SchematicValidationResult, SchematicValidationSeverity

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = AudioSchematicValidator()
        self.project_path = os.path.join(os.path.dirname(__file__), "test_project")

    def test_validate_real_project(self):
        # Load the real KiCad project
        self.validator.load_project(self.project_path)

        # Run the validation
        results = self.validator.validate_schematic()

        # Verify that the validation results match the expected output
        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, SchematicValidationResult) for result in results))

        # Check for specific validation results
        error_messages = [result.message for result in results if result.severity == SchematicValidationSeverity.ERROR]
        warning_messages = [result.message for result in results if result.severity == SchematicValidationSeverity.WARNING]

        # Example assertions (adjust based on expected results)
        self.assertIn("Missing Eurorack power header: PWR1", error_messages)
        self.assertIn("Audio signal AUDIO1 not routed through appropriate components", warning_messages)

if __name__ == "__main__":
    unittest.main() 