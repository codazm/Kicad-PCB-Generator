"""
Tests for advanced noise analysis functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from ...src.audio.simulation.noise_analysis import (
    AdvancedNoiseAnalyzer,
    NoiseType,
    NoiseSource,
    NoiseAnalysisResult
)

@pytest.fixture
def mock_circuit():
    """Create a mock circuit with components."""
    circuit = Mock()
    
    # Mock resistors
    circuit.resistors = [
        Mock(name='R1', value=1000),  # 1kΩ
        Mock(name='R2', value=10000),  # 10kΩ
    ]
    
    # Mock active devices
    circuit.active_devices = [
        Mock(name='Q1', current=1e-3),  # 1mA
        Mock(name='Q2', current=2e-3),  # 2mA
    ]
    
    return circuit

@pytest.fixture
def noise_analyzer(mock_circuit):
    """Create a noise analyzer instance."""
    return AdvancedNoiseAnalyzer(mock_circuit)

def test_noise_source_initialization(noise_analyzer):
    """Test initialization of noise sources."""
    # Check that all expected noise sources are created
    assert len(noise_analyzer.noise_sources) > 0
    
    # Check thermal noise sources
    thermal_sources = [s for s in noise_analyzer.noise_sources 
                      if s.type == NoiseType.THERMAL]
    assert len(thermal_sources) == 2  # One for each resistor
    
    # Check shot noise sources
    shot_sources = [s for s in noise_analyzer.noise_sources 
                   if s.type == NoiseType.SHOT]
    assert len(shot_sources) == 2  # One for each active device
    
    # Check flicker noise sources
    flicker_sources = [s for s in noise_analyzer.noise_sources 
                      if s.type == NoiseType.FLICKER]
    assert len(flicker_sources) == 2  # One for each active device

def test_thermal_noise_calculation(noise_analyzer):
    """Test thermal noise calculation."""
    # Test with standard values
    noise = noise_analyzer._calculate_thermal_noise(1000, 300)  # 1kΩ at 300K
    assert noise > 0
    assert isinstance(noise, float)
    
    # Test with zero resistance
    noise = noise_analyzer._calculate_thermal_noise(0, 300)
    assert noise == 0
    
    # Test with zero temperature
    noise = noise_analyzer._calculate_thermal_noise(1000, 0)
    assert noise == 0

def test_shot_noise_calculation(noise_analyzer):
    """Test shot noise calculation."""
    # Test with standard values
    noise = noise_analyzer._calculate_shot_noise(1e-3)  # 1mA
    assert noise > 0
    assert isinstance(noise, float)
    
    # Test with zero current
    noise = noise_analyzer._calculate_shot_noise(0)
    assert noise == 0

def test_flicker_noise_calculation(noise_analyzer):
    """Test flicker noise calculation."""
    # Test with standard values
    noise = noise_analyzer._calculate_flicker_noise(1e-12, 1.0, 1000)
    assert noise > 0
    assert isinstance(noise, float)
    
    # Test with zero frequency
    with pytest.raises(ZeroDivisionError):
        noise_analyzer._calculate_flicker_noise(1e-12, 1.0, 0)

def test_noise_analysis(noise_analyzer):
    """Test complete noise analysis."""
    # Run analysis
    result = noise_analyzer.analyze_noise(
        frequency_range=(1, 1e6),
        points=100
    )
    
    # Check result structure
    assert isinstance(result, NoiseAnalysisResult)
    assert isinstance(result.total_noise, np.ndarray)
    assert isinstance(result.noise_by_type, dict)
    assert isinstance(result.frequency, np.ndarray)
    assert isinstance(result.snr, float)
    assert isinstance(result.noise_floor, float)
    assert isinstance(result.noise_figure, float)
    
    # Check array shapes
    assert len(result.frequency) == 100
    assert result.total_noise.shape == result.frequency.shape
    for noise in result.noise_by_type.values():
        assert noise.shape == result.frequency.shape
    
    # Check metrics
    assert result.snr > 0
    assert result.noise_floor < 0  # Should be negative in dB
    assert result.noise_figure > 0

def test_noise_analysis_error_handling(noise_analyzer):
    """Test error handling in noise analysis."""
    # Test with invalid frequency range
    result = noise_analyzer.analyze_noise(
        frequency_range=(1e6, 1),  # Invalid range
        points=100
    )
    assert len(result.errors) > 0
    
    # Test with zero points
    result = noise_analyzer.analyze_noise(
        frequency_range=(1, 1e6),
        points=0
    )
    assert len(result.errors) > 0

def test_noise_plotting(noise_analyzer):
    """Test noise analysis plotting."""
    # Run analysis
    result = noise_analyzer.analyze_noise(
        frequency_range=(1, 1e6),
        points=100
    )
    
    # Test plotting
    with patch('matplotlib.pyplot.show') as mock_show:
        noise_analyzer.plot_noise_analysis(result)
        mock_show.assert_called_once()

def test_noise_metrics_calculation(noise_analyzer):
    """Test calculation of noise metrics."""
    # Create test data
    freq = np.logspace(0, 6, 100)
    noise = np.ones_like(freq) * 1e-6  # 1µV/√Hz
    
    # Test SNR calculation
    snr = noise_analyzer._calculate_snr(noise)
    assert isinstance(snr, float)
    assert snr > 0
    
    # Test noise figure calculation
    nf = noise_analyzer._calculate_noise_figure(noise)
    assert isinstance(nf, float)
    assert nf > 0
    
    # Test noise bandwidth calculation
    bw = noise_analyzer._calculate_noise_bandwidth(freq, noise)
    assert isinstance(bw, float)
    assert bw > 0

def test_integration_with_circuit_simulator():
    """Test integration with CircuitSimulator."""
    from ...src.audio.simulation.circuit_simulator import CircuitSimulator
    
    # Create mock board
    board = Mock()
    
    # Create simulator
    simulator = CircuitSimulator(board)
    
    # Create mock circuit
    circuit = Mock()
    circuit.resistors = [Mock(name='R1', value=1000)]
    circuit.active_devices = [Mock(name='Q1', current=1e-3)]
    
    # Run noise simulation
    result = simulator._run_noise_simulation(
        circuit,
        start_frequency=1,
        stop_frequency=1e6,
        number_of_points=100,
        plot=True
    )
    
    # Check result
    assert result.type == 'noise'
    assert 'frequency' in result.data
    assert 'noise' in result.data
    assert 'noise_by_type' in result.data
    assert 'snr' in result.metrics
    assert 'noise_floor' in result.metrics
    assert 'noise_figure' in result.metrics 