"""
Integration tests for signal integrity and crosstalk analysis.
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

from kicad_pcb_generator.core.signal_integrity import (
    SignalIntegrityAnalyzer,
    CrosstalkAnalyzer,
    SignalIntegrityConfig,
    CrosstalkConfig
)
from kicad_pcb_generator.core.pcb import PCBGenerator

class TestSignalIntegrityIntegration(unittest.TestCase):
    """Integration tests for signal integrity and crosstalk analysis."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.pcb_generator = PCBGenerator()
        self.si_analyzer = SignalIntegrityAnalyzer()
        self.xt_analyzer = CrosstalkAnalyzer()

        # Create a test PCB file
        self.pcb_path = os.path.join(self.test_dir, "test_board.kicad_pcb")
        self.pcb_generator.create_new_board(self.pcb_path)

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)

    def test_impedance_analysis(self):
        """Test impedance analysis functionality."""
        # Add test traces
        self.pcb_generator.add_trace(
            net_name="audio_in",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )

        # Analyze impedance
        results = self.si_analyzer.analyze_impedance(
            board_path=self.pcb_path,
            net_name="audio_in"
        )

        self.assertIsNotNone(results)
        self.assertIn("impedance", results)
        self.assertIn("mismatch", results)
        self.assertIn("recommendations", results)

    def test_reflection_analysis(self):
        """Test reflection analysis functionality."""
        # Add test traces with potential reflection points
        self.pcb_generator.add_trace(
            net_name="audio_out",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_via(
            net_name="audio_out",
            position=(50, 0),
            drill_size=0.4,
            pad_size=0.8
        )

        # Analyze reflections
        results = self.si_analyzer.analyze_reflections(
            board_path=self.pcb_path,
            net_name="audio_out"
        )

        self.assertIsNotNone(results)
        self.assertIn("reflection_points", results)
        self.assertIn("severity", results)
        self.assertIn("recommendations", results)

    def test_termination_analysis(self):
        """Test termination analysis functionality."""
        # Add test traces with terminations
        self.pcb_generator.add_trace(
            net_name="left_channel",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="100",
            position=(100, 0),
            layer="F.Cu"
        )

        # Analyze terminations
        results = self.si_analyzer.analyze_termination(
            board_path=self.pcb_path,
            net_name="left_channel"
        )

        self.assertIsNotNone(results)
        self.assertIn("termination_type", results)
        self.assertIn("effectiveness", results)
        self.assertIn("recommendations", results)

    def test_crosstalk_analysis(self):
        """Test crosstalk analysis functionality."""
        # Add parallel traces for crosstalk analysis
        self.pcb_generator.add_trace(
            net_name="signal1",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="signal2",
            start=(0, 0.5),
            end=(100, 0.5),
            width=0.2,
            layer="F.Cu"
        )

        # Analyze crosstalk
        results = self.xt_analyzer.analyze_crosstalk(
            board_path=self.pcb_path,
            net_name="signal1"
        )

        self.assertIsNotNone(results)
        self.assertIn("crosstalk_nets", results)
        self.assertIn("coupling_coefficients", results)
        self.assertIn("recommendations", results)

    def test_coupling_net_analysis(self):
        """Test coupling net analysis functionality."""
        # Add test traces
        self.pcb_generator.add_trace(
            net_name="sensitive_signal",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="aggressor1",
            start=(0, 0.5),
            end=(100, 0.5),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="aggressor2",
            start=(0, 1.0),
            end=(100, 1.0),
            width=0.2,
            layer="F.Cu"
        )

        # Find coupling nets
        results = self.xt_analyzer.find_coupling_nets(
            board_path=self.pcb_path,
            net_name="sensitive_signal"
        )

        self.assertIsNotNone(results)
        self.assertIn("coupling_nets", results)
        self.assertIn("coupling_strength", results)
        self.assertIn("recommendations", results)

    def test_coupling_coefficient_analysis(self):
        """Test coupling coefficient analysis functionality."""
        # Add test traces
        self.pcb_generator.add_trace(
            net_name="victim",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="aggressor",
            start=(0, 0.5),
            end=(100, 0.5),
            width=0.2,
            layer="F.Cu"
        )

        # Calculate coupling coefficients
        results = self.xt_analyzer.calculate_coupling_coefficients(
            board_path=self.pcb_path,
            net_name="victim"
        )

        self.assertIsNotNone(results)
        self.assertIn("coefficients", results)
        self.assertIn("severity", results)
        self.assertIn("recommendations", results)

    def test_configuration_updates(self):
        """Test configuration update functionality."""
        # Update signal integrity configuration
        si_config = SignalIntegrityConfig(
            min_impedance=45,
            max_impedance=55,
            max_reflection=-20,
            termination_threshold=0.8
        )
        self.si_analyzer.update_config(si_config)

        # Update crosstalk configuration
        xt_config = CrosstalkConfig(
            min_spacing=0.5,
            max_parallel_length=50,
            coupling_threshold=0.1
        )
        self.xt_analyzer.update_config(xt_config)

        # Verify configuration updates
        self.assertEqual(self.si_analyzer.config.min_impedance, 45)
        self.assertEqual(self.si_analyzer.config.max_impedance, 55)
        self.assertEqual(self.xt_analyzer.config.min_spacing, 0.5)
        self.assertEqual(self.xt_analyzer.config.max_parallel_length, 50)

    def test_comprehensive_analysis(self):
        """Test comprehensive signal integrity analysis."""
        # Add test traces for comprehensive analysis
        self.pcb_generator.add_trace(
            net_name="audio_signal",
            start=(0, 0),
            end=(100, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="noise_source",
            start=(0, 0.5),
            end=(100, 0.5),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="100",
            position=(100, 0),
            layer="F.Cu"
        )

        # Perform comprehensive analysis
        si_results = self.si_analyzer.analyze_impedance(
            board_path=self.pcb_path,
            net_name="audio_signal"
        )
        xt_results = self.xt_analyzer.analyze_crosstalk(
            board_path=self.pcb_path,
            net_name="audio_signal"
        )

        # Verify results
        self.assertIsNotNone(si_results)
        self.assertIsNotNone(xt_results)
        self.assertIn("impedance", si_results)
        self.assertIn("crosstalk_nets", xt_results)

if __name__ == '__main__':
    unittest.main() 