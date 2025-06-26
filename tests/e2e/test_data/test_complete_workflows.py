"""
End-to-end tests for complete workflows.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path
import json
import pcbnew

from kicad_pcb_generator.core.workflow.design import DesignWorkflow
from kicad_pcb_generator.core.signal_integrity import (
    SignalIntegrityAnalyzer,
    CrosstalkAnalyzer
)
from kicad_pcb_generator.core.manufacturing import (
    ThermalManagement,
    RoutingManagement,
    ModelManagement
)
from kicad_pcb_generator.core.templates import (
    TemplateManager,
    VersionManager
)
from kicad_pcb_generator.audio.circuits import PreamplifierTemplate
from kicad_pcb_generator.core.schematic_importer import SchematicImporter, ImportConfig
from kicad_pcb_generator.core.testing.signal_integrity_tester import SignalIntegrityTester
from kicad_pcb_generator.core.testing.power_ground_tester import PowerGroundTester
from kicad_pcb_generator.core.testing.emi_emc_tester import EMIEMCTester

class TestCompleteWorkflows(unittest.TestCase):
    """End-to-end tests for complete workflows."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.design_dir = os.path.join(self.test_dir, "design")
        self.template_dir = os.path.join(self.test_dir, "templates")
        
        # Initialize all required components
        self.design_workflow = DesignWorkflow(self.design_dir)
        self.si_analyzer = SignalIntegrityAnalyzer()
        self.xt_analyzer = CrosstalkAnalyzer()
        self.thermal = ThermalManagement()
        self.routing = RoutingManagement()
        self.models = ModelManagement()
        self.template_manager = TemplateManager()
        self.version_manager = VersionManager(self.template_manager)
        self.schematic_importer = SchematicImporter()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_audio_amplifier_workflow(self):
        """Test complete audio amplifier design workflow."""
        # 1. Template Management
        template = self.template_manager.create_template(
            name="Audio Amplifier",
            category="audio",
            description="Template for audio amplifier PCB design"
        )
        self.assertIsNotNone(template)
        
        # Create template version
        version = self.version_manager.create_version(
            template_id=template.id,
            version="1.0.0",
            changes="Initial version"
        )
        self.assertEqual(version.version, "1.0.0")

        # 2. Design Workflow
        self.design_workflow.set_template(template)
        
        # Add components
        components = [
            {
                "id": "U1",
                "type": "opamp",
                "value": "NE5532",
                "footprint": "SOIC-8_3.9x4.9mm_P1.27mm",
                "metadata": {"supply_voltage": "±15V"}
            },
            {
                "id": "R1",
                "type": "resistor",
                "value": "10k",
                "footprint": "R_0805_2012Metric",
                "metadata": {"tolerance": "1%"}
            }
        ]
        for component in components:
            self.design_workflow.add_component(component)

        # Add nets
        nets = [
            {
                "name": "VCC",
                "pins": ["U1-8"]
            },
            {
                "name": "GND",
                "pins": ["U1-4"]
            }
        ]
        for net in nets:
            self.design_workflow.add_net(net)

        # 3. Signal Integrity Analysis
        # Add traces for analysis
        self.design_workflow.add_track({
            "net": "VCC",
            "layer": "F.Cu",
            "width": 0.3,
            "points": [(0, 0), (10, 0)]
        })

        # Get board path
        board_path = self.design_workflow.get_board_path()
        board = pcbnew.LoadBoard(board_path)

        # Initialize testers
        si_tester = SignalIntegrityTester(board)
        pg_tester = PowerGroundTester(board)
        emi_tester = EMIEMCTester(board)

        # Run comprehensive validation tests
        si_results = si_tester.test_signal_integrity()
        pg_results = pg_tester.test_power_ground()
        emi_results = emi_tester.test_emi_emc()

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

        # 4. Manufacturing Preparation
        # Create thermal zones
        self.thermal.create_thermal_zone(
            name="opamp_zone",
            position=(5.0, 5.0),
            size=(10.0, 10.0)
        )

        # Create differential pairs
        self.routing.create_differential_pair(
            name="audio_pair",
            net1="left_channel",
            net2="right_channel"
        )

        # Generate 3D model
        model_path = os.path.join(self.test_dir, "amplifier_model.step")
        self.models.generate_3d_model(model_path)
        self.assertTrue(os.path.exists(model_path))

        # 5. Validation
        # Validate design
        design_errors = self.design_workflow.validate_design()
        self.assertIsInstance(design_errors, list)

        # Validate thermal design
        thermal_errors = self.thermal.validate_thermal_design()
        self.assertIsInstance(thermal_errors, list)

        # Validate routing
        routing_errors = self.routing.validate_routing()
        self.assertIsInstance(routing_errors, list)

        # 6. Export
        export_path = os.path.join(self.test_dir, "export")
        self.design_workflow.export_design(export_path)
        self.assertTrue(os.path.exists(os.path.join(export_path, "design_state.json")))

    def test_power_supply_workflow(self):
        """Test complete power supply design workflow."""
        # 1. Template Management
        template = self.template_manager.create_template(
            name="Power Supply",
            category="power",
            description="Template for power supply PCB design"
        )
        self.assertIsNotNone(template)

        # 2. Design Workflow
        self.design_workflow.set_template(template)
        
        # Add components
        components = [
            {
                "id": "U1",
                "type": "regulator",
                "value": "LM317",
                "footprint": "TO-220-3_Vertical",
                "metadata": {"output_voltage": "12V"}
            },
            {
                "id": "C1",
                "type": "capacitor",
                "value": "100uF",
                "footprint": "C_0805_2012Metric",
                "metadata": {"voltage": "25V"}
            }
        ]
        for component in components:
            self.design_workflow.add_component(component)

        # 3. Signal Integrity Analysis
        # Add power traces
        self.design_workflow.add_track({
            "net": "VIN",
            "layer": "F.Cu",
            "width": 0.5,
            "points": [(0, 0), (20, 0)]
        })

        # Get board path
        board_path = self.design_workflow.get_board_path()
        board = pcbnew.LoadBoard(board_path)

        # Initialize testers
        si_tester = SignalIntegrityTester(board)
        pg_tester = PowerGroundTester(board)
        emi_tester = EMIEMCTester(board)

        # Run comprehensive validation tests
        si_results = si_tester.test_signal_integrity()
        pg_results = pg_tester.test_power_ground()
        emi_results = emi_tester.test_emi_emc()

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

        # 4. Manufacturing Preparation
        # Create thermal zones for regulator
        self.thermal.create_thermal_zone(
            name="regulator_zone",
            position=(10.0, 10.0),
            size=(15.0, 15.0)
        )

        # Create power traces
        self.routing.create_power_trace(
            name="VIN",
            width=0.5,
            layer="F.Cu"
        )

        # Generate 3D model
        model_path = os.path.join(self.test_dir, "power_supply_model.step")
        self.models.generate_3d_model(model_path)
        self.assertTrue(os.path.exists(model_path))

        # 5. Validation
        # Validate all aspects
        design_errors = self.design_workflow.validate_design()
        thermal_errors = self.thermal.validate_thermal_design()
        routing_errors = self.routing.validate_routing()
        
        self.assertIsInstance(design_errors, list)
        self.assertIsInstance(thermal_errors, list)
        self.assertIsInstance(routing_errors, list)

        # 6. Export
        export_path = os.path.join(self.test_dir, "export")
        self.design_workflow.export_design(export_path)
        self.assertTrue(os.path.exists(os.path.join(export_path, "design_state.json")))

    def test_error_handling_workflow(self):
        """Test error handling in complete workflows."""
        # 1. Template Management Errors
        with self.assertRaises(ValueError):
            self.template_manager.create_template(
                name="",  # Invalid empty name
                category="audio",
                description="Test template"
            )

        # 2. Design Workflow Errors
        with self.assertRaises(ValueError):
            self.design_workflow.add_component({
                "id": "",  # Invalid empty ID
                "type": "resistor",
                "value": "1k"
            })

        # 3. Signal Integrity Errors
        with self.assertRaises(ValueError):
            self.si_analyzer.analyze_impedance(
                board_path="nonexistent.kicad_pcb",
                net_name="VCC"
            )

        # 4. Manufacturing Errors
        with self.assertRaises(ValueError):
            self.thermal.create_thermal_zone(
                name="zone1",
                position=(-1.0, -1.0),  # Invalid position
                size=(20.0, 20.0)
            )

        # 5. Export Errors
        with self.assertRaises(ValueError):
            self.design_workflow.export_design("")  # Invalid path

        # 6. Validation Errors
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

    def test_falstad_import_workflow(self):
        """Test complete Falstad schematic import workflow."""
        # 1. Create test Falstad schematic
        falstad_path = os.path.join(self.test_dir, "test_circuit.json")
        self._create_test_falstad_schematic(falstad_path)
        
        # 2. Import schematic
        config = ImportConfig(
            apply_audio_optimizations=True,
            validate_schematic=True,
            generate_3d_models=True,
            optimize_placement=True,
            optimize_routing=True
        )
        
        pcb_path = self.schematic_importer.import_schematic(
            schematic_path=falstad_path,
            output_dir=self.test_dir,
            config=config
        )
        
        # Verify PCB was created
        self.assertTrue(os.path.exists(pcb_path))
        
        # 3. Load board for validation
        board = pcbnew.LoadBoard(pcb_path)

        # Initialize testers
        si_tester = SignalIntegrityTester(board)
        pg_tester = PowerGroundTester(board)
        emi_tester = EMIEMCTester(board)

        # Run comprehensive validation tests
        si_results = si_tester.test_signal_integrity()
        pg_results = pg_tester.test_power_ground()
        emi_results = emi_tester.test_emi_emc()

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
        
        # 4. Manufacturing Preparation
        # Create thermal zones
        self.thermal.create_thermal_zone(
            name="opamp_zone",
            position=(5.0, 5.0),
            size=(10.0, 10.0)
        )
        
        # Create differential pairs
        self.routing.create_differential_pair(
            name="audio_pair",
            net1="left_channel",
            net2="right_channel"
        )
        
        # Generate 3D model
        model_path = os.path.join(self.test_dir, "falstad_model.step")
        self.models.generate_3d_model(model_path)
        self.assertTrue(os.path.exists(model_path))
        
        # 5. Validation
        # Validate design
        design_errors = self.design_workflow.validate_design()
        self.assertIsInstance(design_errors, list)
        
        # Validate thermal design
        thermal_errors = self.thermal.validate_thermal_design()
        self.assertIsInstance(thermal_errors, list)
        
        # Validate routing
        routing_errors = self.routing.validate_routing()
        self.assertIsInstance(routing_errors, list)
        
        # 6. Export
        export_path = os.path.join(self.test_dir, "export")
        self.design_workflow.export_design(export_path)
        self.assertTrue(os.path.exists(os.path.join(export_path, "design_state.json")))
    
    def _create_test_falstad_schematic(self, path: str):
        """Create a test Falstad schematic file."""
        content = {
            "elements": [
                {
                    "type": "opamp",
                    "x": 100,
                    "y": 100,
                    "rotation": 0,
                    "value": "NE5532",
                    "properties": {
                        "supply_voltage": "±15V"
                    }
                },
                {
                    "type": "resistor",
                    "x": 200,
                    "y": 100,
                    "rotation": 0,
                    "value": "10k",
                    "properties": {
                        "tolerance": "1%"
                    }
                },
                {
                    "type": "capacitor",
                    "x": 300,
                    "y": 100,
                    "rotation": 0,
                    "value": "100n",
                    "properties": {
                        "voltage": "25V"
                    }
                }
            ],
            "wires": [
                {
                    "x1": 100,
                    "y1": 100,
                    "x2": 200,
                    "y2": 100
                },
                {
                    "x1": 200,
                    "y1": 100,
                    "x2": 300,
                    "y2": 100
                }
            ]
        }
        with open(path, 'w') as f:
            json.dump(content, f)

if __name__ == '__main__':
    unittest.main() 