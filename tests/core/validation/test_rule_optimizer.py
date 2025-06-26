"""Tests for rule parameter optimization."""

import pytest
from datetime import datetime
import numpy as np

from kicad_pcb_generator.core.validation.rule_optimizer import (
    RuleParameterOptimizer,
    OptimizationStrategy,
    ParameterRange,
    OptimizationResult
)
from kicad_pcb_generator.core.validation.validation_rule import ValidationRule
from kicad_pcb_generator.core.validation.rule_effectiveness import RuleEffectiveness
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationCategory,
    ValidationSeverity
)

@pytest.fixture
def optimizer():
    """Create a rule parameter optimizer."""
    return RuleParameterOptimizer()

@pytest.fixture
def sample_rule():
    """Create a sample validation rule."""
    return ValidationRule(
        rule_id="test_rule",
        name="Test Rule",
        description="A test rule",
        category=ValidationCategory.DESIGN,
        parameters={
            "threshold": 1000,
            "min_value": 0,
            "max_value": 2000,
            "tolerance": 100
        },
        dependencies=[],
        severity=ValidationSeverity.ERROR
    )

@pytest.fixture
def sample_effectiveness():
    """Create sample effectiveness data."""
    return RuleEffectiveness(
        rule_id="test_rule",
        rule_name="Test Rule",
        category=ValidationCategory.DESIGN,
        total_validations=100,
        passed_validations=60,
        failed_validations=40,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="needs_improvement",
        feedback_count=20,
        positive_feedback=12,
        negative_feedback=8
    )

def test_initial_state(optimizer):
    """Test the initial state of the optimizer."""
    assert optimizer._optimization_history == {}

def test_get_parameter_range(optimizer):
    """Test getting parameter ranges."""
    # Test threshold parameter
    threshold_range = optimizer._get_parameter_range("threshold", 1000)
    assert threshold_range is not None
    assert threshold_range.min_value == 500  # 0.5 * 1000
    assert threshold_range.max_value == 1500  # 1.5 * 1000
    assert threshold_range.step == 100  # 0.1 * 1000
    assert threshold_range.current_value == 1000
    
    # Test min parameter
    min_range = optimizer._get_parameter_range("min_value", 100)
    assert min_range is not None
    assert min_range.min_value == 0
    assert min_range.max_value == 200  # 2 * 100
    assert min_range.step == 10  # 0.1 * 100
    assert min_range.current_value == 100
    
    # Test max parameter
    max_range = optimizer._get_parameter_range("max_value", 2000)
    assert max_range is not None
    assert max_range.min_value == 1000  # 0.5 * 2000
    assert max_range.max_value == 4000  # 2 * 2000
    assert max_range.step == 200  # 0.1 * 2000
    assert max_range.current_value == 2000
    
    # Test tolerance parameter
    tolerance_range = optimizer._get_parameter_range("tolerance", 100)
    assert tolerance_range is not None
    assert tolerance_range.min_value == 0
    assert tolerance_range.max_value == 200  # 2 * 100
    assert tolerance_range.step == 5  # 0.05 * 100
    assert tolerance_range.current_value == 100
    
    # Test unknown parameter
    unknown_range = optimizer._get_parameter_range("unknown", 100)
    assert unknown_range is None

def test_optimize_parameters(optimizer, sample_rule, sample_effectiveness):
    """Test optimizing rule parameters."""
    results = optimizer.optimize_parameters(
        rule=sample_rule,
        effectiveness=sample_effectiveness,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES
    )
    
    assert len(results) > 0
    assert all(isinstance(result, OptimizationResult) for result in results)
    assert all(result.rule_id == sample_rule.rule_id for result in results)
    assert all(result.improvement > 0 for result in results)

def test_optimize_parameters_no_parameters(optimizer, sample_effectiveness):
    """Test optimizing a rule with no parameters."""
    rule = ValidationRule(
        rule_id="no_params",
        name="No Parameters",
        description="A rule with no parameters",
        category=ValidationCategory.DESIGN,
        parameters={},
        dependencies=[],
        severity=ValidationSeverity.ERROR
    )
    
    results = optimizer.optimize_parameters(
        rule=rule,
        effectiveness=sample_effectiveness
    )
    
    assert len(results) == 0

def test_optimize_parameters_different_strategies(
    optimizer,
    sample_rule,
    sample_effectiveness
):
    """Test optimizing parameters with different strategies."""
    strategies = [
        OptimizationStrategy.MINIMIZE_FAILURES,
        OptimizationStrategy.MAXIMIZE_PASS_RATE,
        OptimizationStrategy.BALANCE_SEVERITY,
        OptimizationStrategy.OPTIMIZE_FEEDBACK
    ]
    
    for strategy in strategies:
        results = optimizer.optimize_parameters(
            rule=sample_rule,
            effectiveness=sample_effectiveness,
            strategy=strategy
        )
        
        assert len(results) > 0
        assert all(result.strategy == strategy for result in results)

def test_evaluate_parameter(optimizer, sample_rule, sample_effectiveness):
    """Test evaluating a parameter value."""
    # Test minimize failures strategy
    score = optimizer._evaluate_parameter(
        rule=sample_rule,
        param_name="threshold",
        param_value=1000,
        effectiveness=sample_effectiveness,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES
    )
    assert 0 <= score <= 1
    
    # Test maximize pass rate strategy
    score = optimizer._evaluate_parameter(
        rule=sample_rule,
        param_name="threshold",
        param_value=1000,
        effectiveness=sample_effectiveness,
        strategy=OptimizationStrategy.MAXIMIZE_PASS_RATE
    )
    assert 0 <= score <= 1
    
    # Test balance severity strategy
    score = optimizer._evaluate_parameter(
        rule=sample_rule,
        param_name="threshold",
        param_value=1000,
        effectiveness=sample_effectiveness,
        strategy=OptimizationStrategy.BALANCE_SEVERITY
    )
    assert 0 <= score <= 1
    
    # Test optimize feedback strategy
    score = optimizer._evaluate_parameter(
        rule=sample_rule,
        param_name="threshold",
        param_value=1000,
        effectiveness=sample_effectiveness,
        strategy=OptimizationStrategy.OPTIMIZE_FEEDBACK
    )
    assert 0 <= score <= 1

def test_calculate_metrics(optimizer, sample_rule, sample_effectiveness):
    """Test calculating metrics for a parameter value."""
    metrics = optimizer._calculate_metrics(
        rule=sample_rule,
        param_name="threshold",
        param_value=1000,
        effectiveness=sample_effectiveness
    )
    
    assert "failure_rate" in metrics
    assert "pass_rate" in metrics
    assert "average_severity" in metrics
    assert "feedback_score" in metrics
    
    assert 0 <= metrics["failure_rate"] <= 1
    assert 0 <= metrics["pass_rate"] <= 1
    assert 0 <= metrics["average_severity"] <= ValidationSeverity.ERROR.value
    assert 0 <= metrics["feedback_score"] <= 1

def test_optimization_history(optimizer, sample_rule, sample_effectiveness):
    """Test recording and retrieving optimization history."""
    # Optimize parameters
    results = optimizer.optimize_parameters(
        rule=sample_rule,
        effectiveness=sample_effectiveness
    )
    
    # Check history
    history = optimizer.get_optimization_history(sample_rule.rule_id)
    assert len(history) == len(results)
    assert all(isinstance(result, OptimizationResult) for result in history)
    
    # Check best optimization
    best = optimizer.get_best_optimization(sample_rule.rule_id)
    assert best is not None
    assert best.improvement == max(result.improvement for result in results)
    
    # Check optimization summary
    summary = optimizer.get_optimization_summary(sample_rule.rule_id)
    assert summary["total_optimizations"] == len(results)
    assert summary["average_improvement"] > 0
    assert summary["best_improvement"] > 0
    assert len(summary["optimized_parameters"]) > 0

def test_optimization_history_empty(optimizer):
    """Test optimization history for a rule with no optimizations."""
    # Check history
    history = optimizer.get_optimization_history("unknown_rule")
    assert len(history) == 0
    
    # Check best optimization
    best = optimizer.get_best_optimization("unknown_rule")
    assert best is None
    
    # Check optimization summary
    summary = optimizer.get_optimization_summary("unknown_rule")
    assert summary["total_optimizations"] == 0
    assert summary["average_improvement"] == 0.0
    assert summary["best_improvement"] == 0.0
    assert len(summary["optimized_parameters"]) == 0 