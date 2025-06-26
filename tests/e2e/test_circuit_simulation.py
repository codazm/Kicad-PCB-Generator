"""End-to-end tests for circuit simulation and optimization."""

import unittest
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
import numpy as np
import PySpice
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pcbnew
from PySpice.Unit import u_V, u_A, u_Hz, u_s, u_F, u_H, u_Ohm

from kicad_pcb_generator.audio.optimization.advanced_circuit_optimizer import (
    AdvancedCircuitOptimizer,
    OptimizationType,
    SimulationResult
)
from kicad_pcb_generator.core.pcb import PCBGenerator
from kicad_pcb_generator.core.validation.base_validator import ValidationCategory
from kicad_pcb_generator.audio.simulation.circuit_simulator import CircuitSimulator, SimulationType
from kicad_pcb_generator.audio.analysis.analyzer import AudioPCBAnalyzer

class TestCircuitSimulation(unittest.TestCase):
    """End-to-end tests for circuit simulation and optimization."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.pcb_generator = PCBGenerator()
        
        # Create a test PCB file
        self.pcb_path = os.path.join(self.test_dir, "test_board.kicad_pcb")
        self.pcb_generator.create_new_board(self.pcb_path)
        
        # Initialize optimizer
        self.optimizer = AdvancedCircuitOptimizer(self.pcb_generator.board)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_audio_amplifier_simulation(self):
        """Test simulation of a complete audio amplifier circuit."""
        # Add components
        self.pcb_generator.add_component(
            ref="U1",
            value="NE5532",
            position=(0, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="R10k",
            position=(10, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="C1",
            value="C100n",
            position=(20, 0),
            layer="F.Cu"
        )
        
        # Add connections
        self.pcb_generator.add_trace(
            net_name="audio_in",
            start=(0, 0),
            end=(10, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="audio_out",
            start=(10, 0),
            end=(20, 0),
            width=0.2,
            layer="F.Cu"
        )
        
        # Run simulation
        result = self.optimizer.simulate_circuit()
        
        # Check simulation results
        self.assertIsInstance(result, SimulationResult)
        self.assertIn("frequencies", result.frequency_response)
        self.assertIn("magnitude", result.frequency_response)
        self.assertIn("phase", result.frequency_response)
        self.assertIn("frequencies", result.noise_analysis)
        self.assertIn("noise_floor", result.noise_analysis)
        self.assertIn("time", result.stability_analysis)
        self.assertIn("step_response", result.stability_analysis)
        
        # Check metrics
        self.assertIn("bandwidth", result.metrics)
        self.assertIn("noise_floor", result.metrics)
        self.assertIn("settling_time", result.metrics)
        
        # Verify reasonable values
        self.assertGreater(result.metrics["bandwidth"], 0)
        self.assertLess(result.metrics["noise_floor"], 0)  # Should be negative dB
        self.assertGreater(result.metrics["settling_time"], 0)
    
    def test_power_supply_simulation(self):
        """Test simulation of a power supply circuit."""
        # Add components
        self.pcb_generator.add_component(
            ref="U1",
            value="LM317",
            position=(0, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="C1",
            value="C100u",
            position=(10, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="R240",
            position=(20, 0),
            layer="F.Cu"
        )
        
        # Add connections
        self.pcb_generator.add_trace(
            net_name="VIN",
            start=(0, 0),
            end=(10, 0),
            width=0.5,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="VOUT",
            start=(10, 0),
            end=(20, 0),
            width=0.5,
            layer="F.Cu"
        )
        
        # Run simulation
        result = self.optimizer.simulate_circuit()
        
        # Check simulation results
        self.assertIsInstance(result, SimulationResult)
        
        # Check metrics
        self.assertIn("bandwidth", result.metrics)
        self.assertIn("noise_floor", result.metrics)
        self.assertIn("settling_time", result.metrics)
        
        # Verify reasonable values
        self.assertGreater(result.metrics["bandwidth"], 0)
        self.assertLess(result.metrics["noise_floor"], 0)  # Should be negative dB
        self.assertGreater(result.metrics["settling_time"], 0)
    
    def test_optimization_with_simulation(self):
        """Test circuit optimization with simulation feedback."""
        # Add components
        self.pcb_generator.add_component(
            ref="U1",
            value="NE5532",
            position=(0, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="R10k",
            position=(10, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="C1",
            value="C100n",
            position=(20, 0),
            layer="F.Cu"
        )
        
        # Add connections
        self.pcb_generator.add_trace(
            net_name="audio_in",
            start=(0, 0),
            end=(10, 0),
            width=0.2,
            layer="F.Cu"
        )
        self.pcb_generator.add_trace(
            net_name="audio_out",
            start=(10, 0),
            end=(20, 0),
            width=0.2,
            layer="F.Cu"
        )
        
        # Run optimization
        result = self.optimizer.optimize_circuit()
        
        # Check optimization results
        self.assertIsNotNone(result.simulation_result)
        self.assertIsInstance(result.simulation_result, SimulationResult)
        
        # Check optimization metrics
        self.assertIn("signal_quality", result.metrics)
        self.assertIn("power_quality", result.metrics)
        self.assertIn("ground_quality", result.metrics)
        self.assertIn("placement_quality", result.metrics)
        self.assertIn("thermal_quality", result.metrics)
        self.assertIn("emi_quality", result.metrics)
        
        # Verify reasonable values
        self.assertGreater(result.score, 0)
        self.assertLess(result.score, 1)
    
    def test_error_handling(self):
        """Test error handling in circuit simulation."""
        # Test with invalid component
        self.pcb_generator.add_component(
            ref="U1",
            value="INVALID",
            position=(0, 0),
            layer="F.Cu"
        )
        
        # Run simulation
        result = self.optimizer.simulate_circuit()
        
        # Check that simulation still returns results
        self.assertIsInstance(result, SimulationResult)
        self.assertIn("frequencies", result.frequency_response)
        self.assertIn("magnitude", result.frequency_response)
        self.assertIn("phase", result.frequency_response)
        
        # Test with missing connections
        self.pcb_generator.add_component(
            ref="R1",
            value="R10k",
            position=(10, 0),
            layer="F.Cu"
        )
        
        # Run simulation
        result = self.optimizer.simulate_circuit()
        
        # Check that simulation still returns results
        self.assertIsInstance(result, SimulationResult)
        self.assertIn("frequencies", result.frequency_response)
        self.assertIn("magnitude", result.frequency_response)
        self.assertIn("phase", result.frequency_response)
    
    def test_plot_simulation_results(self):
        """Test plotting of simulation results."""
        # Add test components
        self.pcb_generator.add_component(
            ref="U1",
            value="NE5532",
            position=(0, 0),
            layer="F.Cu"
        )
        self.pcb_generator.add_component(
            ref="R1",
            value="R10k",
            position=(10, 0),
            layer="F.Cu"
        )
        
        # Run simulation
        result = self.optimizer.simulate_circuit()
        
        # Create plot
        plot_path = os.path.join(self.test_dir, "simulation_results.png")
        self.optimizer.plot_simulation_results(result, Path(plot_path))
        
        # Check that plot was created
        self.assertTrue(os.path.exists(plot_path))
        self.assertTrue(os.path.getsize(plot_path) > 0)

if __name__ == "__main__":
    unittest.main() 