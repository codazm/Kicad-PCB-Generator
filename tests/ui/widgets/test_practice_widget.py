"""Tests for the practice widget."""

import json
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ....core.learning.practice_manager import PracticeManager
from ....core.learning.learning_data import PracticeExercise
from ....core.validation.base_validator import ValidationResult, ValidationSeverity
from ....ui.widgets.practice_widget import PracticeWidget

@pytest.fixture
def app():
    """Create QApplication instance."""
    return QApplication([])

@pytest.fixture
def practice_manager(tmp_path):
    """Create practice manager with test data."""
    manager = PracticeManager(storage_path=str(tmp_path))
    
    # Add test exercise
    exercise = PracticeExercise(
        id="test_exercise",
        title="Test Exercise",
        description="Test exercise description",
        category="Test",
        difficulty="Beginner",
        instructions="Test instructions",
        solution_template={
            "components": [
                {
                    "type": "resistor",
                    "value": "10k",
                    "position": [0, 0]
                }
            ],
            "nets": [
                {
                    "name": "VCC",
                    "nodes": [[0, 0], [0, 1]]
                }
            ]
        }
    )
    manager.exercises[exercise.id] = exercise
    
    return manager

@pytest.fixture
def practice_widget(app, practice_manager):
    """Create practice widget."""
    widget = PracticeWidget(practice_manager, "test_user")
    widget.show()
    return widget

def test_initial_state(practice_widget):
    """Test initial widget state."""
    assert practice_widget.current_exercise is None
    assert practice_widget.solution_text.toPlainText() == ""
    assert practice_widget.feedback_text.toPlainText() == ""
    assert practice_widget.feedback_tree.topLevelItemCount() == 0
    assert practice_widget.progress_bar.value() == 0

def test_load_exercises(practice_widget):
    """Test loading exercises."""
    assert practice_widget.category_combo.count() > 0
    assert "Test" in [practice_widget.category_combo.itemText(i) for i in range(practice_widget.category_combo.count())]

def test_select_exercise(practice_widget):
    """Test selecting an exercise."""
    # Select category
    practice_widget.category_combo.setCurrentText("Test")
    
    # Select exercise
    practice_widget.exercise_combo.setCurrentText("Test Exercise")
    
    assert practice_widget.current_exercise is not None
    assert practice_widget.current_exercise.id == "test_exercise"
    assert practice_widget.title_label.text() == "Test Exercise"
    assert practice_widget.description_label.text() == "Test exercise description"
    assert practice_widget.instructions_text.toPlainText() == "Test instructions"
    
    # Check solution template
    template = json.loads(practice_widget.solution_text.toPlainText())
    assert "components" in template
    assert "nets" in template

def test_validate_solution(practice_widget, monkeypatch):
    """Test solution validation."""
    # Select exercise
    practice_widget.category_combo.setCurrentText("Test")
    practice_widget.exercise_combo.setCurrentText("Test Exercise")
    
    # Mock validation results
    def mock_validate(*args, **kwargs):
        return type("Feedback", (), {
            "score": 0.8,
            "feedback": "Good solution!",
            "validation_results": [
                ValidationResult(
                    message="Test error",
                    severity=ValidationSeverity.ERROR,
                    details="Error details",
                    suggestion="Try this instead"
                ),
                ValidationResult(
                    message="Test warning",
                    severity=ValidationSeverity.WARNING
                )
            ]
        })
    
    monkeypatch.setattr(practice_widget.practice_manager, "validate_solution", mock_validate)
    
    # Enter solution
    practice_widget.solution_text.setText(json.dumps({
        "components": [
            {
                "type": "resistor",
                "value": "10k",
                "position": [0, 0]
            }
        ],
        "nets": [
            {
                "name": "VCC",
                "nodes": [[0, 0], [0, 1]]
            }
        ]
    }))
    
    # Validate solution
    practice_widget._validate_solution()
    
    # Check feedback
    assert practice_widget.feedback_text.toPlainText() == "Good solution!"
    assert practice_widget.progress_bar.value() == 80
    
    # Check feedback tree
    assert practice_widget.feedback_tree.topLevelItemCount() > 0
    
    # Check error item
    error_item = practice_widget.feedback_tree.topLevelItem(0)
    assert error_item.text(0) == ValidationSeverity.ERROR.value
    assert error_item.childCount() > 0
    
    error_result = error_item.child(0)
    assert error_result.text(0) == "Test error"
    assert error_result.text(1) == ValidationSeverity.ERROR.value
    
    # Check details and suggestion
    assert error_result.childCount() == 2
    assert error_result.child(0).text(0) == "Details"
    assert error_result.child(0).text(2) == "Error details"
    assert error_result.child(1).text(0) == "Suggestion"
    assert error_result.child(1).text(2) == "Try this instead"

def test_invalid_solution(practice_widget):
    """Test invalid solution handling."""
    # Select exercise
    practice_widget.category_combo.setCurrentText("Test")
    practice_widget.exercise_combo.setCurrentText("Test Exercise")
    
    # Enter invalid solution
    practice_widget.solution_text.setText("invalid json")
    
    # Try to validate
    with pytest.raises(ValueError, match="Invalid JSON format"):
        practice_widget._validate_solution()

def test_reset_solution(practice_widget):
    """Test resetting solution."""
    # Select exercise
    practice_widget.category_combo.setCurrentText("Test")
    practice_widget.exercise_combo.setCurrentText("Test Exercise")
    
    # Enter solution
    practice_widget.solution_text.setText("test solution")
    
    # Add feedback
    practice_widget.feedback_text.setText("test feedback")
    practice_widget.feedback_tree.addTopLevelItem(QTreeWidgetItem(["test"]))
    
    # Reset
    practice_widget._reset_solution()
    
    # Check reset
    template = json.loads(practice_widget.solution_text.toPlainText())
    assert "components" in template
    assert "nets" in template
    assert practice_widget.feedback_text.toPlainText() == ""
    assert practice_widget.feedback_tree.topLevelItemCount() == 0 