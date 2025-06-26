"""Tests for community dialog classes."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import tempfile
import shutil
from pathlib import Path

from kicad_pcb_generator.ui.dialogs.community_dialogs import (
    NewPostDialog,
    ShareProjectDialog,
    ReviewDialog
)

@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication([])

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_new_post_dialog(app):
    """Test the NewPostDialog class."""
    dialog = NewPostDialog()
    
    # Test initial state
    assert dialog.title_input.text() == ""
    assert dialog.content_input.toPlainText() == ""
    assert dialog.tags_input.text() == ""
    
    # Test setting values
    dialog.title_input.setText("Test Post")
    dialog.content_input.setText("Test Content")
    dialog.tags_input.setText("test, audio")
    
    # Test getting data
    data = dialog.get_post_data()
    assert data["title"] == "Test Post"
    assert data["content"] == "Test Content"
    assert data["tags"] == ["test", "audio"]

def test_share_project_dialog(app):
    """Test the ShareProjectDialog class."""
    dialog = ShareProjectDialog()
    
    # Test initial state
    assert dialog.title_input.text() == ""
    assert dialog.description_input.toPlainText() == ""
    assert dialog.tags_input.text() == ""
    assert dialog.files_list.count() == 0
    assert len(dialog.files) == 0
    
    # Test setting values
    dialog.title_input.setText("Test Project")
    dialog.description_input.setText("Test Description")
    dialog.tags_input.setText("test, audio")
    
    # Test getting data
    data = dialog.get_project_data()
    assert data["title"] == "Test Project"
    assert data["description"] == "Test Description"
    assert data["tags"] == ["test", "audio"]
    assert data["files"] == {}

def test_review_dialog(app):
    """Test the ReviewDialog class."""
    dialog = ReviewDialog("Test Project")
    
    # Test initial state
    assert dialog.feedback_input.toPlainText() == ""
    assert dialog.category_input.text() == ""
    assert dialog.severity_input.text() == ""
    
    # Test setting values
    dialog.feedback_input.setText("Test feedback")
    dialog.category_input.setText("layout")
    dialog.severity_input.setText("warning")
    
    # Test getting data
    data = dialog.get_feedback_data()
    assert data["message"] == "Test feedback"
    assert data["category"] == "layout"
    assert data["severity"] == "warning"
    
    # Test validation
    dialog.feedback_input.clear()
    dialog.category_input.clear()
    dialog.severity_input.setText("invalid")
    
    # Should not accept with invalid inputs
    dialog.accept()
    assert dialog.result() == QDialog.Rejected
    
    # Test valid inputs
    dialog.feedback_input.setText("Test feedback")
    dialog.category_input.setText("layout")
    dialog.severity_input.setText("warning")
    
    dialog.accept()
    assert dialog.result() == QDialog.Accepted 
