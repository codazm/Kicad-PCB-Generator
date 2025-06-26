"""Unit tests for component filter dialog."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from kicad_pcb_generator.ui.dialogs.component_filter_dialog import ComponentFilterDialog

@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication([])

@pytest.fixture
def dialog(app):
    """Create a component filter dialog."""
    return ComponentFilterDialog()

def test_dialog_initialization(dialog):
    """Test dialog initialization."""
    assert dialog.windowTitle() == "Filter Components"
    assert dialog.name_edit.text() == ""
    assert dialog.type_edit.text() == ""
    assert dialog.value_edit.text() == ""
    assert dialog.sort_by_combo.currentText() == "Name"
    assert dialog.sort_order_combo.currentText() == "Ascending"
    
    # Check all type filters are checked by default
    for checkbox in dialog.type_filters.values():
        assert checkbox.isChecked()

def test_get_filter_settings(dialog):
    """Test getting filter settings."""
    # Set some values
    dialog.name_edit.setText("R1")
    dialog.type_edit.setText("Resistor")
    dialog.value_edit.setText("1k")
    dialog.sort_by_combo.setCurrentText("Value")
    dialog.sort_order_combo.setCurrentText("Descending")
    
    # Uncheck some type filters
    dialog.type_filters["Capacitor"].setChecked(False)
    dialog.type_filters["Inductor"].setChecked(False)
    
    # Get settings
    settings = dialog.get_filter_settings()
    
    # Check settings
    assert settings['search']['name'] == "R1"
    assert settings['search']['type'] == "Resistor"
    assert settings['search']['value'] == "1k"
    assert settings['sort']['by'] == "Value"
    assert settings['sort']['order'] == "Descending"
    assert settings['filters']['Resistor'] is True
    assert settings['filters']['Capacitor'] is False
    assert settings['filters']['Inductor'] is False

def test_reset_filters(dialog):
    """Test resetting filters."""
    # Set some values
    dialog.name_edit.setText("R1")
    dialog.type_edit.setText("Resistor")
    dialog.value_edit.setText("1k")
    dialog.sort_by_combo.setCurrentText("Value")
    dialog.sort_order_combo.setCurrentText("Descending")
    
    # Uncheck some type filters
    dialog.type_filters["Capacitor"].setChecked(False)
    dialog.type_filters["Inductor"].setChecked(False)
    
    # Reset filters
    dialog.reset_filters()
    
    # Check values are reset
    assert dialog.name_edit.text() == ""
    assert dialog.type_edit.text() == ""
    assert dialog.value_edit.text() == ""
    assert dialog.sort_by_combo.currentText() == "Name"
    assert dialog.sort_order_combo.currentText() == "Ascending"
    
    # Check all type filters are checked
    for checkbox in dialog.type_filters.values():
        assert checkbox.isChecked()

def test_set_filter_settings(dialog):
    """Test setting filter settings."""
    settings = {
        'search': {
            'name': 'R1',
            'type': 'Resistor',
            'value': '1k'
        },
        'filters': {
            'Resistor': True,
            'Capacitor': False,
            'Inductor': True,
            'Transistor': False,
            'OpAmp': True,
            'Diode': True
        },
        'sort': {
            'by': 'Value',
            'order': 'Descending'
        }
    }
    
    # Set settings
    dialog.set_filter_settings(settings)
    
    # Check values are set
    assert dialog.name_edit.text() == "R1"
    assert dialog.type_edit.text() == "Resistor"
    assert dialog.value_edit.text() == "1k"
    assert dialog.sort_by_combo.currentText() == "Value"
    assert dialog.sort_order_combo.currentText() == "Descending"
    assert dialog.type_filters["Resistor"].isChecked()
    assert not dialog.type_filters["Capacitor"].isChecked()
    assert dialog.type_filters["Inductor"].isChecked()
    assert not dialog.type_filters["Transistor"].isChecked()
    assert dialog.type_filters["OpAmp"].isChecked()
    assert dialog.type_filters["Diode"].isChecked()

def test_filter_updated_signal(dialog):
    """Test filter_updated signal."""
    # Set up signal handler
    received_settings = None
    def on_filter_updated(settings):
        nonlocal received_settings
        received_settings = settings
    
    dialog.filter_updated.connect(on_filter_updated)
    
    # Set some values
    dialog.name_edit.setText("R1")
    dialog.type_edit.setText("Resistor")
    dialog.value_edit.setText("1k")
    
    # Apply filters
    dialog.apply_filters()
    
    # Check signal
    assert received_settings is not None
    assert received_settings['search']['name'] == "R1"
    assert received_settings['search']['type'] == "Resistor"
    assert received_settings['search']['value'] == "1k"

def test_cancel_dialog(dialog):
    """Test canceling the dialog."""
    # Set up signal handler
    signal_received = False
    def on_filter_updated(settings):
        nonlocal signal_received
        signal_received = True
    
    dialog.filter_updated.connect(on_filter_updated)
    
    # Set some values
    dialog.name_edit.setText("R1")
    dialog.type_edit.setText("Resistor")
    dialog.value_edit.setText("1k")
    
    # Cancel dialog
    dialog.reject()
    
    # Check signal was not emitted
    assert not signal_received 