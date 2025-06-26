"""
Unit tests for the circuit simulator module.
"""

import unittest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile
import shutil
import numpy as np

from kicad_pcb_generator.audio.simulation.circuit_simulator import (
    CircuitSimulator,
    SimulationType,
    SimulationResult
)

class TestCircuitSimulator(unittest.TestCase):
    """Test cases for the CircuitSimulator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_board = Mock()
        self.mock_board.GetFileName.return_value = "test_board.kicad_pcb"
        self.mock_board.GetFootprints.return_value = []
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create simulator instance
        self.simulator = CircuitSimulator(self.mock_board)
        self.simulator.temp_dir = self.test_dir
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """Test simulator initialization."""
        self.assertEqual(self.simulator.board, self.mock_board)
        self.assertIsNotNone(self.simulator.temp_dir)
        self.assertIsInstance(self.simulator.settings, dict)
        self.assertIsInstance(self.simulator.models, dict)
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_load_component_models(self, mock_listdir, mock_exists):
        """Test loading component models."""
        # Mock model files
        mock_exists.return_value = True
        mock_listdir.return_value = ["model1.lib", "model2.lib"]
        
        # Mock file content
        mock_content = "* Test model\n.model test_model\n"
        
        with patch('builtins.open', mock_open(read_data=mock_content)):
            self.simulator._load_component_models()
            
        self.assertEqual(len(self.simulator.models), 2)
        self.assertIn("model1.lib", self.simulator.models)
        self.assertIn("model2.lib", self.simulator.models)
    
    def test_generate_netlist(self):
        """Test netlist generation."""
        # Add a mock model
        self.simulator.models["test.lib"] = "* Test model\n.model test_model\n"
        
        # Add a mock footprint
        mock_footprint = Mock()
        mock_footprint.GetReference.return_value = "R1"
        mock_footprint.GetValue.return_value = "test_model"
        self.mock_board.GetFootprints.return_value = [mock_footprint]
        
        netlist = self.simulator._generate_netlist()
        
        self.assertIn("Netlist for test_board.kicad_pcb", netlist)
        self.assertIn("Test model", netlist)
        self.assertIn("Component: R1 (test_model)", netlist)
    
    def test_get_analysis_commands(self):
        """Test generation of analysis commands."""
        commands = self.simulator._get_analysis_commands()
        
        self.assertIn(".dc", commands)
        self.assertIn(".ac", commands)
        self.assertIn(".tran", commands)
        self.assertIn(".noise", commands)
    
    @patch('subprocess.Popen')
    def test_run_simulation_success(self, mock_popen):
        """Test successful simulation run."""
        # Mock successful simulation
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ("Simulation output", "")
        mock_popen.return_value = mock_process
        
        result = self.simulator.run_simulation(SimulationType.DC)
        
        self.assertTrue(result.success)
        self.assertEqual(result.type, SimulationType.DC)
        self.assertEqual(result.errors, [])
    
    @patch('subprocess.Popen')
    def test_run_simulation_failure(self, mock_popen):
        """Test failed simulation run."""
        # Mock failed simulation
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = ("", "Simulation error")
        mock_popen.return_value = mock_process
        
        result = self.simulator.run_simulation(SimulationType.DC)
        
        self.assertFalse(result.success)
        self.assertEqual(result.type, SimulationType.DC)
        self.assertEqual(result.errors, ["Simulation error"])
    
    def test_cleanup(self):
        """Test cleanup of temporary files."""
        # Create a test file in temp directory
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        self.simulator.cleanup()
        
        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(self.test_dir))

if __name__ == '__main__':
    unittest.main() 