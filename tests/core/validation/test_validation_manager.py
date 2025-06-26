"""
Tests for validation manager.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Dict, Any
from datetime import datetime

from kicad_pcb_generator.core.validation import (
    ValidationManager,
    ValidationRule,
    ValidationCategory,
    ValidationSeverity,
    RuleEffectiveness,
    RuleEffectivenessStatus,
    OptimizationStrategy,
    OptimizationResult
)
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationResult
)
from kicad_pcb_generator.core.validation.rule_effectiveness import (
    RuleEffectiveness,
    RuleEffectivenessStatus
)
from kicad_pcb_generator.core.validation.rule_improvements import (
    RuleImprovement,
    ImprovementPriority
)
from kicad_pcb_generator.core.community import CommunityMetricsManager

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def metrics_manager(temp_dir):
    """Create a CommunityMetricsManager instance."""
    return CommunityMetricsManager(data_dir=temp_dir)

@pytest.fixture
def validation_manager(temp_dir, metrics_manager):
    """Create a ValidationManager instance."""
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
def sample_effectiveness():
    """Create sample effectiveness data."""
    return RuleEffectiveness(
        rule_id="test_rule",
        rule_name="Test Rule",
        category=ValidationCategory.DESIGN,
        total_validations=100,
        passed_validations=80,
        failed_validations=20,
        total_feedback=50,
        positive_feedback=40,
        negative_feedback=10,
        status=RuleEffectivenessStatus.EFFECTIVE,
        last_updated=datetime.now()
    )

def test_initial_state(validation_manager):
    """Test initial state of the validation manager."""
    assert len(validation_manager._rules) == 0
    assert len(validation_manager._categories) == 0
    assert validation_manager._effectiveness_tracker is not None
    assert validation_manager._improvement_generator is not None

def test_add_rule(validation_manager, sample_rule):
    """Test adding a validation rule."""
    validation_manager.add_rule(sample_rule)
    assert sample_rule.rule_id in validation_manager._rules
    assert sample_rule.category in validation_manager._categories

def test_remove_rule(validation_manager, sample_rule):
    """Test removing a validation rule."""
    validation_manager.add_rule(sample_rule)
    validation_manager.remove_rule(sample_rule.rule_id)
    assert sample_rule.rule_id not in validation_manager._rules
    assert sample_rule.category not in validation_manager._categories

def test_get_rules_by_category(validation_manager, sample_rule):
    """Test getting rules by category."""
    validation_manager.add_rule(sample_rule)
    rules = validation_manager.get_rules_by_category(sample_rule.category)
    assert len(rules) == 1
    assert rules[0].rule_id == sample_rule.rule_id

def test_validate_rule(validation_manager, sample_rule):
    """Test validating a rule."""
    validation_manager.add_rule(sample_rule)
    results = validation_manager.validate({"test": "data"})
    assert len(results) == 1
    assert results[0].rule_id == sample_rule.rule_id

def test_validate_failed_rule(validation_manager, sample_rule):
    """Test validating a rule that fails."""
    validation_manager.add_rule(sample_rule)
    results = validation_manager.validate({})
    assert len(results) == 1
    assert not results[0].passed

def test_add_rule_feedback(validation_manager, sample_rule):
    """Test adding feedback for a rule."""
    validation_manager.add_rule(sample_rule)
    validation_manager.add_rule_feedback(
        sample_rule.rule_id,
        is_positive=True,
        feedback_text="Good rule"
    )
    effectiveness = validation_manager.get_rule_effectiveness(sample_rule.rule_id)
    assert effectiveness is not None
    assert effectiveness.total_feedback == 1
    assert effectiveness.positive_feedback == 1

def test_get_rule_effectiveness(validation_manager, sample_rule, sample_effectiveness):
    """Test getting rule effectiveness."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    effectiveness = validation_manager.get_rule_effectiveness(sample_rule.rule_id)
    assert effectiveness == sample_effectiveness

def test_get_effective_rules(validation_manager, sample_rule, sample_effectiveness):
    """Test getting effective rules."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    effective_rules = validation_manager.get_effective_rules()
    assert len(effective_rules) == 1
    assert effective_rules[0].rule_id == sample_rule.rule_id

def test_get_ineffective_rules(validation_manager, sample_rule):
    """Test getting ineffective rules."""
    validation_manager.add_rule(sample_rule)
    effectiveness = RuleEffectiveness(
        rule_id=sample_rule.rule_id,
        rule_name=sample_rule.name,
        category=sample_rule.category,
        total_validations=100,
        passed_validations=20,
        failed_validations=80,
        total_feedback=50,
        positive_feedback=10,
        negative_feedback=40,
        status=RuleEffectivenessStatus.INEFFECTIVE,
        last_updated=datetime.now()
    )
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = effectiveness
    ineffective_rules = validation_manager.get_ineffective_rules()
    assert len(ineffective_rules) == 1
    assert ineffective_rules[0].rule_id == sample_rule.rule_id

def test_get_rules_needing_improvement(validation_manager, sample_rule):
    """Test getting rules needing improvement."""
    validation_manager.add_rule(sample_rule)
    effectiveness = RuleEffectiveness(
        rule_id=sample_rule.rule_id,
        rule_name=sample_rule.name,
        category=sample_rule.category,
        total_validations=100,
        passed_validations=50,
        failed_validations=50,
        total_feedback=50,
        positive_feedback=25,
        negative_feedback=25,
        status=RuleEffectivenessStatus.NEEDS_IMPROVEMENT,
        last_updated=datetime.now()
    )
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = effectiveness
    rules_needing_improvement = validation_manager.get_rules_needing_improvement()
    assert len(rules_needing_improvement) == 1
    assert rules_needing_improvement[0].rule_id == sample_rule.rule_id

def test_get_effectiveness_summary(validation_manager, sample_rule, sample_effectiveness):
    """Test getting effectiveness summary."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    summary = validation_manager.get_effectiveness_summary()
    assert "total_rules" in summary
    assert "effective_rules" in summary
    assert "ineffective_rules" in summary
    assert "rules_needing_improvement" in summary

def test_get_rule_improvements(validation_manager, sample_rule, sample_effectiveness):
    """Test getting rule improvements."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    improvements = validation_manager.get_rule_improvements(sample_rule.rule_id)
    assert isinstance(improvements, list)

def test_get_high_priority_improvements(validation_manager, sample_rule, sample_effectiveness):
    """Test getting high priority improvements."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    improvements = validation_manager.get_high_priority_improvements()
    assert isinstance(improvements, list)

def test_get_improvements_by_category(validation_manager, sample_rule, sample_effectiveness):
    """Test getting improvements by category."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    improvements = validation_manager.get_improvements_by_category(sample_rule.category)
    assert isinstance(improvements, list)

def test_optimize_rule_parameters(validation_manager, sample_rule, sample_effectiveness):
    """Test optimizing rule parameters."""
    validation_manager.add_rule(sample_rule)
    validation_manager._effectiveness_tracker._effectiveness[sample_rule.rule_id] = sample_effectiveness
    results = validation_manager.optimize_rule_parameters(
        sample_rule.rule_id,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES
    )
    assert isinstance(results, list)
    if results:
        assert isinstance(results[0], OptimizationResult)

def test_get_optimization_history(validation_manager, sample_rule):
    """Test getting optimization history."""
    validation_manager.add_rule(sample_rule)
    history = validation_manager.get_optimization_history(sample_rule.rule_id)
    assert isinstance(history, list)

def test_get_best_optimization(validation_manager, sample_rule):
    """Test getting best optimization."""
    validation_manager.add_rule(sample_rule)
    best = validation_manager.get_best_optimization(sample_rule.rule_id)
    assert best is None or isinstance(best, OptimizationResult)

def test_get_optimization_summary(validation_manager, sample_rule):
    """Test getting optimization summary."""
    validation_manager.add_rule(sample_rule)
    summary = validation_manager.get_optimization_summary(sample_rule.rule_id)
    assert isinstance(summary, dict)
    assert "total_optimizations" in summary
    assert "average_improvement" in summary
    assert "best_improvement" in summary
    assert "optimized_parameters" in summary

def test_apply_optimization(validation_manager, sample_rule):
    """Test applying an optimization."""
    validation_manager.add_rule(sample_rule)
    optimization = OptimizationResult(
        rule_id=sample_rule.rule_id,
        parameter_name="threshold",
        original_value=0.5,
        optimized_value=0.6,
        improvement=0.1,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES,
        metrics={},
        created_at=datetime.now()
    )
    success = validation_manager.apply_optimization(sample_rule.rule_id, optimization)
    assert success
    assert sample_rule.parameters["threshold"] == 0.6

def test_apply_optimization_invalid_parameter(validation_manager, sample_rule):
    """Test applying an optimization with invalid parameter."""
    validation_manager.add_rule(sample_rule)
    optimization = OptimizationResult(
        rule_id=sample_rule.rule_id,
        parameter_name="invalid_param",
        original_value=0.5,
        optimized_value=0.6,
        improvement=0.1,
        strategy=OptimizationStrategy.MINIMIZE_FAILURES,
        metrics={},
        created_at=datetime.now()
    )
    success = validation_manager.apply_optimization(sample_rule.rule_id, optimization)
    assert not success
    assert "threshold" in sample_rule.parameters
    assert sample_rule.parameters["threshold"] == 0.5

@pytest.fixture
def board_data() -> Dict[str, Any]:
    """Create test board data.
    
    Returns:
        Dictionary containing board data
    """
    return {
        "board_size": {
            "width": 100,
            "height": 100
        },
        "drill_sizes": [0.3, 0.4, 0.5],
        "trace_widths": [0.2, 0.3, 0.4],
        "min_spacing": 0.2,
        "min_annular_ring": 0.15
    }
    
def test_validate(validation_manager, board_data: Dict[str, Any]) -> None:
    """Test validation.
    
    Args:
        validation_manager: Validation manager
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 150},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validation_manager.add_rule(rule)
    
    # Validate
    result = validation_manager.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_validate_category(validation_manager, board_data: Dict[str, Any]) -> None:
    """Test validation by category.
    
    Args:
        validation_manager: Validation manager
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 150},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validation_manager.add_rule(rule)
    
    # Validate manufacturing category
    result = validation_manager.validate(
        board_data,
        categories=[ValidationCategory.MANUFACTURING]
    )
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_run_tests(validation_manager) -> None:
    """Test running tests.
    
    Args:
        validation_manager: Validation manager
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 150},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validation_manager.add_rule(rule)
    
    # Run tests
    results = validation_manager.run_tests()
    
    # Check results
    assert ValidationCategory.MANUFACTURING.value in results
    assert "Max Board Size" in results[ValidationCategory.MANUFACTURING.value]
    
def test_run_tests_category(validation_manager) -> None:
    """Test running tests by category.
    
    Args:
        validation_manager: Validation manager
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 150},
                expected_result=True
            )
        ]
    )
    
    # Add rule
    validation_manager.add_rule(rule)
    
    # Run tests for manufacturing category
    results = validation_manager.run_tests(
        categories=[ValidationCategory.MANUFACTURING]
    )
    
    # Check results
    assert ValidationCategory.MANUFACTURING.value in results
    assert "Max Board Size" in results[ValidationCategory.MANUFACTURING.value]
    
def test_multiple_rules(validation_manager, board_data: Dict[str, Any]) -> None:
    """Test multiple rules.
    
    Args:
        validation_manager: Validation manager
        board_data: Test board data
    """
    # Create rules
    rules = [
        ValidationRule(
            name="Max Board Size",
            description="Check maximum board size",
            category=ValidationCategory.MANUFACTURING,
            severity=ValidationSeverity.ERROR,
            test_cases=[
                TestCase(
                    name="Max Size Check",
                    description="Check board size against maximum",
                    input_data={"max_size": 150},
                    expected_result=True
                )
            ]
        ),
        ValidationRule(
            name="Min Drill Size",
            description="Check minimum drill size",
            category=ValidationCategory.MANUFACTURING,
            severity=ValidationSeverity.ERROR,
            test_cases=[
                TestCase(
                    name="Min Drill Check",
                    description="Check drill sizes against minimum",
                    input_data={"min_drill": 0.25},
                    expected_result=True
                )
            ]
        )
    ]
    
    # Add rules
    for rule in rules:
        validation_manager.add_rule(rule)
        
    # Validate
    result = validation_manager.validate(board_data)
    
    # Check result
    assert result.passed
    assert not result.has_errors
    assert not result.has_warnings
    
def test_failing_validation(validation_manager, board_data: Dict[str, Any]) -> None:
    """Test failing validation.
    
    Args:
        validation_manager: Validation manager
        board_data: Test board data
    """
    # Create rule
    rule = ValidationRule(
        name="Max Board Size",
        description="Check maximum board size",
        category=ValidationCategory.MANUFACTURING,
        severity=ValidationSeverity.ERROR,
        test_cases=[
            TestCase(
                name="Max Size Check",
                description="Check board size against maximum",
                input_data={"max_size": 50},
                expected_result=False
            )
        ]
    )
    
    # Add rule
    validation_manager.add_rule(rule)
    
    # Validate
    result = validation_manager.validate(board_data)
    
    # Check result
    assert not result.passed
    assert result.has_errors
    assert not result.has_warnings
    assert result.error_count == 1 