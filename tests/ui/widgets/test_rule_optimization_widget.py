"""Tests for rule optimization widget."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
import json
import csv
from unittest.mock import MagicMock, patch

from PyQt5.QtWidgets import QApplication, QGroupBox, QMessageBox
from PyQt5.QtCore import Qt

from kicad_pcb_generator.core.validation import (
    ValidationManager,
    ValidationRule,
    ValidationCategory,
    ValidationSeverity,
    OptimizationStrategy,
    OptimizationResult,
    RuleEffectiveness,
    RuleEffectivenessStatus
)
from kicad_pcb_generator.core.community import CommunityMetricsManager
from kicad_pcb_generator.ui.widgets.rule_optimization_widget import RuleOptimizationWidget

@pytest.fixture
def app():
    """Create a QApplication instance."""
    return QApplication([])

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def metrics_manager(temp_dir):
    """Create a metrics manager for testing."""
    return CommunityMetricsManager(data_dir=temp_dir)

@pytest.fixture
def validation_manager(temp_dir, metrics_manager):
    """Create a validation manager for testing."""
    return ValidationManager(
        data_dir=temp_dir,
        metrics_manager=metrics_manager
    )

@pytest.fixture
def sample_rule():
    """Create a sample validation rule."""
    return ValidationRule(
        rule_id="test_rule",
        name="Test Rule",
        description="A test rule",
        category=ValidationCategory.DESIGN,
        severity=ValidationSeverity.WARNING,
        parameters={
            "threshold": 0.5,
            "min_value": 0.0,
            "max_value": 1.0,
            "tolerance": 0.1
        }
    )

@pytest.fixture
def sample_optimization():
    """Create a sample optimization result."""
    return OptimizationResult(
        rule_id="test_rule",
        parameter_name="threshold",
        original_value=0.5,
        optimized_value=0.6,
        improvement=0.1,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES,
        metrics={},
        created_at=datetime.now()
    )

@pytest.fixture
def widget(validation_manager, app):
    """Create a rule optimization widget for testing."""
    return RuleOptimizationWidget(validation_manager)

def test_initial_state(widget):
    """Test initial state of the widget."""
    assert widget._current_rule is None
    assert len(widget._current_optimizations) == 0
    assert widget._rule_combo.count() == 0
    assert widget._strategy_combo.count() == len(OptimizationStrategy)
    assert not widget._optimize_button.isEnabled()
    assert not widget._apply_button.isEnabled()
    assert not widget._progress_bar.isVisible()

def test_rule_list_update(widget, validation_manager, sample_rule):
    """Test updating the rule list."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    assert widget._rule_combo.count() == 1
    assert widget._rule_combo.itemText(0) == sample_rule.name
    assert widget._rule_combo.itemData(0) == sample_rule.rule_id

def test_rule_selection(widget, validation_manager, sample_rule):
    """Test selecting a rule."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    assert widget._current_rule == sample_rule
    assert widget._optimize_button.isEnabled()

def test_parameter_display(widget, validation_manager, sample_rule):
    """Test displaying rule parameters."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    params_group = widget.findChild(QGroupBox, "Current Parameters")
    assert params_group is not None
    
    params_layout = params_group.layout()
    assert params_layout is not None
    
    # Check that all parameters are displayed
    for name, value in sample_rule.parameters.items():
        label = widget._param_labels.get(name)
        assert label is not None
        assert label.text() == str(value)

def test_optimization_history(widget, validation_manager, sample_rule, sample_optimization):
    """Test displaying optimization history."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization history
    with patch.object(
        validation_manager,
        'get_optimization_history',
        return_value=[sample_optimization]
    ):
        widget._update_optimization_history()
        
        assert widget._history_table.rowCount() == 1
        assert widget._history_table.item(0, 0).text() == sample_optimization.parameter_name
        assert widget._history_table.item(0, 1).text() == str(sample_optimization.original_value)
        assert widget._history_table.item(0, 2).text() == str(sample_optimization.optimized_value)
        assert widget._history_table.item(0, 3).text() == f"{sample_optimization.improvement:.1%}"
        assert widget._history_table.item(0, 4).text() == sample_optimization.strategy.name

def test_optimization_summary(widget, validation_manager, sample_rule):
    """Test displaying optimization summary."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization summary
    summary = {
        "total_optimizations": 5,
        "average_improvement": 0.15,
        "best_improvement": 0.25,
        "optimized_parameters": ["threshold", "tolerance"]
    }
    
    with patch.object(
        validation_manager,
        'get_optimization_summary',
        return_value=summary
    ):
        widget._update_optimization_summary()
        
        assert widget._summary_labels["total"].text() == "5"
        assert widget._summary_labels["average"].text() == "15.0%"
        assert widget._summary_labels["best"].text() == "25.0%"
        assert widget._summary_labels["parameters"].text() == "threshold, tolerance"

def test_optimize_button(widget, validation_manager, sample_rule):
    """Test optimize button functionality."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization results
    results = [
        OptimizationResult(
            rule_id=sample_rule.rule_id,
            parameter_name="threshold",
            original_value=0.5,
            optimized_value=0.6,
            improvement=0.1,
            strategy=OptimizationStrategy.MINIMIZE_FAILURES,
            metrics={},
            created_at=datetime.now()
        )
    ]
    
    with patch.object(
        validation_manager,
        'optimize_rule_parameters',
        return_value=results
    ):
        widget._on_optimize_clicked()
        
        assert not widget._progress_bar.isVisible()
        assert widget._optimize_button.isEnabled()
        assert widget._history_table.rowCount() == 1

def test_apply_optimization(widget, validation_manager, sample_rule, sample_optimization):
    """Test applying an optimization."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization history
    with patch.object(
        validation_manager,
        'get_optimization_history',
        return_value=[sample_optimization]
    ):
        widget._update_optimization_history()
        
        # Select the optimization
        widget._history_table.selectRow(0)
        assert widget._apply_button.isEnabled()
        
        # Mock applying optimization
        with patch.object(
            validation_manager,
            'apply_optimization',
            return_value=True
        ):
            widget._on_apply_clicked()
            assert sample_rule.parameters[sample_optimization.parameter_name] == sample_optimization.optimized_value

def test_optimization_error_handling(widget, validation_manager, sample_rule):
    """Test error handling during optimization."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization error
    with patch.object(
        validation_manager,
        'optimize_rule_parameters',
        side_effect=Exception("Test error")
    ):
        widget._on_optimize_clicked()
        
        assert not widget._progress_bar.isVisible()
        assert widget._optimize_button.isEnabled()

def test_apply_optimization_error_handling(widget, validation_manager, sample_rule, sample_optimization):
    """Test error handling when applying optimization."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Mock optimization history
    with patch.object(
        validation_manager,
        'get_optimization_history',
        return_value=[sample_optimization]
    ):
        widget._update_optimization_history()
        
        # Select the optimization
        widget._history_table.selectRow(0)
        
        # Mock applying optimization error
        with patch.object(
            validation_manager,
            'apply_optimization',
            side_effect=Exception("Test error")
        ):
            widget._on_apply_clicked()
            assert sample_rule.parameters[sample_optimization.parameter_name] == sample_optimization.original_value

def test_batch_optimization_initial_state(widget):
    """Test initial state of batch optimization controls."""
    assert widget._rule_list.count() == 0
    assert not widget._batch_optimize_button.isEnabled()

def test_batch_optimization_rule_list(widget, validation_manager, sample_rule):
    """Test batch optimization rule list."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    assert widget._rule_list.count() == 1
    assert widget._rule_list.item(0).text() == sample_rule.name
    assert widget._rule_list.item(0).data(Qt.UserRole) == sample_rule.rule_id

def test_select_all_rules(widget, validation_manager, sample_rule):
    """Test selecting all rules."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._on_select_all_clicked()
    assert widget._rule_list.item(0).isSelected()

def test_deselect_all_rules(widget, validation_manager, sample_rule):
    """Test deselecting all rules."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_list.item(0).setSelected(True)
    widget._on_deselect_all_clicked()
    assert not widget._rule_list.item(0).isSelected()

def test_batch_optimize_no_selection(widget, validation_manager, sample_rule):
    """Test batch optimization with no rules selected."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    
    with patch.object(QMessageBox, 'warning') as mock_warning:
        widget._on_batch_optimize_clicked()
        mock_warning.assert_called_once()

def test_batch_optimize_single_rule(widget, validation_manager, sample_rule):
    """Test batch optimization for a single rule."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_list.item(0).setSelected(True)
    
    results = [
        OptimizationResult(
            rule_id=sample_rule.rule_id,
            parameter_name="threshold",
            original_value=0.5,
            optimized_value=0.6,
            improvement=0.1,
            strategy=OptimizationStrategy.MINIMIZE_FAILURES,
            metrics={},
            created_at=datetime.now()
        )
    ]
    
    with patch.object(
        validation_manager,
        'optimize_rule_parameters',
        return_value=results
    ):
        widget._on_batch_optimize_clicked()
        assert not widget._progress_bar.isVisible()
        assert widget._batch_optimize_button.isEnabled()

def test_batch_optimize_multiple_rules(widget, validation_manager):
    """Test batch optimization for multiple rules."""
    # Add multiple rules
    rules = []
    for i in range(3):
        rule = ValidationRule(
            rule_id=f"test_rule_{i}",
            name=f"Test Rule {i}",
            description=f"A test rule {i}",
            category=ValidationCategory.DESIGN,
            severity=ValidationSeverity.WARNING,
            parameters={
                "threshold": 0.5,
                "min_value": 0.0,
                "max_value": 1.0,
                "tolerance": 0.1
            }
        )
        validation_manager.add_rule(rule)
        rules.append(rule)
    
    widget.refresh()
    
    # Select all rules
    for i in range(widget._rule_list.count()):
        widget._rule_list.item(i).setSelected(True)
    
    # Mock optimization results
    results = [
        OptimizationResult(
            rule_id=rule.rule_id,
            parameter_name="threshold",
            original_value=0.5,
            optimized_value=0.6,
            improvement=0.1,
            strategy=OptimizationStrategy.MINIMIZE_FAILURES,
            metrics={},
            created_at=datetime.now()
        )
        for rule in rules
    ]
    
    with patch.object(
        validation_manager,
        'optimize_rule_parameters',
        return_value=results
    ):
        widget._on_batch_optimize_clicked()
        assert not widget._progress_bar.isVisible()
        assert widget._batch_optimize_button.isEnabled()

def test_export_csv(widget, validation_manager, sample_rule, sample_optimization, tmp_path):
    """Test exporting optimization history to CSV."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Add optimization to history
    widget._current_optimizations = [sample_optimization]
    
    # Export to CSV
    file_path = tmp_path / "optimizations.csv"
    widget._export_csv(str(file_path))
    
    # Verify CSV contents
    with open(file_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["Rule ID"] == sample_optimization.rule_id
        assert rows[0]["Parameter"] == sample_optimization.parameter_name
        assert float(rows[0]["Original Value"]) == sample_optimization.original_value
        assert float(rows[0]["Optimized Value"]) == sample_optimization.optimized_value
        assert float(rows[0]["Improvement"]) == sample_optimization.improvement
        assert rows[0]["Strategy"] == sample_optimization.strategy.name

def test_export_json(widget, validation_manager, sample_rule, sample_optimization, tmp_path):
    """Test exporting optimization history to JSON."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Add optimization to history
    widget._current_optimizations = [sample_optimization]
    
    # Export to JSON
    file_path = tmp_path / "optimizations.json"
    widget._export_json(str(file_path))
    
    # Verify JSON contents
    with open(file_path, 'r') as f:
        data = json.load(f)
        assert data["rule_id"] == sample_rule.rule_id
        assert data["rule_name"] == sample_rule.name
        assert len(data["optimizations"]) == 1
        
        opt_data = data["optimizations"][0]
        assert opt_data["parameter_name"] == sample_optimization.parameter_name
        assert opt_data["original_value"] == sample_optimization.original_value
        assert opt_data["optimized_value"] == sample_optimization.optimized_value
        assert opt_data["improvement"] == sample_optimization.improvement
        assert opt_data["strategy"] == sample_optimization.strategy.name

def test_import_csv(widget, validation_manager, sample_rule, tmp_path):
    """Test importing optimization history from CSV."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Create test CSV
    file_path = tmp_path / "optimizations.csv"
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rule ID",
            "Parameter",
            "Original Value",
            "Optimized Value",
            "Improvement",
            "Strategy",
            "Date"
        ])
        writer.writerow([
            sample_rule.rule_id,
            "threshold",
            0.5,
            0.6,
            0.1,
            "MINIMIZE_FAILURES",
            datetime.now().isoformat()
        ])
    
    # Import CSV
    widget._import_csv(str(file_path))
    assert len(widget._current_optimizations) == 1
    
    opt = widget._current_optimizations[0]
    assert opt.rule_id == sample_rule.rule_id
    assert opt.parameter_name == "threshold"
    assert opt.original_value == 0.5
    assert opt.optimized_value == 0.6
    assert opt.improvement == 0.1
    assert opt.strategy == OptimizationStrategy.MINIMIZE_FAILURES

def test_import_json(widget, validation_manager, sample_rule, tmp_path):
    """Test importing optimization history from JSON."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Create test JSON
    file_path = tmp_path / "optimizations.json"
    data = {
        "rule_id": sample_rule.rule_id,
        "rule_name": sample_rule.name,
        "optimizations": [
            {
                "parameter_name": "threshold",
                "original_value": 0.5,
                "optimized_value": 0.6,
                "improvement": 0.1,
                "strategy": "MINIMIZE_FAILURES",
                "created_at": datetime.now().isoformat(),
                "metrics": {}
            }
        ]
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    # Import JSON
    widget._import_json(str(file_path))
    assert len(widget._current_optimizations) == 1
    
    opt = widget._current_optimizations[0]
    assert opt.rule_id == sample_rule.rule_id
    assert opt.parameter_name == "threshold"
    assert opt.original_value == 0.5
    assert opt.optimized_value == 0.6
    assert opt.improvement == 0.1
    assert opt.strategy == OptimizationStrategy.MINIMIZE_FAILURES

def test_import_wrong_rule(widget, validation_manager, sample_rule, tmp_path):
    """Test importing optimization history for wrong rule."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Create test JSON with wrong rule ID
    file_path = tmp_path / "optimizations.json"
    data = {
        "rule_id": "wrong_rule",
        "rule_name": "Wrong Rule",
        "optimizations": []
    }
    
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    # Import JSON
    with pytest.raises(ValueError):
        widget._import_json(str(file_path))

def test_export_import_roundtrip(widget, validation_manager, sample_rule, sample_optimization, tmp_path):
    """Test export and import roundtrip."""
    validation_manager.add_rule(sample_rule)
    widget.refresh()
    widget._rule_combo.setCurrentIndex(0)
    
    # Add optimization to history
    widget._current_optimizations = [sample_optimization]
    
    # Export to JSON
    json_path = tmp_path / "optimizations.json"
    widget._export_json(str(json_path))
    
    # Clear current optimizations
    widget._current_optimizations = []
    
    # Import JSON
    widget._import_json(str(json_path))
    
    # Verify optimizations match
    assert len(widget._current_optimizations) == 1
    imported = widget._current_optimizations[0]
    assert imported.rule_id == sample_optimization.rule_id
    assert imported.parameter_name == sample_optimization.parameter_name
    assert imported.original_value == sample_optimization.original_value
    assert imported.optimized_value == sample_optimization.optimized_value
    assert imported.improvement == sample_optimization.improvement
    assert imported.strategy == sample_optimization.strategy.name 