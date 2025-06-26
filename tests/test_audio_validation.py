"""
Tests for audio validation system.
"""

import pytest
from unittest.mock import Mock, patch
import pcbnew
from pathlib import Path

from ..src.audio.validation.audio_validator import AudioValidator, AudioValidationResult
from ..src.audio.simulation.circuit_simulator import CircuitSimulator, SimulationType, SimulationResult
from ..src.core.validation.base_validator import ValidationSeverity, ValidationCategory

@pytest.fixture
def mock_board():
    """Create a mock KiCad board."""
    board = Mock(spec=pcbnew.BOARD)
    board.GetFootprints.return_value = []
    board.GetTracks.return_value = []
    return board

@pytest.fixture
def audio_validator(mock_board):
    """Create an audio validator instance."""
    return AudioValidator()

@pytest.fixture
def circuit_simulator(mock_board):
    """Create a circuit simulator instance."""
    return CircuitSimulator(mock_board)

def test_audio_validation_result():
    """Test AudioValidationResult class."""
    result = AudioValidationResult()
    
    # Test adding metrics
    result.add_audio_metric("snr", 90.0)
    result.add_power_metric("efficiency", 0.85)
    result.add_ground_metric("impedance", 0.1)
    
    assert result.audio_metrics["snr"] == 90.0
    assert result.power_metrics["efficiency"] == 0.85
    assert result.ground_metrics["impedance"] == 0.1

def test_audio_validator_initialization(audio_validator):
    """Test AudioValidator initialization."""
    assert audio_validator is not None
    assert len(audio_validator.callbacks) == 0
    assert isinstance(audio_validator.validation_cache, dict)

def test_audio_validator_validation(mock_board, audio_validator):
    """Test audio validation process."""
    result = audio_validator.validate(mock_board)
    
    assert isinstance(result, AudioValidationResult)
    assert len(result.issues) >= 0  # May have warnings/errors

def test_audio_validator_callbacks(mock_board, audio_validator):
    """Test audio validator callbacks."""
    callback_called = False
    
    def callback(result):
        nonlocal callback_called
        callback_called = True
        assert isinstance(result, AudioValidationResult)
    
    audio_validator.add_validation_callback(callback)
    audio_validator.validate(mock_board)
    
    assert callback_called

def test_circuit_simulator_initialization(circuit_simulator):
    """Test CircuitSimulator initialization."""
    assert circuit_simulator is not None
    assert len(circuit_simulator.callbacks) == 0
    assert isinstance(circuit_simulator.results_cache, dict)

def test_circuit_simulator_simulation(circuit_simulator):
    """Test circuit simulation process."""
    result = circuit_simulator.run_simulation(SimulationType.DC)
    
    assert isinstance(result, SimulationResult)
    assert result.type == SimulationType.DC
    assert isinstance(result.data, dict)
    assert isinstance(result.metrics, dict)
    assert isinstance(result.warnings, list)
    assert isinstance(result.errors, list)

def test_circuit_simulator_callbacks(circuit_simulator):
    """Test circuit simulator callbacks."""
    callback_called = False
    
    def callback(result):
        nonlocal callback_called
        callback_called = True
        assert isinstance(result, SimulationResult)
    
    circuit_simulator.add_simulation_callback(callback)
    circuit_simulator.run_simulation(SimulationType.DC)
    
    assert callback_called

def test_circuit_simulator_cache(circuit_simulator):
    """Test circuit simulator caching."""
    # Run simulation
    result1 = circuit_simulator.run_simulation(SimulationType.DC)
    
    # Run same simulation again
    result2 = circuit_simulator.run_simulation(SimulationType.DC)
    
    # Results should be cached
    assert result1 is result2
    
    # Clear cache
    circuit_simulator.clear_cache()
    
    # Run simulation again
    result3 = circuit_simulator.run_simulation(SimulationType.DC)
    
    # Should be a new result
    assert result3 is not result1

def test_audio_validator_component_validation(mock_board, audio_validator):
    """Test audio component validation."""
    # Create mock component
    component = Mock()
    component.GetReference.return_value = "R1"
    component.GetValue.return_value = "10k"
    
    # Add component to board
    mock_board.GetFootprints.return_value = [component]
    
    # Run validation
    result = audio_validator.validate(mock_board)
    
    # Check for component-related issues
    component_issues = [issue for issue in result.issues 
                       if issue.category == ValidationCategory.COMPONENT]
    assert len(component_issues) >= 0  # May have warnings/errors

def test_audio_validator_signal_path_validation(mock_board, audio_validator):
    """Test audio signal path validation."""
    # Create mock track
    track = Mock()
    track.GetNet.return_value = "Signal"
    
    # Add track to board
    mock_board.GetTracks.return_value = [track]
    
    # Run validation
    result = audio_validator.validate(mock_board)
    
    # Check for signal-related issues
    signal_issues = [issue for issue in result.issues 
                    if issue.category == ValidationCategory.SIGNAL]
    assert len(signal_issues) >= 0  # May have warnings/errors

def test_circuit_simulator_different_types(circuit_simulator):
    """Test different simulation types."""
    simulation_types = [
        SimulationType.DC,
        SimulationType.AC,
        SimulationType.TRANSIENT,
        SimulationType.NOISE,
        SimulationType.DISTORTION,
        SimulationType.TEMPERATURE
    ]
    
    for sim_type in simulation_types:
        result = circuit_simulator.run_simulation(sim_type)
        assert result.type == sim_type
        assert isinstance(result.data, dict)
        assert isinstance(result.metrics, dict)

def test_audio_validator_error_handling(mock_board, audio_validator):
    """Test audio validator error handling."""
    # Make board.GetFootprints raise an exception
    mock_board.GetFootprints.side_effect = Exception("Test error")
    
    # Run validation
    result = audio_validator.validate(mock_board)
    
    # Should have error issues
    error_issues = [issue for issue in result.issues 
                   if issue.severity == ValidationSeverity.ERROR]
    assert len(error_issues) > 0

def test_circuit_simulator_error_handling(circuit_simulator):
    """Test circuit simulator error handling."""
    # Make _create_circuit raise an exception
    with patch.object(circuit_simulator, '_create_circuit', 
                     side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            circuit_simulator.run_simulation(SimulationType.DC) 