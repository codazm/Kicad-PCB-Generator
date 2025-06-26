"""Unit tests for format preview widget."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint
from kicad_pcb_generator.ui.widgets.format_preview import FormatPreviewWidget
from kicad_pcb_generator.audio.pcb.formats import (
    KOSMO_FORMATS,
    EURORACK_FORMATS,
    GUITAR_PEDAL_FORMATS,
    DESKTOP_FORMATS
)

@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication([])

@pytest.fixture
def preview_widget(app):
    """Create format preview widget instance."""
    return FormatPreviewWidget()

def test_widget_initialization(preview_widget):
    """Test widget initialization."""
    assert preview_widget.current_format is None
    assert preview_widget.current_type is None
    assert preview_widget.show_zones is True
    
    # Check UI elements
    assert preview_widget.format_type_combo.count() == 4
    assert preview_widget.show_zones_btn.isChecked()

def test_format_type_selection(preview_widget):
    """Test format type selection."""
    # Test Kosmo format type
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    assert preview_widget.current_type == "Kosmo"
    assert preview_widget.format_combo.count() == len(KOSMO_FORMATS)
    
    # Test Eurorack format type
    preview_widget.format_type_combo.setCurrentText("Eurorack")
    assert preview_widget.current_type == "Eurorack"
    assert preview_widget.format_combo.count() == len(EURORACK_FORMATS)
    
    # Test Guitar Pedal format type
    preview_widget.format_type_combo.setCurrentText("Guitar Pedal")
    assert preview_widget.current_type == "Guitar Pedal"
    assert preview_widget.format_combo.count() == len(GUITAR_PEDAL_FORMATS)
    
    # Test Desktop format type
    preview_widget.format_type_combo.setCurrentText("Desktop")
    assert preview_widget.current_type == "Desktop"
    assert preview_widget.format_combo.count() == len(DESKTOP_FORMATS)

def test_format_selection(preview_widget):
    """Test format selection."""
    # Select Kosmo standard format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    assert preview_widget.current_format == KOSMO_FORMATS["standard"]
    
    # Select Eurorack 4HP format
    preview_widget.format_type_combo.setCurrentText("Eurorack")
    preview_widget.format_combo.setCurrentText("4hp")
    assert preview_widget.current_format == EURORACK_FORMATS["4hp"]

def test_zone_toggle(preview_widget):
    """Test zone visibility toggle."""
    # Select a format with zones
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Toggle zones off
    preview_widget.show_zones_btn.click()
    assert not preview_widget.show_zones
    
    # Toggle zones on
    preview_widget.show_zones_btn.click()
    assert preview_widget.show_zones

def test_preview_scene(preview_widget):
    """Test preview scene creation and updates."""
    # Select a format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Check scene items
    items = preview_widget.scene.items()
    assert len(items) > 0
    
    # Check for board outline
    board_items = [item for item in items if isinstance(item, QGraphicsRectItem)]
    assert len(board_items) > 0
    
    # Check for mounting holes
    hole_items = [item for item in items if isinstance(item, QGraphicsEllipseItem)]
    assert len(hole_items) == 4  # Should have 4 mounting holes
    
    # Check for zone rectangles when zones are visible
    zone_items = [item for item in items if isinstance(item, QGraphicsRectItem) and item != board_items[0]]
    assert len(zone_items) > 0

def test_preview_scaling(preview_widget):
    """Test preview scaling and fitting."""
    # Select a format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Resize widget
    preview_widget.resize(800, 600)
    
    # Check that view is properly scaled
    view_rect = preview_widget.view.viewport().rect()
    scene_rect = preview_widget.scene.sceneRect()
    assert view_rect.width() > 0
    assert view_rect.height() > 0
    assert scene_rect.width() > 0
    assert scene_rect.height() > 0

def test_format_information_display(preview_widget):
    """Test format information display."""
    # Select a format
    preview_widget.format_type_combo.setCurrentText("Kosmo")
    preview_widget.format_combo.setCurrentText("standard")
    
    # Check for information text
    items = preview_widget.scene.items()
    text_items = [item for item in items if isinstance(item, QGraphicsTextItem)]
    assert len(text_items) > 0
    
    # Check information content
    info_text = text_items[0].toPlainText()
    assert "standard" in info_text.lower()
    assert "mm" in info_text
    assert "max component height" in info_text.lower() 