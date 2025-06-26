"""Tests for rule improvement suggestions."""

import pytest
from datetime import datetime, timedelta

from kicad_pcb_generator.core.validation.rule_improvements import (
    RuleImprovementGenerator,
    RuleImprovement,
    ImprovementPriority
)
from kicad_pcb_generator.core.validation.rule_effectiveness import RuleEffectiveness
from kicad_pcb_generator.core.validation.validation_rule import ValidationRule
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationCategory,
    ValidationSeverity
)

@pytest.fixture
def improvement_generator():
    """Create a rule improvement generator."""
    return RuleImprovementGenerator()

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
            "min_value": 0
        },
        dependencies=[],
        severity=ValidationSeverity.ERROR
    )

@pytest.fixture
def effective_rule_data():
    """Create sample data for an effective rule."""
    return RuleEffectiveness(
        rule_id="effective_rule",
        rule_name="Effective Rule",
        category=ValidationCategory.DESIGN,
        total_validations=100,
        passed_validations=90,
        failed_validations=10,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="effective",
        feedback_count=20,
        positive_feedback=18,
        negative_feedback=2
    )

@pytest.fixture
def ineffective_rule_data():
    """Create sample data for an ineffective rule."""
    return RuleEffectiveness(
        rule_id="ineffective_rule",
        rule_name="Ineffective Rule",
        category=ValidationCategory.DESIGN,
        total_validations=100,
        passed_validations=30,
        failed_validations=70,
        average_severity=ValidationSeverity.ERROR.value,
        last_updated=datetime.now(),
        status="ineffective",
        feedback_count=15,
        positive_feedback=5,
        negative_feedback=10
    )

def test_initial_state(improvement_generator):
    """Test the initial state of the improvement generator."""
    assert improvement_generator._improvement_patterns is not None
    assert len(improvement_generator._improvement_patterns) > 0

def test_high_failure_rate_improvement(improvement_generator, ineffective_rule_data):
    """Test generation of improvements for high failure rate."""
    improvements = improvement_generator.generate_improvements(ineffective_rule_data)
    
    # Should have high failure rate improvement
    high_failure = next(
        (imp for imp in improvements if imp.title == "High Failure Rate"),
        None
    )
    assert high_failure is not None
    assert high_failure.priority == ImprovementPriority.HIGH
    assert "failure rate" in high_failure.description
    assert len(high_failure.suggestions) > 0

def test_high_severity_improvement(improvement_generator, ineffective_rule_data):
    """Test generation of improvements for high severity failures."""
    improvements = improvement_generator.generate_improvements(ineffective_rule_data)
    
    # Should have high severity improvement
    high_severity = next(
        (imp for imp in improvements if imp.title == "High Severity Failures"),
        None
    )
    assert high_severity is not None
    assert high_severity.priority == ImprovementPriority.HIGH
    assert "severity" in high_severity.description.lower()
    assert len(high_severity.suggestions) > 0

def test_low_feedback_improvement(improvement_generator):
    """Test generation of improvements for low feedback."""
    rule_data = RuleEffectiveness(
        rule_id="low_feedback_rule",
        rule_name="Low Feedback Rule",
        category=ValidationCategory.DESIGN,
        total_validations=50,
        passed_validations=45,
        failed_validations=5,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="effective",
        feedback_count=3,  # Below threshold
        positive_feedback=2,
        negative_feedback=1
    )
    
    improvements = improvement_generator.generate_improvements(rule_data)
    
    # Should have low feedback improvement
    low_feedback = next(
        (imp for imp in improvements if imp.title == "Low User Feedback"),
        None
    )
    assert low_feedback is not None
    assert low_feedback.priority == ImprovementPriority.MEDIUM
    assert "feedback" in low_feedback.description.lower()
    assert len(low_feedback.suggestions) > 0

def test_negative_feedback_improvement(improvement_generator):
    """Test generation of improvements for high negative feedback."""
    rule_data = RuleEffectiveness(
        rule_id="negative_feedback_rule",
        rule_name="Negative Feedback Rule",
        category=ValidationCategory.DESIGN,
        total_validations=50,
        passed_validations=45,
        failed_validations=5,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="effective",
        feedback_count=10,
        positive_feedback=4,
        negative_feedback=6  # Above threshold
    )
    
    improvements = improvement_generator.generate_improvements(rule_data)
    
    # Should have negative feedback improvement
    negative_feedback = next(
        (imp for imp in improvements if imp.title == "High Negative Feedback"),
        None
    )
    assert negative_feedback is not None
    assert negative_feedback.priority == ImprovementPriority.HIGH
    assert "negative feedback" in negative_feedback.description.lower()
    assert len(negative_feedback.suggestions) > 0

def test_inconsistent_results_improvement(improvement_generator):
    """Test generation of improvements for inconsistent results."""
    rule_data = RuleEffectiveness(
        rule_id="inconsistent_rule",
        rule_name="Inconsistent Rule",
        category=ValidationCategory.DESIGN,
        total_validations=20,  # Above threshold
        passed_validations=10,
        failed_validations=10,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="needs_improvement",
        feedback_count=10,
        positive_feedback=5,
        negative_feedback=5
    )
    
    improvements = improvement_generator.generate_improvements(rule_data)
    
    # Should have inconsistent results improvement
    inconsistent = next(
        (imp for imp in improvements if imp.title == "Inconsistent Results"),
        None
    )
    assert inconsistent is not None
    assert inconsistent.priority == ImprovementPriority.MEDIUM
    assert "inconsistent" in inconsistent.description.lower()
    assert len(inconsistent.suggestions) > 0

def test_rule_specific_improvements(improvement_generator, sample_rule):
    """Test generation of rule-specific improvements."""
    rule_data = RuleEffectiveness(
        rule_id="test_rule",
        rule_name="Test Rule",
        category=ValidationCategory.DESIGN,
        total_validations=50,
        passed_validations=45,
        failed_validations=5,
        average_severity=ValidationSeverity.WARNING.value,
        last_updated=datetime.now(),
        status="effective",
        feedback_count=10,
        positive_feedback=8,
        negative_feedback=2
    )
    
    improvements = improvement_generator.generate_improvements(rule_data, sample_rule)
    
    # Should have parameter-related improvements
    param_improvements = [
        imp for imp in improvements
        if imp.title.startswith("Extreme Parameter Value")
    ]
    assert len(param_improvements) > 0
    
    # Should have dependency-related improvements
    dep_improvements = [
        imp for imp in improvements
        if imp.title == "Missing Dependencies"
    ]
    assert len(dep_improvements) > 0
    
    # Should have documentation-related improvements
    doc_improvements = [
        imp for imp in improvements
        if imp.title == "Minimal Documentation"
    ]
    assert len(doc_improvements) > 0

def test_effective_rule_no_improvements(improvement_generator, effective_rule_data):
    """Test that effective rules don't generate unnecessary improvements."""
    improvements = improvement_generator.generate_improvements(effective_rule_data)
    
    # Should not have high priority improvements
    high_priority = [
        imp for imp in improvements
        if imp.priority == ImprovementPriority.HIGH
    ]
    assert len(high_priority) == 0

def test_improvement_metrics(improvement_generator, ineffective_rule_data):
    """Test that improvements include relevant metrics."""
    improvements = improvement_generator.generate_improvements(ineffective_rule_data)
    
    # Check metrics for high failure rate improvement
    high_failure = next(
        (imp for imp in improvements if imp.title == "High Failure Rate"),
        None
    )
    assert high_failure is not None
    assert "failure_rate" in high_failure.metrics
    assert isinstance(high_failure.metrics["failure_rate"], float)

def test_improvement_creation(improvement_generator, ineffective_rule_data):
    """Test creation of individual improvements."""
    improvement = improvement_generator._create_improvement(
        ineffective_rule_data,
        "Test Improvement",
        "Test description",
        ImprovementPriority.HIGH,
        ["Suggestion 1", "Suggestion 2"],
        {"metric": 0.5}
    )
    
    assert isinstance(improvement, RuleImprovement)
    assert improvement.rule_id == ineffective_rule_data.rule_id
    assert improvement.title == "Test Improvement"
    assert improvement.description == "Test description"
    assert improvement.priority == ImprovementPriority.HIGH
    assert improvement.category == ineffective_rule_data.category
    assert len(improvement.suggestions) == 2
    assert "metric" in improvement.metrics
    assert isinstance(improvement.created_at, datetime) 