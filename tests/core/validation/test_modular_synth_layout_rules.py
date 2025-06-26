"""Unit tests for ModularSynthLayoutRules."""
import unittest
import pcbnew
from kicad_pcb_generator.audio.layout.modular_synth_layout_rules import ModularSynthLayoutRules

class TestModularSynthLayoutRules(unittest.TestCase):
    def setUp(self):
        self.rules = ModularSynthLayoutRules()
        self.board = pcbnew.BOARD()

    def test_check_off_board_components(self):
        # Create a mock footprint with PanelMount field set to 'true'
        fp = pcbnew.FOOTPRINT(self.board)
        fp.SetReference("J1")
        fp.SetFPID(pcbnew.FPID("", "Jack_3.5mm"))
        fp.SetField("PanelMount", "true")
        self.board.Add(fp)

        # Create a mock footprint without PanelMount field
        fp2 = pcbnew.FOOTPRINT(self.board)
        fp2.SetReference("R1")
        fp2.SetFPID(pcbnew.FPID("", "R_0805_2012Metric"))
        self.board.Add(fp2)

        # Run the check
        warnings = self.rules.check_off_board_components(self.board)
        self.assertEqual(len(warnings), 0, "No warnings expected for valid panel-mount footprint.")

        # Remove the footprint and check again
        self.board.Remove(fp)
        warnings = self.rules.check_off_board_components(self.board)
        self.assertEqual(len(warnings), 0, "No warnings expected if no panel-mount footprints are present.")

    def test_validate(self):
        # Create a mock footprint with PanelMount field set to 'true'
        fp = pcbnew.FOOTPRINT(self.board)
        fp.SetReference("J1")
        fp.SetFPID(pcbnew.FPID("", "Jack_3.5mm"))
        fp.SetField("PanelMount", "true")
        self.board.Add(fp)

        # Run the validate method
        errors = self.rules.validate(self.board)
        self.assertEqual(len(errors), 0, "No errors expected for valid board.")

        # Remove the footprint and check again
        self.board.Remove(fp)
        errors = self.rules.validate(self.board)
        self.assertEqual(len(errors), 0, "No errors expected if no panel-mount footprints are present.")

if __name__ == "__main__":
    unittest.main() 