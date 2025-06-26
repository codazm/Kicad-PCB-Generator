"""Unit tests for noise analysis functionality."""

import pytest
import numpy as np
from unittest.mock import Mock, patch
from kicad_pcb_generator.audio.simulation.noise_analysis import (
    AdvancedNoiseAnalyzer,
    NoiseSource,
    NoiseAnalysisResult,
    NoiseType
)

@pytest.fixture
def mock_circuit():
    """Create a mock circuit for testing."""
    circuit = Mock()
    circuit.components = {
        'R1': {'type': 'resistor', 'value': 10e3},
        'C1': {'type': 'capacitor', 'value': 1e-6},
        'Q1': {'type': 'transistor', 'model': '2N3904'}
    }
    return circuit

@pytest.fixture
def noise_analyzer(mock_circuit):
    """Create a noise analyzer instance for testing."""
    return AdvancedNoiseAnalyzer(mock_circuit)

def test_noise_analyzer_initialization(noise_analyzer, mock_circuit):
    """Test noise analyzer initialization."""
    assert noise_analyzer.circuit == mock_circuit
    assert noise_analyzer.logger is not None

def test_analyze_noise_basic(noise_analyzer):
    """Test basic noise analysis functionality."""
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    assert isinstance(result, NoiseAnalysisResult)
    assert isinstance(result.total_noise, np.ndarray)
    assert isinstance(result.noise_by_type, dict)
    assert len(result.frequency) == 100
    assert result.snr > 0
    assert result.noise_floor < 0
    assert result.noise_figure > 0
    assert len(result.noise_sources) > 0
    assert isinstance(result.metrics, dict)
    assert isinstance(result.warnings, list)
    assert isinstance(result.errors, list)

def test_analyze_noise_frequency_range(noise_analyzer):
    """Test noise analysis with different frequency ranges."""
    # Audio range
    result_audio = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    assert result_audio.frequency[0] == 20
    assert result_audio.frequency[-1] == 20e3
    
    # Extended range
    result_extended = noise_analyzer.analyze_noise(
        frequency_range=(1, 1e6),
        points=100
    )
    assert result_extended.frequency[0] == 1
    assert result_extended.frequency[-1] == 1e6

def test_analyze_noise_points(noise_analyzer):
    """Test noise analysis with different numbers of points."""
    for points in [10, 100, 1000]:
        result = noise_analyzer.analyze_noise(
            frequency_range=(20, 20e3),
            points=points
        )
        assert len(result.frequency) == points
        assert len(result.total_noise) == points

def test_noise_types(noise_analyzer):
    """Test that all noise types are analyzed."""
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    for noise_type in NoiseType:
        assert noise_type in result.noise_by_type
        assert isinstance(result.noise_by_type[noise_type], np.ndarray)
        assert len(result.noise_by_type[noise_type]) == 100

def test_noise_source_creation():
    """Test noise source creation and validation."""
    source = NoiseSource(
        type=NoiseType.THERMAL,
        location="R1",
        parameters={"temperature": 300, "resistance": 10e3},
        frequency_range=(20, 20e3),
        amplitude=1e-9
    )
    
    assert source.type == NoiseType.THERMAL
    assert source.location == "R1"
    assert source.parameters["temperature"] == 300
    assert source.parameters["resistance"] == 10e3
    assert source.frequency_range == (20, 20e3)
    assert source.amplitude == 1e-9
    assert source.phase == 0.0

def test_noise_metrics_calculation(noise_analyzer):
    """Test noise metrics calculation."""
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    # Check basic metrics
    assert "snr" in result.metrics
    assert "noise_floor" in result.metrics
    assert "noise_figure" in result.metrics
    assert "total_noise_power" in result.metrics
    assert "peak_noise" in result.metrics
    assert "noise_bandwidth" in result.metrics
    
    # Check metric ranges
    assert result.metrics["snr"] > 0
    assert result.metrics["noise_floor"] < 0
    assert result.metrics["noise_figure"] > 0
    assert result.metrics["total_noise_power"] > 0
    assert result.metrics["peak_noise"] > 0
    assert result.metrics["noise_bandwidth"] > 0

@patch('matplotlib.pyplot.show')
def test_plot_noise_analysis(mock_show, noise_analyzer):
    """Test noise analysis plotting."""
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    # Test plotting
    noise_analyzer.plot_noise_analysis(result)
    mock_show.assert_called_once()

def test_error_handling(noise_analyzer):
    """Test error handling in noise analysis."""
    # Test invalid frequency range
    with pytest.raises(ValueError):
        noise_analyzer.analyze_noise(
            frequency_range=(20e3, 20),  # Reversed range
            points=100
        )
    
    # Test invalid points
    with pytest.raises(ValueError):
        noise_analyzer.analyze_noise(
            frequency_range=(20, 20e3),
            points=0  # Invalid points
        )
    
    # Test missing component
    noise_analyzer.circuit.components = {}
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    assert len(result.warnings) > 0
    assert "No components found" in result.warnings[0]

def test_noise_source_contribution(noise_analyzer):
    """Test noise source contribution analysis."""
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    # Check that each noise source contributes to total noise
    total_noise = np.zeros_like(result.total_noise)
    for noise_type, noise in result.noise_by_type.items():
        total_noise += noise**2
    
    total_noise = np.sqrt(total_noise)
    np.testing.assert_allclose(
        result.total_noise,
        total_noise,
        rtol=1e-10
    )

def test_noise_analysis_caching(noise_analyzer):
    """Test noise analysis result caching."""
    # First analysis
    result1 = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    # Second analysis with same parameters
    result2 = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100
    )
    
    # Results should be identical
    np.testing.assert_array_equal(result1.total_noise, result2.total_noise)
    np.testing.assert_array_equal(result1.frequency, result2.frequency)
    
    # Different parameters should give different results
    result3 = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=200
    )
    assert len(result3.frequency) != len(result1.frequency)

def test_noise_analysis_performance(noise_analyzer):
    """Test noise analysis performance."""
    import time
    
    # Measure analysis time
    start_time = time.time()
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=1000
    )
    analysis_time = time.time() - start_time
    
    # Analysis should complete within 5 seconds
    assert analysis_time < 5.0
    
    # Cached analysis should be much faster
    start_time = time.time()
    result2 = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=1000
    )
    cached_time = time.time() - start_time
    
    assert cached_time < analysis_time / 10

def test_high_precision_frequency_analysis(noise_analyzer):
    """Test high-precision frequency analysis for extended audio bandwidth."""
    # Test extended bandwidth analysis up to 80kHz
    result_extended = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify extended bandwidth coverage
    assert result_extended.frequency[0] == 20
    assert result_extended.frequency[-1] == 80e3
    assert len(result_extended.frequency) >= 200
    
    # Test high-precision mode
    result_hp = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify high-precision characteristics
    assert hasattr(result_hp, 'high_precision_mode')
    assert result_hp.high_precision_mode is True
    assert hasattr(result_hp, 'extended_bandwidth_analysis')
    assert result_hp.extended_bandwidth_analysis is True
    
    # Test frequency distribution optimization
    frequencies = result_hp.frequency
    low_freq_count = sum(1 for f in frequencies if f <= 1000)
    mid_freq_count = sum(1 for f in frequencies if 1000 < f <= 20000)
    high_freq_count = sum(1 for f in frequencies if f > 20000)
    
    # Should have reasonable distribution across frequency ranges
    assert low_freq_count > 0
    assert mid_freq_count > 0
    assert high_freq_count > 0
    assert low_freq_count + mid_freq_count + high_freq_count == len(frequencies)

def test_extended_bandwidth_noise_components(noise_analyzer):
    """Test high-frequency noise components for extended bandwidth."""
    # Test noise analysis with high-frequency components
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify high-frequency noise components are present
    assert hasattr(result, 'high_frequency_noise')
    assert len(result.high_frequency_noise) > 0
    
    # Check that high-frequency noise is zero below 20kHz
    for i, freq in enumerate(result.frequency):
        if freq <= 20000:
            assert result.high_frequency_noise[i] == 0.0
        elif freq > 20000:
            assert result.high_frequency_noise[i] >= 0.0
    
    # Verify noise spectrum analysis
    assert hasattr(result, 'noise_spectrum_analysis')
    assert len(result.noise_spectrum_analysis) > 0

def test_high_precision_bandwidth_metrics(noise_analyzer):
    """Test high-precision bandwidth metrics calculation."""
    # Test bandwidth analysis with extended range
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify bandwidth metrics
    assert hasattr(result, 'bandwidth_analysis')
    if hasattr(result, 'bandwidth_analysis') and result.bandwidth_analysis:
        for net_analysis in result.bandwidth_analysis.values():
            assert 'low_freq_3db' in net_analysis
            assert 'high_freq_3db' in net_analysis
            assert 'bandwidth' in net_analysis
            assert 'extended_bandwidth' in net_analysis
            assert net_analysis['extended_bandwidth'] is True
            assert net_analysis['max_frequency'] >= 80000.0

def test_precision_metrics_calculation(noise_analyzer):
    """Test precision metrics calculation for high-precision analysis."""
    # Test precision metrics
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify precision metrics
    assert hasattr(result, 'precision_metrics')
    if hasattr(result, 'precision_metrics') and result.precision_metrics:
        metrics = result.precision_metrics
        assert 'frequency_range' in metrics
        assert 'resolution' in metrics
        assert 'bandwidth_coverage' in metrics
        assert 'precision_enhancements' in metrics
        
        # Check bandwidth coverage
        bandwidth_coverage = metrics['bandwidth_coverage']
        assert bandwidth_coverage['audio_bandwidth'] is True
        assert bandwidth_coverage['extended_bandwidth'] is True
        
        # Check precision enhancements
        precision_enhancements = metrics['precision_enhancements']
        assert precision_enhancements['high_precision_mode'] is True
        assert precision_enhancements['extended_analysis'] is True
        assert precision_enhancements['enhanced_resolution'] is True

def test_high_precision_noise_analysis_performance(noise_analyzer):
    """Test performance of high-precision noise analysis."""
    import time
    
    # Measure high-precision analysis time
    start_time = time.time()
    result_hp = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    hp_analysis_time = time.time() - start_time
    
    # Measure standard analysis time
    start_time = time.time()
    result_std = noise_analyzer.analyze_noise(
        frequency_range=(20, 20e3),
        points=100,
        high_precision=False
    )
    std_analysis_time = time.time() - start_time
    
    # High-precision analysis should complete within reasonable time
    assert hp_analysis_time < 10.0  # Should complete within 10 seconds
    
    # High-precision analysis should provide more detailed results
    assert len(result_hp.frequency) >= len(result_std.frequency)
    assert max(result_hp.frequency) >= max(result_std.frequency)

def test_extended_bandwidth_frequency_distribution(noise_analyzer):
    """Test optimized frequency distribution for extended bandwidth."""
    # Test frequency point generation
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    frequencies = result.frequency
    
    # Verify logarithmic distribution
    for i in range(1, len(frequencies)):
        assert frequencies[i] > frequencies[i-1]  # Monotonic increase
    
    # Verify coverage of critical frequency ranges
    low_freq_present = any(20 <= f <= 1000 for f in frequencies)
    mid_freq_present = any(1000 < f <= 20000 for f in frequencies)
    high_freq_present = any(20000 < f <= 80000 for f in frequencies)
    
    assert low_freq_present
    assert mid_freq_present
    assert high_freq_present
    
    # Verify frequency resolution
    freq_resolution = (max(frequencies) - min(frequencies)) / len(frequencies)
    assert freq_resolution > 0
    assert freq_resolution < 1000  # Reasonable resolution

def test_high_precision_noise_components(noise_analyzer):
    """Test high-precision noise component calculations."""
    # Test individual noise components with high precision
    result = noise_analyzer.analyze_noise(
        frequency_range=(20, 80e3),
        points=200,
        high_precision=True
    )
    
    # Verify all noise components are present
    assert hasattr(result, 'thermal_noise')
    assert hasattr(result, 'shot_noise')
    assert hasattr(result, 'flicker_noise')
    assert hasattr(result, 'high_frequency_noise')
    assert hasattr(result, 'total_noise')
    
    # Verify noise component characteristics
    for net_name in result.thermal_noise:
        thermal = result.thermal_noise[net_name]
        shot = result.shot_noise[net_name]
        flicker = result.flicker_noise[net_name]
        hf = result.high_frequency_noise[net_name]
        total = result.total_noise[net_name]
        
        # All noise components should be non-negative
        assert all(t >= 0 for t in thermal)
        assert all(s >= 0 for s in shot)
        assert all(f >= 0 for f in flicker)
        assert all(h >= 0 for h in hf)
        assert all(tot >= 0 for tot in total)
        
        # Total noise should be RMS sum of components
        for i in range(len(total)):
            expected_total = (thermal[i]**2 + shot[i]**2 + flicker[i]**2 + hf[i]**2)**0.5
            assert abs(total[i] - expected_total) < 1e-12  # Within numerical precision 
