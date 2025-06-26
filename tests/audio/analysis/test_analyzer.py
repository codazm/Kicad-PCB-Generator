"""Tests for audio analysis functionality."""

import pytest
from unittest.mock import Mock, patch
import pcbnew
import numpy as np
from pathlib import Path

from kicad_pcb_generator.audio.analysis.analyzer import (
    SignalIntegrityAnalysis,
    EMIAnalysis,
    AudioAnalyzer
)

@pytest.fixture
def mock_board():
    """Create a mock KiCad board with audio components."""
    board = Mock(spec=pcbnew.BOARD)
    
    # Create mock audio tracks
    audio_tracks = []
    for net in ['AUDIO_IN', 'AUDIO_OUT', 'POWER']:
        track = Mock(spec=pcbnew.TRACK)
        track.GetNetname.return_value = net
        track.GetWidth.return_value = 0.2e6  # 0.2mm
        track.GetStart.return_value = Mock(x=0, y=0)
        track.GetEnd.return_value = Mock(x=10e6, y=0)
        audio_tracks.append(track)
    
    board.GetTracks.return_value = audio_tracks
    
    return board

@pytest.fixture
def analyzer(mock_board):
    """Create an audio analyzer instance."""
    return AudioAnalyzer(mock_board)

def test_signal_integrity_analysis(analyzer):
    """Test signal integrity analysis functionality."""
    result = analyzer.analyze_signal_integrity()
    
    assert isinstance(result, SignalIntegrityAnalysis)
    assert len(result.crosstalk) == 3
    assert len(result.reflections) == 3
    assert len(result.impedance_mismatch) == 3
    assert len(result.signal_quality) == 3
    
    # Check that all metrics are within expected ranges
    for net_name in ['AUDIO_IN', 'AUDIO_OUT', 'POWER']:
        assert net_name in result.crosstalk
        assert net_name in result.reflections
        assert net_name in result.impedance_mismatch
        assert net_name in result.signal_quality
        
        assert -60 <= result.crosstalk[net_name] <= 0  # dB
        assert 0 <= result.reflections[net_name] <= 1
        assert 0 <= result.impedance_mismatch[net_name] <= 100  # %
        assert 0 <= result.signal_quality[net_name] <= 1

def test_emi_analysis(analyzer):
    """Test EMI/EMC analysis functionality."""
    result = analyzer.analyze_emi()
    
    assert isinstance(result, EMIAnalysis)
    assert len(result.radiated_emissions) == 100  # Number of frequency points
    assert len(result.conducted_emissions) == 100
    assert len(result.susceptibility) == 100
    assert isinstance(result.compliance_margin, float)
    
    # Check frequency range
    frequencies = list(result.radiated_emissions.keys())
    assert min(frequencies) >= 1e4  # 10kHz
    assert max(frequencies) <= 1e9  # 1GHz
    
    # Check that all metrics are within expected ranges
    for freq in frequencies:
        assert 0 <= result.radiated_emissions[freq] <= 100  # dBμV/m
        assert 0 <= result.conducted_emissions[freq] <= 100  # dBμV
        assert 0 <= result.susceptibility[freq] <= 100  # dBμV/m

def test_frequency_domain_analysis(analyzer):
    """Test frequency domain analysis functionality."""
    # Create test signal
    t = np.linspace(0, 1e-3, 1000)
    f1, f2 = 1e3, 10e3  # 1kHz and 10kHz
    signal = np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f2 * t)
    
    # Run analysis
    result = analyzer.analyze_frequency_domain(signal, 1e6)  # 1MHz sampling rate
    
    # Check results
    assert isinstance(result, dict)
    assert 'magnitude' in result
    assert 'phase' in result
    assert 'frequencies' in result
    
    # Verify frequency components
    frequencies = result['frequencies']
    magnitude = result['magnitude']
    
    # Should detect both frequency components
    peaks = np.where(magnitude > 0.1 * np.max(magnitude))[0]
    peak_freqs = frequencies[peaks]
    
    assert len(peaks) >= 2
    assert any(abs(f - f1) < 100 for f in peak_freqs)  # 1kHz component
    assert any(abs(f - f2) < 100 for f in peak_freqs)  # 10kHz component

def test_time_domain_analysis(analyzer):
    """Test time domain analysis functionality."""
    # Create test signal
    t = np.linspace(0, 1e-3, 1000)
    f = 1e3  # 1kHz
    signal = np.sin(2 * np.pi * f * t)
    
    # Run analysis
    result = analyzer.analyze_time_domain(signal, 1e6)  # 1MHz sampling rate
    
    # Check results
    assert isinstance(result, dict)
    assert 'rise_time' in result
    assert 'fall_time' in result
    assert 'overshoot' in result
    assert 'settling_time' in result
    
    # Verify timing parameters
    assert 0 < result['rise_time'] < 1e-3  # Rise time < 1ms
    assert 0 < result['fall_time'] < 1e-3  # Fall time < 1ms
    assert 0 <= result['overshoot'] <= 0.1  # Overshoot < 10%
    assert 0 < result['settling_time'] < 1e-3  # Settling time < 1ms

def test_noise_analysis(analyzer):
    """Test noise analysis functionality."""
    # Create test signal with noise
    t = np.linspace(0, 1e-3, 1000)
    f = 1e3  # 1kHz
    signal = np.sin(2 * np.pi * f * t) + 0.1 * np.random.randn(len(t))
    
    # Run analysis
    result = analyzer.analyze_noise(signal, 1e6)  # 1MHz sampling rate
    
    # Check results
    assert isinstance(result, dict)
    assert 'snr' in result
    assert 'thd' in result
    assert 'noise_floor' in result
    
    # Verify noise metrics
    assert result['snr'] > 20  # SNR > 20dB
    assert result['thd'] < 0.1  # THD < 10%
    assert result['noise_floor'] < -60  # Noise floor < -60dB

def test_analysis_error_handling(analyzer):
    """Test error handling in analysis functions."""
    # Test with invalid input
    with pytest.raises(ValueError):
        analyzer.analyze_frequency_domain([], 1e6)
    
    # Test with invalid sampling rate
    with pytest.raises(ValueError):
        analyzer.analyze_time_domain([1, 2, 3], 0)
    
    # Test with invalid signal type
    with pytest.raises(TypeError):
        analyzer.analyze_noise("invalid", 1e6)

def test_analysis_caching(analyzer):
    """Test analysis result caching."""
    # Run analysis twice
    result1 = analyzer.analyze_signal_integrity()
    result2 = analyzer.analyze_signal_integrity()
    
    # Results should be cached
    assert result1 is result2
    
    # Clear cache
    analyzer.clear_cache()
    
    # Run analysis again
    result3 = analyzer.analyze_signal_integrity()
    
    # Should get new results
    assert result3 is not result1 
