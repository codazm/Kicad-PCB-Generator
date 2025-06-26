"""
End-to-end tests for noise analysis functionality.
"""

import pytest
import numpy as np
from pathlib import Path
import pcbnew
from ...src.audio.simulation.circuit_simulator import CircuitSimulator
from ...src.audio.simulation.noise_analysis import (
    AdvancedNoiseAnalyzer,
    NoiseType,
    NoiseAnalysisResult
)

@pytest.fixture
def test_board():
    """Create a test board with audio components."""
    board = pcbnew.BOARD()
    
    # Add test components
    # Resistors
    r1 = board.Add(pcbnew.FOOTPRINT())
    r1.SetReference('R1')
    r1.SetValue('1k')
    
    r2 = board.Add(pcbnew.FOOTPRINT())
    r2.SetReference('R2')
    r2.SetValue('10k')
    
    # Active devices
    q1 = board.Add(pcbnew.FOOTPRINT())
    q1.SetReference('Q1')
    q1.SetValue('2N3904')
    
    q2 = board.Add(pcbnew.FOOTPRINT())
    q2.SetReference('Q2')
    q2.SetValue('2N3906')
    
    # Add connections
    track1 = board.Add(pcbnew.TRACK())
    track1.SetStart(pcbnew.VECTOR2I(0, 0))
    track1.SetEnd(pcbnew.VECTOR2I(1000, 0))
    track1.SetNetCode(1)
    
    track2 = board.Add(pcbnew.TRACK())
    track2.SetStart(pcbnew.VECTOR2I(1000, 0))
    track2.SetEnd(pcbnew.VECTOR2I(2000, 0))
    track2.SetNetCode(1)
    
    return board

@pytest.fixture
def circuit_simulator(test_board):
    """Create a circuit simulator instance."""
    return CircuitSimulator(test_board)

def test_noise_analysis_workflow(circuit_simulator):
    """Test complete noise analysis workflow."""
    # Create circuit
    circuit = circuit_simulator._create_circuit()
    
    # Run noise analysis
    result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=1000,
        plot=True
    )
    
    # Verify results
    assert result.type == 'noise'
    assert 'frequency' in result.data
    assert 'noise' in result.data
    assert 'noise_by_type' in result.data
    
    # Check metrics
    assert 'snr' in result.metrics
    assert 'noise_floor' in result.metrics
    assert 'noise_figure' in result.metrics
    assert 'total_noise_power' in result.metrics
    assert 'peak_noise' in result.metrics
    assert 'noise_bandwidth' in result.metrics
    
    # Verify data types and shapes
    assert isinstance(result.data['frequency'], np.ndarray)
    assert isinstance(result.data['noise'], np.ndarray)
    assert len(result.data['frequency']) == 1000
    assert result.data['frequency'].shape == result.data['noise'].shape
    
    # Check noise by type
    for noise_type in NoiseType:
        assert noise_type.value in result.data['noise_by_type']
        assert isinstance(result.data['noise_by_type'][noise_type.value], np.ndarray)
        assert result.data['noise_by_type'][noise_type.value].shape == result.data['frequency'].shape

def test_noise_analysis_with_real_components(circuit_simulator):
    """Test noise analysis with real audio components."""
    # Create circuit with audio components
    circuit = circuit_simulator._create_circuit()
    
    # Add audio-specific components
    # Op-amp
    opamp = circuit.IC('U1', 'OPA1612')
    
    # Audio capacitors
    c1 = circuit.C('C1', 1e-6)  # 1µF
    c2 = circuit.C('C2', 10e-6)  # 10µF
    
    # Run noise analysis
    result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=20,  # Audio range
        stop_frequency=20e3,
        number_of_points=1000,
        plot=True
    )
    
    # Verify audio-specific metrics
    assert result.metrics['snr'] > 60  # Good audio SNR
    assert result.metrics['noise_floor'] < -100  # Good noise floor
    assert result.metrics['noise_figure'] < 3  # Good noise figure

def test_noise_analysis_error_handling(circuit_simulator):
    """Test error handling in noise analysis workflow."""
    # Test with invalid frequency range
    circuit = circuit_simulator._create_circuit()
    result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1e6,
        stop_frequency=1,  # Invalid range
        number_of_points=1000
    )
    assert len(result.errors) > 0
    
    # Test with zero points
    result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=0
    )
    assert len(result.errors) > 0
    
    # Test with empty circuit
    empty_circuit = pcbnew.BOARD()
    empty_simulator = CircuitSimulator(empty_circuit)
    result = empty_simulator._run_noise_simulation(
        empty_simulator._create_circuit(),
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=1000
    )
    assert len(result.warnings) > 0

def test_noise_analysis_performance(circuit_simulator):
    """Test noise analysis performance."""
    import time
    
    # Create circuit
    circuit = circuit_simulator._create_circuit()
    
    # Measure analysis time
    start_time = time.time()
    result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=1000
    )
    end_time = time.time()
    
    # Verify performance
    analysis_time = end_time - start_time
    assert analysis_time < 5.0  # Should complete within 5 seconds
    
    # Verify results are cached
    start_time = time.time()
    cached_result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=1000
    )
    end_time = time.time()
    
    # Cached results should be much faster
    cached_time = end_time - start_time
    assert cached_time < analysis_time * 0.1  # At least 10x faster

def test_noise_analysis_integration(circuit_simulator):
    """Test integration with other simulation types."""
    circuit = circuit_simulator._create_circuit()
    
    # Run DC analysis first
    dc_result = circuit_simulator._run_dc_simulation(circuit)
    assert dc_result.type == 'dc'
    
    # Run noise analysis
    noise_result = circuit_simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=1000
    )
    assert noise_result.type == 'noise'
    
    # Verify metrics are consistent
    assert 'power_dissipation' in dc_result.metrics
    assert 'total_noise_power' in noise_result.metrics
    
    # Run AC analysis
    ac_result = circuit_simulator._run_ac_simulation(circuit)
    assert ac_result.type == 'ac'
    
    # Verify frequency responses are consistent
    assert len(ac_result.data['frequency']) == len(noise_result.data['frequency'])
    assert np.allclose(ac_result.data['frequency'], noise_result.data['frequency']) 