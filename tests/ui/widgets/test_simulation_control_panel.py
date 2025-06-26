"""Unit tests for simulation control panel widget."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import numpy as np
from unittest.mock import Mock, patch

from kicad_pcb_generator.ui.widgets.simulation_control_panel import (
    SimulationControlPanel,
    SimulationPlotWidget
)
from kicad_pcb_generator.audio.simulation import (
    CircuitSimulator,
    SimulationType,
    SimulationResult
)

@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication([])

@pytest.fixture
def mock_simulator():
    """Create mock circuit simulator."""
    simulator = Mock(spec=CircuitSimulator)
    return simulator

@pytest.fixture
def control_panel(app, mock_simulator):
    """Create simulation control panel instance."""
    panel = SimulationControlPanel()
    panel.set_simulator(mock_simulator)
    return panel

@pytest.fixture
def plot_widget(app):
    """Create simulation plot widget instance."""
    return SimulationPlotWidget()

def test_control_panel_initialization(control_panel):
    """Test control panel initialization."""
    assert control_panel.simulator is not None
    assert control_panel.type_combo.count() == len(SimulationType)
    assert control_panel.start_freq.value() == 20
    assert control_panel.stop_freq.value() == 20e3
    assert control_panel.points_spin.value() == 1000
    assert control_panel.plot_check.isChecked()
    assert control_panel.cache_check.isChecked()
    assert not control_panel.stop_button.isEnabled()
    assert not control_panel.progress.isVisible()

def test_plot_widget_initialization(plot_widget):
    """Test plot widget initialization."""
    assert plot_widget.figure is not None
    assert plot_widget.canvas is not None

def test_run_simulation(control_panel, mock_simulator):
    """Test running simulation."""
    # Mock simulation result
    result = SimulationResult(
        simulation_type=SimulationType.NOISE,
        status="completed",
        duration=1.0,
        frequency=np.logspace(1, 5, 100),
        total_noise=np.ones(100) * 1e-9,
        noise_by_type={
            SimulationType.THERMAL: np.ones(100) * 1e-9,
            SimulationType.SHOT: np.ones(100) * 1e-10
        },
        metrics={
            "snr": 100,
            "noise_floor": -120,
            "noise_figure": 1.0
        },
        warnings=[],
        errors=[]
    )
    mock_simulator.run_simulation.return_value = result
    
    # Run simulation
    control_panel._run_simulation()
    
    # Check simulator was called
    mock_simulator.run_simulation.assert_called_once()
    
    # Check UI updates
    assert control_panel.run_button.isEnabled()
    assert not control_panel.stop_button.isEnabled()
    assert not control_panel.progress.isVisible()
    
    # Check results display
    assert "SNR: 100.0 dB" in control_panel.metrics_text.toPlainText()
    assert "Noise Floor: -120.0 dBV/√Hz" in control_panel.metrics_text.toPlainText()
    assert "Noise Figure: 1.0 dB" in control_panel.metrics_text.toPlainText()

def test_stop_simulation(control_panel, mock_simulator):
    """Test stopping simulation."""
    control_panel._stop_simulation()
    mock_simulator.stop_simulation.assert_called_once()
    assert "Simulation stopped by user" in control_panel.log_text.toPlainText()

def test_plot_noise_results(plot_widget):
    """Test plotting noise analysis results."""
    result = SimulationResult(
        simulation_type=SimulationType.NOISE,
        status="completed",
        duration=1.0,
        frequency=np.logspace(1, 5, 100),
        total_noise=np.ones(100) * 1e-9,
        noise_by_type={
            SimulationType.THERMAL: np.ones(100) * 1e-9,
            SimulationType.SHOT: np.ones(100) * 1e-10
        },
        metrics={},
        warnings=[],
        errors=[]
    )
    
    plot_widget.plot_results(result)
    assert len(plot_widget.figure.axes) == 1

def test_plot_ac_results(plot_widget):
    """Test plotting AC analysis results."""
    result = SimulationResult(
        simulation_type=SimulationType.AC,
        status="completed",
        duration=1.0,
        frequency=np.logspace(1, 5, 100),
        magnitude=np.ones(100),
        phase=np.zeros(100),
        metrics={},
        warnings=[],
        errors=[]
    )
    
    plot_widget.plot_results(result)
    assert len(plot_widget.figure.axes) == 1

def test_plot_dc_results(plot_widget):
    """Test plotting DC analysis results."""
    result = SimulationResult(
        simulation_type=SimulationType.DC,
        status="completed",
        duration=1.0,
        dc_operating_points={"V1": 5.0, "V2": 3.3},
        metrics={},
        warnings=[],
        errors=[]
    )
    
    plot_widget.plot_results(result)
    assert len(plot_widget.figure.axes) == 1

def test_plot_transient_results(plot_widget):
    """Test plotting transient analysis results."""
    result = SimulationResult(
        simulation_type=SimulationType.TRANSIENT,
        status="completed",
        duration=1.0,
        time=np.linspace(0, 1, 100),
        time_domain={"V1": np.sin(np.linspace(0, 2*np.pi, 100))},
        metrics={},
        warnings=[],
        errors=[]
    )
    
    plot_widget.plot_results(result)
    assert len(plot_widget.figure.axes) == 1

def test_simulation_error_handling(control_panel, mock_simulator):
    """Test simulation error handling."""
    mock_simulator.run_simulation.side_effect = Exception("Test error")
    
    # Run simulation
    control_panel._run_simulation()
    
    # Check error handling
    assert "Error: Test error" in control_panel.log_text.toPlainText()
    assert control_panel.run_button.isEnabled()
    assert not control_panel.stop_button.isEnabled()
    assert not control_panel.progress.isVisible()

def test_parameter_validation(control_panel):
    """Test parameter validation."""
    # Test invalid frequency range
    control_panel.start_freq.setValue(20e3)
    control_panel.stop_freq.setValue(20)
    
    # Run simulation
    control_panel._run_simulation()
    
    # Check error handling
    assert "Error" in control_panel.log_text.toPlainText()
    
    # Test invalid points
    control_panel.start_freq.setValue(20)
    control_panel.stop_freq.setValue(20e3)
    control_panel.points_spin.setValue(0)
    
    # Run simulation
    control_panel._run_simulation()
    
    # Check error handling
    assert "Error" in control_panel.log_text.toPlainText()

def test_simulation_signals(control_panel, mock_simulator):
    """Test simulation signals."""
    # Mock signal handlers
    started = Mock()
    completed = Mock()
    error = Mock()
    
    control_panel.simulation_started.connect(started)
    control_panel.simulation_completed.connect(completed)
    control_panel.simulation_error.connect(error)
    
    # Run successful simulation
    result = SimulationResult(
        simulation_type=SimulationType.NOISE,
        status="completed",
        duration=1.0,
        frequency=np.logspace(1, 5, 100),
        total_noise=np.ones(100) * 1e-9,
        noise_by_type={},
        metrics={},
        warnings=[],
        errors=[]
    )
    mock_simulator.run_simulation.return_value = result
    
    control_panel._run_simulation()
    
    assert started.called
    assert completed.called
    assert not error.called
    
    # Run failed simulation
    started.reset_mock()
    completed.reset_mock()
    error.reset_mock()
    
    mock_simulator.run_simulation.side_effect = Exception("Test error")
    control_panel._run_simulation()
    
    assert started.called
    assert not completed.called
    assert error.called 