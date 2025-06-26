"""Tests for the advanced circuit optimizer."""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np
from pathlib import Path
import tempfile
import PySpice
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_V, u_A, u_Hz, u_s, u_F, u_H, u_Ohm

from kicad_pcb_generator.audio.optimization.advanced_circuit_optimizer import (
    AdvancedCircuitOptimizer,
    OptimizationType,
    SimulationResult
)

class TestAdvancedCircuitOptimizer(unittest.TestCase):
    """Test cases for the AdvancedCircuitOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = MagicMock()
        
        # Mock footprints
        self.resistor = MagicMock()
        type(self.resistor).GetReference = PropertyMock(return_value='R1')
        type(self.resistor).GetValue = PropertyMock(return_value='R10k')
        self.resistor.GetPads.return_value = [
            MagicMock(GetNetname=lambda: 'net1'),
            MagicMock(GetNetname=lambda: 'net2')
        ]
        
        self.capacitor = MagicMock()
        type(self.capacitor).GetReference = PropertyMock(return_value='C1')
        type(self.capacitor).GetValue = PropertyMock(return_value='C100n')
        self.capacitor.GetPads.return_value = [
            MagicMock(GetNetname=lambda: 'net2'),
            MagicMock(GetNetname=lambda: 'net3')
        ]
        
        self.transistor = MagicMock()
        type(self.transistor).GetReference = PropertyMock(return_value='Q1')
        type(self.transistor).GetValue = PropertyMock(return_value='Q2N2222')
        self.transistor.GetPads.return_value = [
            MagicMock(GetNetname=lambda: 'base'),
            MagicMock(GetNetname=lambda: 'collector'),
            MagicMock(GetNetname=lambda: 'emitter')
        ]
        
        self.board.GetFootprints.return_value = [
            self.resistor,
            self.capacitor,
            self.transistor
        ]
        
        self.optimizer = AdvancedCircuitOptimizer(self.board)
    
    def test_create_circuit(self):
        """Test circuit creation from KiCad board."""
        # Create circuit
        circuit = self.optimizer._create_circuit()
        
        # Check circuit type
        self.assertIsInstance(circuit, Circuit)
        
        # Check power supplies
        self.assertIn('VCC', circuit.elements)
        self.assertIn('VEE', circuit.elements)
        
        # Check components
        self.assertIn('R1', circuit.elements)
        self.assertIn('C1', circuit.elements)
        self.assertIn('Q1', circuit.elements)
    
    @patch('PySpice.Spice.Simulation.CircuitSimulator')
    def test_simulate_frequency_response(self, mock_simulator):
        """Test frequency response simulation."""
        # Mock simulation results
        mock_analysis = MagicMock()
        mock_analysis.__getitem__.return_value = np.array([1.0, 0.5, 0.25])
        mock_simulator.return_value.ac.return_value = mock_analysis
        
        # Generate test frequencies
        frequencies = np.logspace(1, 4, 3)
        
        # Run simulation
        result = self.optimizer._simulate_frequency_response(frequencies)
        
        # Check result structure
        self.assertIn("frequencies", result)
        self.assertIn("magnitude", result)
        self.assertIn("phase", result)
        
        # Check data types
        self.assertIsInstance(result["frequencies"], list)
        self.assertIsInstance(result["magnitude"], list)
        self.assertIsInstance(result["phase"], list)
        
        # Check data lengths
        self.assertEqual(len(result["frequencies"]), len(frequencies))
        self.assertEqual(len(result["magnitude"]), len(frequencies))
        self.assertEqual(len(result["phase"]), len(frequencies))
    
    @patch('PySpice.Spice.Simulation.CircuitSimulator')
    def test_simulate_noise(self, mock_simulator):
        """Test noise simulation."""
        # Mock simulation results
        mock_analysis = MagicMock()
        mock_analysis.__getitem__.return_value = np.array([1e-6, 2e-6, 3e-6])
        mock_simulator.return_value.noise.return_value = mock_analysis
        
        # Generate test frequencies
        frequencies = np.logspace(1, 4, 3)
        
        # Run simulation
        result = self.optimizer._simulate_noise(frequencies)
        
        # Check result structure
        self.assertIn("frequencies", result)
        self.assertIn("noise_floor", result)
        
        # Check data types
        self.assertIsInstance(result["frequencies"], list)
        self.assertIsInstance(result["noise_floor"], list)
        
        # Check data lengths
        self.assertEqual(len(result["frequencies"]), len(frequencies))
        self.assertEqual(len(result["noise_floor"]), len(frequencies))
    
    @patch('PySpice.Spice.Simulation.CircuitSimulator')
    def test_simulate_stability(self, mock_simulator):
        """Test stability simulation."""
        # Mock simulation results
        mock_analysis = MagicMock()
        mock_analysis.time = np.linspace(0, 1, 3)
        mock_analysis.__getitem__.return_value = np.array([0.0, 0.5, 1.0])
        mock_simulator.return_value.transient.return_value = mock_analysis
        
        # Run simulation
        result = self.optimizer._simulate_stability()
        
        # Check result structure
        self.assertIn("time", result)
        self.assertIn("step_response", result)
        
        # Check data types
        self.assertIsInstance(result["time"], list)
        self.assertIsInstance(result["step_response"], list)
        
        # Check data lengths
        self.assertEqual(len(result["time"]), 3)
        self.assertEqual(len(result["step_response"]), 3)
    
    def test_simulation_error_handling(self):
        """Test simulation error handling."""
        # Mock PySpice to raise an exception
        with patch('PySpice.Spice.Simulation.CircuitSimulator') as mock_simulator:
            mock_simulator.side_effect = Exception("Simulation failed")
            
            # Test frequency response simulation
            frequencies = np.logspace(1, 4, 3)
            result = self.optimizer._simulate_frequency_response(frequencies)
            self.assertIn("frequencies", result)
            self.assertIn("magnitude", result)
            self.assertIn("phase", result)
            
            # Test noise simulation
            result = self.optimizer._simulate_noise(frequencies)
            self.assertIn("frequencies", result)
            self.assertIn("noise_floor", result)
            
            # Test stability simulation
            result = self.optimizer._simulate_stability()
            self.assertIn("time", result)
            self.assertIn("step_response", result)
    
    def test_plot_simulation_results(self):
        """Test plotting of simulation results."""
        # Create test data
        result = SimulationResult(
            frequency_response={
                "frequencies": np.logspace(1, 4, 100).tolist(),
                "magnitude": (-20 * np.log10(1 + (np.logspace(1, 4, 100)/1000)**2)).tolist(),
                "phase": (-np.arctan(np.logspace(1, 4, 100)/1000) * 180/np.pi).tolist()
            },
            noise_analysis={
                "frequencies": np.logspace(1, 4, 100).tolist(),
                "noise_floor": (-100 + 10 * np.random.randn(100)).tolist()
            },
            stability_analysis={
                "time": np.linspace(0, 1, 1000).tolist(),
                "step_response": (1 - np.exp(-5 * np.linspace(0, 1, 1000))).tolist()
            },
            metrics={
                "bandwidth": 1000.0,
                "noise_floor": -90.0,
                "settling_time": 0.1
            },
            warnings=[],
            errors=[]
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            # Plot results
            self.optimizer.plot_simulation_results(result, Path(tmp.name))
            
            # Check if file was created
            self.assertTrue(Path(tmp.name).exists())
            self.assertTrue(Path(tmp.name).stat().st_size > 0)
    
    def test_optimize_circuit_with_simulation(self):
        """Test circuit optimization with simulation."""
        # Mock simulation results
        with patch.object(self.optimizer, '_simulate_frequency_response') as mock_freq, \
             patch.object(self.optimizer, '_simulate_noise') as mock_noise, \
             patch.object(self.optimizer, '_simulate_stability') as mock_stab:
            
            # Set up mock return values
            mock_freq.return_value = {
                "frequencies": [1000],
                "magnitude": [0],
                "phase": [0]
            }
            mock_noise.return_value = {
                "frequencies": [1000],
                "noise_floor": [-100]
            }
            mock_stab.return_value = {
                "time": [0, 1],
                "step_response": [0, 1]
            }
            
            # Run optimization
            result = self.optimizer.optimize_circuit()
            
            # Check simulation result
            self.assertIsNotNone(result.simulation_result)
            self.assertIsInstance(result.simulation_result, SimulationResult)
            
            # Check simulation metrics
            self.assertIn("bandwidth", result.simulation_result.metrics)
            self.assertIn("noise_floor", result.simulation_result.metrics)
            self.assertIn("settling_time", result.simulation_result.metrics)

if __name__ == "__main__":
    unittest.main() 
