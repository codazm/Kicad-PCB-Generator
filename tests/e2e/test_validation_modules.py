"""End-to-end tests for validation modules integration."""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
import json
import pcbnew
from unittest.mock import MagicMock

from kicad_pcb_generator.core.testing.signal_integrity_tester import (
    SignalIntegrityTester,
    SignalIntegrityConfig
)
from kicad_pcb_generator.core.testing.power_ground_tester import (
    PowerGroundTester,
    PowerGroundConfig
)
from kicad_pcb_generator.core.testing.emi_emc_tester import (
    EMIEMCTester,
    EMIEMCConfig
)
from kicad_pcb_generator.core.workflow.design import DesignWorkflow
from kicad_pcb_generator.core.schematic_importer import SchematicImporter, ImportConfig
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory

class TestValidationModules(unittest.TestCase):
    """End-to-end tests for validation modules integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        cls.design_dir = os.path.join(cls.test_dir, "design")
        cls.output_dir = os.path.join(cls.test_dir, "output")
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Create test schematic
        cls.schematic_path = os.path.join(cls.test_dir, "test_circuit.kicad_sch")
        cls._create_test_schematic(cls.schematic_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up each test case."""
        # Initialize design workflow
        self.design_workflow = DesignWorkflow(self.design_dir)
        
        # Import schematic
        self.schematic_importer = SchematicImporter()
        config = ImportConfig(
            apply_audio_optimizations=True,
            validate_schematic=True,
            generate_3d_models=True,
            optimize_placement=True,
            optimize_routing=True
        )
        self.board_path = self.schematic_importer.import_schematic(
            schematic_path=self.schematic_path,
            output_dir=self.output_dir,
            config=config
        )
        
        # Load board
        self.board = pcbnew.LoadBoard(self.board_path)
        
        # Initialize testers with default configs
        self.si_tester = SignalIntegrityTester(self.board)
        self.pg_tester = PowerGroundTester(self.board)
        self.emi_tester = EMIEMCTester(self.board)

    def test_signal_integrity_workflow(self):
        """Test signal integrity testing workflow."""
        # Run comprehensive signal integrity tests
        si_results = self.si_tester.test_signal_integrity()
        
        # Verify results structure
        self.assertIsInstance(si_results, dict)
        self.assertIn('impedance', si_results)
        self.assertIn('crosstalk', si_results)
        self.assertIn('reflections', si_results)
        
        # Verify impedance matching
        impedance_results = si_results['impedance']
        self.assertIsInstance(impedance_results, dict)
        self.assertIn('passed', impedance_results)
        self.assertIn('metrics', impedance_results)
        
        # Verify crosstalk analysis
        crosstalk_results = si_results['crosstalk']
        self.assertIsInstance(crosstalk_results, dict)
        self.assertIn('passed', crosstalk_results)
        self.assertIn('metrics', crosstalk_results)
        
        # Verify reflection analysis
        reflection_results = si_results['reflections']
        self.assertIsInstance(reflection_results, dict)
        self.assertIn('passed', reflection_results)
        self.assertIn('metrics', reflection_results)

    def test_power_ground_workflow(self):
        """Test power and ground testing workflow."""
        # Run comprehensive power and ground tests
        pg_results = self.pg_tester.test_power_ground()
        
        # Verify results structure
        self.assertIsInstance(pg_results, dict)
        self.assertIn('power_supply', pg_results)
        self.assertIn('ground_plane', pg_results)
        self.assertIn('power_distribution', pg_results)
        self.assertIn('ground_noise', pg_results)
        self.assertIn('thermal', pg_results)
        
        # Verify power supply characteristics
        power_results = pg_results['power_supply']
        self.assertIsInstance(power_results, dict)
        self.assertIn('passed', power_results)
        self.assertIn('metrics', power_results)
        
        # Verify ground plane characteristics
        ground_results = pg_results['ground_plane']
        self.assertIsInstance(ground_results, dict)
        self.assertIn('passed', ground_results)
        self.assertIn('metrics', ground_results)
        
        # Verify power distribution
        distribution_results = pg_results['power_distribution']
        self.assertIsInstance(distribution_results, dict)
        self.assertIn('passed', distribution_results)
        self.assertIn('metrics', distribution_results)
        
        # Verify ground noise
        noise_results = pg_results['ground_noise']
        self.assertIsInstance(noise_results, dict)
        self.assertIn('passed', noise_results)
        self.assertIn('metrics', noise_results)
        
        # Verify thermal performance
        thermal_results = pg_results['thermal']
        self.assertIsInstance(thermal_results, dict)
        self.assertIn('passed', thermal_results)
        self.assertIn('metrics', thermal_results)

    def test_emi_emc_workflow(self):
        """Test EMI/EMC testing workflow."""
        # Run comprehensive EMI/EMC tests
        emi_results = self.emi_tester.test_emi_emc()
        
        # Verify results structure
        self.assertIsInstance(emi_results, dict)
        self.assertIn('emissions', emi_results)
        self.assertIn('immunity', emi_results)
        self.assertIn('shielding', emi_results)
        self.assertIn('guard_traces', emi_results)
        self.assertIn('ground_stitching', emi_results)
        
        # Verify emissions testing
        emissions_results = emi_results['emissions']
        self.assertIsInstance(emissions_results, dict)
        self.assertIn('passed', emissions_results)
        self.assertIn('metrics', emissions_results)
        
        # Verify immunity testing
        immunity_results = emi_results['immunity']
        self.assertIsInstance(immunity_results, dict)
        self.assertIn('passed', immunity_results)
        self.assertIn('metrics', immunity_results)
        
        # Verify shielding testing
        shielding_results = emi_results['shielding']
        self.assertIsInstance(shielding_results, dict)
        self.assertIn('passed', shielding_results)
        self.assertIn('metrics', shielding_results)
        
        # Verify guard trace testing
        guard_results = emi_results['guard_traces']
        self.assertIsInstance(guard_results, dict)
        self.assertIn('passed', guard_results)
        self.assertIn('metrics', guard_results)
        
        # Verify ground stitching testing
        stitching_results = emi_results['ground_stitching']
        self.assertIsInstance(stitching_results, dict)
        self.assertIn('passed', stitching_results)
        self.assertIn('metrics', stitching_results)

    def test_custom_configurations(self):
        """Test validation modules with custom configurations."""
        # Create custom configs
        si_config = SignalIntegrityConfig(
            crosstalk_threshold=-50.0,  # More lenient
            reflection_threshold=0.2,   # More lenient
            impedance_mismatch_threshold=10.0  # More lenient
        )
        
        pg_config = PowerGroundConfig(
            voltage_drop_threshold=0.2,  # More lenient
            ripple_threshold=0.2,       # More lenient
            ground_coverage_threshold=0.7  # More lenient
        )
        
        emi_config = EMIEMCConfig(
            radiated_emissions_limit=50.0,  # More lenient
            conducted_emissions_limit=40.0,  # More lenient
            shielding_effectiveness_limit=30.0  # More lenient
        )
        
        # Initialize testers with custom configs
        si_tester = SignalIntegrityTester(self.board, si_config)
        pg_tester = PowerGroundTester(self.board, pg_config)
        emi_tester = EMIEMCTester(self.board, emi_config)
        
        # Run tests
        si_results = si_tester.test_signal_integrity()
        pg_results = pg_tester.test_power_ground()
        emi_results = emi_tester.test_emi_emc()
        
        # Verify results reflect custom thresholds
        self.assertTrue(si_results['impedance']['passed'])
        self.assertTrue(pg_results['power_supply']['passed'])
        self.assertTrue(emi_results['emissions']['passed'])

    def test_error_handling(self):
        """Test error handling in validation modules."""
        # Test with invalid board
        invalid_board = pcbnew.BOARD()
        
        # Test signal integrity tester
        with self.assertRaises(Exception):
            si_tester = SignalIntegrityTester(invalid_board)
            si_tester.test_signal_integrity()
        
        # Test power/ground tester
        with self.assertRaises(Exception):
            pg_tester = PowerGroundTester(invalid_board)
            pg_tester.test_power_ground()
        
        # Test EMI/EMC tester
        with self.assertRaises(Exception):
            emi_tester = EMIEMCTester(invalid_board)
            emi_tester.test_emi_emc()

    @classmethod
    def _create_test_schematic(cls, path):
        """Create a test schematic file."""
        # Create a minimal valid schematic file
        with open(path, 'w') as f:
            f.write("""(kicad_sch (version 20211123) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (junction (at 50.8 50.8) (diameter 0) (color 0 0 0 0))
  (wire (pts (xy 50.8 50.8) (xy 101.6 50.8)) (stroke (width 0) (type default)))
  (label (at 76.2 45.72 0) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid 00000000-0000-0000-0000-000000000000)
    (text "Test"))
)""")

if __name__ == '__main__':
    unittest.main() 