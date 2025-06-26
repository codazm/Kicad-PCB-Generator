"""Unit tests for simulation window."""

import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from unittest.mock import MagicMock, patch
from pathlib import Path

from kicad_pcb_generator.ui.views.simulation_window import SimulationWindow
from kicad_pcb_generator.audio.simulation.circuit_file_handler import (
    CircuitData, CircuitComponent
)

@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication([])

@pytest.fixture
def mock_simulator():
    """Create a mock circuit simulator."""
    simulator = MagicMock()
    simulator.is_running = False
    return simulator

@pytest.fixture
def sample_circuit():
    """Create a sample circuit."""
    return CircuitData(
        name="Test Circuit",
        description="A test circuit",
        components=[
            CircuitComponent(
                name="R1",
                type="Resistor",
                value="1k",
                parameters={"tolerance": "1%"},
                position={"x": 0, "y": 0},
                connections=["VCC", "GND"]
            ),
            CircuitComponent(
                name="C1",
                type="Capacitor",
                value="100n",
                parameters={"voltage": "16V"},
                position={"x": 100, "y": 0},
                connections=["VCC", "GND"]
            )
        ],
        nets=["VCC", "GND"],
        parameters={"voltage": "5V"}
    )

@pytest.fixture
def window(app, mock_simulator):
    """Create a simulation window."""
    return SimulationWindow(mock_simulator)

@pytest.fixture
def sample_components():
    """Create sample circuit components."""
    return [
        CircuitComponent(
            name="R1",
            type="Resistor",
            value="1k",
            parameters={},
            position={"x": 0, "y": 0},
            connections=[]
        ),
        CircuitComponent(
            name="C1",
            type="Capacitor",
            value="100n",
            parameters={},
            position={"x": 0, "y": 0},
            connections=[]
        ),
        CircuitComponent(
            name="L1",
            type="Inductor",
            value="10m",
            parameters={},
            position={"x": 0, "y": 0},
            connections=[]
        )
    ]

def test_window_initialization(window):
    """Test window initialization."""
    assert window.windowTitle() == "Circuit Simulator"
    assert window.simulator is not None
    assert window.file_handler is not None
    assert window.component_tree is not None
    assert window.search_bar is not None
    assert window.search_bar.placeholderText() == "Search components..."

def test_menu_bar_creation(window):
    """Test menu bar creation."""
    menubar = window.menuBar()
    assert menubar is not None
    
    # Check file menu
    file_menu = menubar.findChild(QMenu, "File")
    assert file_menu is not None
    assert file_menu.actions()[0].text() == "New"
    assert file_menu.actions()[1].text() == "Open"
    assert file_menu.actions()[2].text() == "Save"
    assert file_menu.actions()[3].text() == "Save As"
    assert file_menu.actions()[5].text() == "Exit"
    
    # Check edit menu
    edit_menu = menubar.findChild(QMenu, "Edit")
    assert edit_menu is not None
    assert edit_menu.actions()[0].text() == "Add Component"
    assert edit_menu.actions()[1].text() == "Remove Component"
    assert edit_menu.actions()[3].text() == "Filter Components"
    
    # Check view menu
    view_menu = menubar.findChild(QMenu, "View")
    assert view_menu is not None
    assert view_menu.actions()[0].text() == "Show Components"

def test_filter_components(window, sample_components):
    """Test component filtering."""
    # Add sample components
    for component in sample_components:
        window.file_handler.add_component(component)
    
    # Test search by name
    window.search_bar.setText("R1")
    window.filter_components()
    assert window.component_tree.topLevelItemCount() == 1
    assert window.component_tree.topLevelItem(0).text(0) == "R1"
    
    # Test search by type
    window.search_bar.setText("Capacitor")
    window.filter_components()
    assert window.component_tree.topLevelItemCount() == 1
    assert window.component_tree.topLevelItem(0).text(0) == "C1"
    
    # Test search by value
    window.search_bar.setText("10m")
    window.filter_components()
    assert window.component_tree.topLevelItemCount() == 1
    assert window.component_tree.topLevelItem(0).text(0) == "L1"
    
    # Test clear search
    window.search_bar.setText("")
    window.filter_components()
    assert window.component_tree.topLevelItemCount() == 3

def test_filter_dialog(window, sample_components):
    """Test component filter dialog."""
    # Add sample components
    for component in sample_components:
        window.file_handler.add_component(component)
    
    # Test type filtering
    window.filter_settings['filters']['Capacitor'] = False
    window.filter_settings['filters']['Inductor'] = False
    window.update_component_tree()
    assert window.component_tree.topLevelItemCount() == 1
    assert window.component_tree.topLevelItem(0).text(0) == "R1"
    
    # Test sorting
    window.filter_settings['sort']['by'] = 'Value'
    window.filter_settings['sort']['order'] = 'Descending'
    window.update_component_tree()
    assert window.component_tree.topLevelItemCount() == 3
    assert window.component_tree.topLevelItem(0).text(0) == "L1"  # 10m
    assert window.component_tree.topLevelItem(1).text(0) == "R1"  # 1k
    assert window.component_tree.topLevelItem(2).text(0) == "C1"  # 100n

def test_toggle_components(window):
    """Test toggling components visibility."""
    # Find components dock
    components_dock = None
    for dock in window.findChildren(QDockWidget):
        if dock.windowTitle() == "Components":
            components_dock = dock
            break
    
    assert components_dock is not None
    assert components_dock.isVisible()
    
    # Toggle visibility
    window.toggle_components()
    assert not components_dock.isVisible()
    
    window.toggle_components()
    assert components_dock.isVisible()

def test_unsaved_changes(window):
    """Test handling of unsaved changes."""
    # Mock save_circuit to return True
    window.save_circuit = MagicMock(return_value=True)
    
    # Test with no current file
    window.file_handler.current_file = None
    assert window.confirm_unsaved_changes()
    
    # Test with current file and save
    window.file_handler.current_file = "test.circuit"
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.Save):
        assert window.confirm_unsaved_changes()
        window.save_circuit.assert_called_once()
    
    # Test with current file and discard
    window.save_circuit.reset_mock()
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.Discard):
        assert window.confirm_unsaved_changes()
        window.save_circuit.assert_not_called()
    
    # Test with current file and cancel
    with patch.object(QMessageBox, 'question', return_value=QMessageBox.Cancel):
        assert not window.confirm_unsaved_changes()

def test_close_event(window):
    """Test window close event."""
    # Mock confirm_unsaved_changes
    window.confirm_unsaved_changes = MagicMock(return_value=True)
    
    # Test accept
    event = MagicMock()
    window.closeEvent(event)
    event.accept.assert_called_once()
    event.ignore.assert_not_called()
    
    # Test ignore
    window.confirm_unsaved_changes.return_value = False
    event = MagicMock()
    window.closeEvent(event)
    event.accept.assert_not_called()
    event.ignore.assert_called_once()

def test_new_circuit(app, mock_simulator):
    """Test creating a new circuit."""
    window = SimulationWindow(mock_simulator)
    
    # Mock QInputDialog
    with patch('PyQt5.QtWidgets.QInputDialog.getText') as mock_get_text:
        mock_get_text.return_value = ("New Circuit", True)
        
        # Trigger new circuit action
        window.new_circuit()
        
        # Check circuit was created
        assert window.current_circuit is not None
        assert window.current_circuit.name == "New Circuit"
        assert len(window.current_circuit.components) == 0

def test_open_circuit(app, mock_simulator, sample_circuit, tmp_path):
    """Test opening a circuit."""
    window = SimulationWindow(mock_simulator)
    
    # Save sample circuit
    circuit_file = tmp_path / "test.circuit"
    window.file_handler.save_circuit(sample_circuit, circuit_file)
    
    # Mock QFileDialog
    with patch('PyQt5.QtWidgets.QFileDialog.getOpenFileName') as mock_get_file:
        mock_get_file.return_value = (str(circuit_file), None)
        
        # Trigger open circuit action
        window.open_circuit()
        
        # Check circuit was loaded
        assert window.current_circuit is not None
        assert window.current_circuit.name == sample_circuit.name
        assert len(window.current_circuit.components) == len(sample_circuit.components)

def test_save_circuit(app, mock_simulator, sample_circuit, tmp_path):
    """Test saving a circuit."""
    window = SimulationWindow(mock_simulator)
    window.current_circuit = sample_circuit
    
    # Set current file
    circuit_file = tmp_path / "test.circuit"
    window.file_handler.current_file = circuit_file
    
    # Save circuit
    assert window.save_circuit()
    
    # Check file was saved
    assert circuit_file.exists()
    loaded_circuit = window.file_handler.load_circuit(circuit_file)
    assert loaded_circuit is not None
    assert loaded_circuit.name == sample_circuit.name

def test_save_circuit_as(app, mock_simulator, sample_circuit, tmp_path):
    """Test saving a circuit to a new file."""
    window = SimulationWindow(mock_simulator)
    window.current_circuit = sample_circuit
    
    # Mock QFileDialog
    new_file = tmp_path / "new.circuit"
    with patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName') as mock_get_file:
        mock_get_file.return_value = (str(new_file), None)
        
        # Save circuit
        assert window.save_circuit_as()
        
        # Check file was saved
        assert new_file.exists()
        loaded_circuit = window.file_handler.load_circuit(new_file)
        assert loaded_circuit is not None
        assert loaded_circuit.name == sample_circuit.name

def test_add_component(app, mock_simulator):
    """Test adding a component."""
    window = SimulationWindow(mock_simulator)
    
    # Mock ComponentDialog
    with patch('kicad_pcb_generator.ui.views.simulation_window.ComponentDialog') as mock_dialog:
        mock_dialog_instance = mock_dialog.return_value
        mock_dialog_instance.exec_.return_value = True
        
        # Create sample component
        component = CircuitComponent(
            name="R1",
            type="Resistor",
            value="1k",
            parameters={},
            position={"x": 0, "y": 0},
            connections=[]
        )
        
        # Set up signal handler
        def on_component_updated(comp):
            window.on_component_updated(comp)
        mock_dialog_instance.component_updated.connect(on_component_updated)
        
        # Trigger add component action
        window.add_component()
        
        # Check component was added
        assert len(window.current_circuit.components) == 1
        assert window.current_circuit.components[0].name == "R1"

def test_remove_component(app, mock_simulator, sample_circuit):
    """Test removing a component."""
    window = SimulationWindow(mock_simulator)
    window.current_circuit = sample_circuit
    window.update_component_tree()
    
    # Select component in tree
    item = window.component_tree.topLevelItem(0)
    window.component_tree.setCurrentItem(item)
    
    # Mock QMessageBox
    with patch('PyQt5.QtWidgets.QMessageBox.question') as mock_question:
        mock_question.return_value = QMessageBox.Yes
        
        # Trigger remove component action
        window.remove_component()
        
        # Check component was removed
        assert len(window.current_circuit.components) == 1
        assert window.current_circuit.components[0].name == "C1"

def test_update_component_tree(app, mock_simulator, sample_circuit):
    """Test updating component tree."""
    window = SimulationWindow(mock_simulator)
    window.current_circuit = sample_circuit
    
    # Update tree
    window.update_component_tree()
    
    # Check tree items
    assert window.component_tree.topLevelItemCount() == 2
    assert window.component_tree.topLevelItem(0).text(0) == "R1"
    assert window.component_tree.topLevelItem(1).text(0) == "C1"

def test_simulation_signals(app, mock_simulator):
    """Test simulation signals."""
    window = SimulationWindow(mock_simulator)
    
    # Test simulation started
    window.on_simulation_started()
    assert window.windowTitle() == "Circuit Simulator - Running..."
    
    # Test simulation completed
    window.on_simulation_completed()
    assert window.windowTitle() == "Circuit Simulator"
    
    # Test simulation error
    with patch('PyQt5.QtWidgets.QMessageBox.critical') as mock_critical:
        window.on_simulation_error("Test error")
        mock_critical.assert_called_once()

def test_show_about(app, mock_simulator):
    """Test showing about dialog."""
    window = SimulationWindow(mock_simulator)
    
    with patch('PyQt5.QtWidgets.QMessageBox.about') as mock_about:
        window.show_about()
        mock_about.assert_called_once() 
