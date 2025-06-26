"""Integration tests for manufacturing features."""
import unittest
import os
import tempfile
import shutil
import pcbnew

from kicad_pcb_generator.core.manufacturing import (
    ThermalManagement,
    RoutingManagement,
    ModelManagement
)
from kicad_pcb_generator.core.testing.signal_integrity_tester import SignalIntegrityTester
from kicad_pcb_generator.core.testing.power_ground_tester import PowerGroundTester
from kicad_pcb_generator.core.testing.emi_emc_tester import EMIEMCTester

class TestManufacturingIntegration(unittest.TestCase):
    """Integration tests for manufacturing features."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.thermal = ThermalManagement()
        self.routing = RoutingManagement()
        self.models = ModelManagement()
        
        # Create test board
        self.board = pcbnew.BOARD()
        
        # Initialize testers
        self.si_tester = SignalIntegrityTester(self.board)
        self.pg_tester = PowerGroundTester(self.board)
        self.emi_tester = EMIEMCTester(self.board)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_complete_manufacturing_workflow(self):
        """Test complete manufacturing workflow."""
        # 1. Create thermal zones
        self.thermal.create_thermal_zone(
            name="zone1",
            position=(10.0, 10.0),
            size=(20.0, 20.0)
        )
        
        # 2. Create differential pairs
        self.routing.create_differential_pair(
            name="pair1",
            net1="net1",
            net2="net2"
        )
        
        # 3. Generate 3D model
        output_path = os.path.join(self.temp_dir, "test_model.step")
        self.models.generate_3d_model(output_path)
        
        # 4. Run comprehensive validation tests
        si_results = self.si_tester.test_signal_integrity()
        pg_results = self.pg_tester.test_power_ground()
        emi_results = self.emi_tester.test_emi_emc()
        
        # Verify signal integrity
        self.assertTrue(si_results['impedance']['passed'])
        self.assertTrue(si_results['crosstalk']['passed'])
        self.assertTrue(si_results['reflections']['passed'])
        
        # Verify power and ground
        self.assertTrue(pg_results['power_supply']['passed'])
        self.assertTrue(pg_results['ground_plane']['passed'])
        self.assertTrue(pg_results['power_distribution']['passed'])
        self.assertTrue(pg_results['ground_noise']['passed'])
        self.assertTrue(pg_results['thermal']['passed'])
        
        # Verify EMI/EMC
        self.assertTrue(emi_results['emissions']['passed'])
        self.assertTrue(emi_results['immunity']['passed'])
        self.assertTrue(emi_results['shielding']['passed'])
        self.assertTrue(emi_results['guard_traces']['passed'])
        self.assertTrue(emi_results['ground_stitching']['passed'])
        
        # 5. Validate all features
        thermal_errors = self.thermal.validate_thermal_design()
        routing_errors = self.routing.validate_routing()
        model_errors = self.models.validate_3d_model(output_path)
        
        # Check validation results
        self.assertIsInstance(thermal_errors, list)
        self.assertIsInstance(routing_errors, list)
        self.assertIsInstance(model_errors, list)
        
        # 6. Optimize features
        self.thermal.optimize_thermal_design()
        self.routing.match_trace_lengths("pair1")
        
        # 7. Final validation
        final_si_results = self.si_tester.test_signal_integrity()
        final_pg_results = self.pg_tester.test_power_ground()
        final_emi_results = self.emi_tester.test_emi_emc()
        
        # Verify final signal integrity
        self.assertTrue(final_si_results['impedance']['passed'])
        self.assertTrue(final_si_results['crosstalk']['passed'])
        self.assertTrue(final_si_results['reflections']['passed'])
        
        # Verify final power and ground
        self.assertTrue(final_pg_results['power_supply']['passed'])
        self.assertTrue(final_pg_results['ground_plane']['passed'])
        self.assertTrue(final_pg_results['power_distribution']['passed'])
        self.assertTrue(final_pg_results['ground_noise']['passed'])
        self.assertTrue(final_pg_results['thermal']['passed'])
        
        # Verify final EMI/EMC
        self.assertTrue(final_emi_results['emissions']['passed'])
        self.assertTrue(final_emi_results['immunity']['passed'])
        self.assertTrue(final_emi_results['shielding']['passed'])
        self.assertTrue(final_emi_results['guard_traces']['passed'])
        self.assertTrue(final_emi_results['ground_stitching']['passed'])
        
        final_thermal_errors = self.thermal.validate_thermal_design()
        final_routing_errors = self.routing.validate_routing()
        
        # Check final validation results
        self.assertIsInstance(final_thermal_errors, list)
        self.assertIsInstance(final_routing_errors, list)

    def test_thermal_management(self):
        """Test thermal management features."""
        # Create thermal zones
        self.thermal.create_thermal_zone(
            name="zone1",
            position=(10.0, 10.0),
            size=(20.0, 20.0)
        )
        
        # Run thermal validation
        pg_results = self.pg_tester.test_power_ground()
        self.assertTrue(pg_results['thermal']['passed'])
        
        # Optimize thermal design
        self.thermal.optimize_thermal_design()
        
        # Verify optimization
        final_pg_results = self.pg_tester.test_power_ground()
        self.assertTrue(final_pg_results['thermal']['passed'])

    def test_routing_management(self):
        """Test routing management features."""
        # Create differential pairs
        self.routing.create_differential_pair(
            name="pair1",
            net1="net1",
            net2="net2"
        )
        
        # Run signal integrity validation
        si_results = self.si_tester.test_signal_integrity()
        self.assertTrue(si_results['impedance']['passed'])
        self.assertTrue(si_results['crosstalk']['passed'])
        
        # Optimize routing
        self.routing.match_trace_lengths("pair1")
        
        # Verify optimization
        final_si_results = self.si_tester.test_signal_integrity()
        self.assertTrue(final_si_results['impedance']['passed'])
        self.assertTrue(final_si_results['crosstalk']['passed'])

    def test_model_management(self):
        """Test 3D model management features."""
        # Generate 3D model
        output_path = os.path.join(self.temp_dir, "test_model.step")
        self.models.generate_3d_model(output_path)
        
        # Validate model
        model_errors = self.models.validate_3d_model(output_path)
        self.assertIsInstance(model_errors, list)
        
        # Verify file exists
        self.assertTrue(os.path.exists(output_path))

    def test_error_handling(self):
        """Test error handling in manufacturing features."""
        # Test invalid thermal zone
        with self.assertRaises(ValueError):
            self.thermal.create_thermal_zone(
                name="zone1",
                position=(-1.0, -1.0),  # Invalid position
                size=(20.0, 20.0)
            )
        
        # Test invalid differential pair
        with self.assertRaises(ValueError):
            self.routing.create_differential_pair(
                name="pair1",
                net1="",  # Invalid net name
                net2="net2"
            )
        
        # Test invalid model path
        with self.assertRaises(ValueError):
            self.models.generate_3d_model("")  # Invalid path
        
        # Test invalid board
        invalid_board = pcbnew.BOARD()
        with self.assertRaises(Exception):
            si_tester = SignalIntegrityTester(invalid_board)
            si_tester.test_signal_integrity()
        
        with self.assertRaises(Exception):
            pg_tester = PowerGroundTester(invalid_board)
            pg_tester.test_power_ground()
        
        with self.assertRaises(Exception):
            emi_tester = EMIEMCTester(invalid_board)
            emi_tester.test_emi_emc()

if __name__ == '__main__':
    unittest.main() 