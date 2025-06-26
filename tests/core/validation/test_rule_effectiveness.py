"""Tests for the rule effectiveness tracking module."""

import pytest
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path
import json

from kicad_pcb_generator.core.validation.rule_effectiveness import (
    RuleEffectivenessTracker,
    RuleEffectiveness,
    RuleEffectivenessStatus
)
from kicad_pcb_generator.core.validation.validation_rule import ValidationRule
from kicad_pcb_generator.core.validation.validation_results import (
    ValidationCategory,
    ValidationSeverity
)
from kicad_pcb_generator.core.community.community_metrics import (
    CommunityMetricsManager,
    CommunityMetrics
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def metrics_manager(temp_dir):
    """Create a CommunityMetricsManager instance."""
    return CommunityMetricsManager(temp_dir)

@pytest.fixture
def effectiveness_tracker(temp_dir, metrics_manager):
    """Create a RuleEffectivenessTracker instance."""
    return RuleEffectivenessTracker(Path(temp_dir), metrics_manager)

@pytest.fixture
def sample_rule():
    """Create a sample validation rule."""
    return ValidationRule(
        name="test_rule",
        description="Test rule",
        category=ValidationCategory.DESIGN_RULES,
        severity=ValidationSeverity.WARNING
    )

def test_initial_state(effectiveness_tracker):
    """Test initial state of the tracker."""
    assert len(effectiveness_tracker.effectiveness_data) == 0
    assert effectiveness_tracker.get_effectiveness_summary() == {
        "total_rules": 0,
        "effective_rules": 0,
        "ineffective_rules": 0,
        "needs_improvement": 0,
        "effectiveness_rate": 0
    }

def test_track_validation(effectiveness_tracker, sample_rule):
    """Test tracking validation results."""
    # Track successful validation
    effectiveness_tracker.track_validation(
        sample_rule,
        passed=True,
        severity=ValidationSeverity.WARNING
    )
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness is not None
    assert effectiveness.total_validations == 1
    assert effectiveness.passed_validations == 1
    assert effectiveness.failed_validations == 0
    assert effectiveness.status == RuleEffectivenessStatus.UNKNOWN
    
    # Track failed validation
    effectiveness_tracker.track_validation(
        sample_rule,
        passed=False,
        severity=ValidationSeverity.ERROR
    )
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness.total_validations == 2
    assert effectiveness.passed_validations == 1
    assert effectiveness.failed_validations == 1
    assert effectiveness.status == RuleEffectivenessStatus.UNKNOWN

def test_add_feedback(effectiveness_tracker, sample_rule):
    """Test adding feedback for rules."""
    # Track some validations first
    for _ in range(10):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=True,
            severity=ValidationSeverity.WARNING
        )
    
    # Add positive feedback
    effectiveness_tracker.add_feedback(sample_rule.name, is_positive=True)
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness.feedback_count == 1
    assert effectiveness.positive_feedback == 1
    assert effectiveness.negative_feedback == 0
    assert effectiveness.status == RuleEffectivenessStatus.EFFECTIVE
    
    # Add negative feedback
    effectiveness_tracker.add_feedback(sample_rule.name, is_positive=False)
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness.feedback_count == 2
    assert effectiveness.positive_feedback == 1
    assert effectiveness.negative_feedback == 1
    assert effectiveness.status == RuleEffectivenessStatus.NEEDS_IMPROVEMENT

def test_rule_status_updates(effectiveness_tracker, sample_rule):
    """Test rule status updates based on metrics."""
    # Add enough validations and feedback to determine status
    for _ in range(10):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=True,
            severity=ValidationSeverity.WARNING
        )
    
    # Add mostly positive feedback
    for _ in range(8):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=True)
    for _ in range(2):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=False)
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness.status == RuleEffectivenessStatus.EFFECTIVE
    
    # Add more negative feedback
    for _ in range(5):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=False)
    
    effectiveness = effectiveness_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness.status == RuleEffectivenessStatus.NEEDS_IMPROVEMENT

def test_community_metrics_integration(effectiveness_tracker, sample_rule, metrics_manager):
    """Test integration with community metrics."""
    # Track some validations
    for _ in range(5):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=True,
            severity=ValidationSeverity.WARNING
        )
    
    # Check community metrics
    metrics = metrics_manager.get_community_metrics()
    assert hasattr(metrics, 'rule_effectiveness')
    assert metrics.rule_effectiveness['total_validations'] == 5
    assert metrics.rule_effectiveness['passed_validations'] == 5
    assert metrics.rule_effectiveness['failed_validations'] == 0

def test_persistence(effectiveness_tracker, sample_rule, temp_dir):
    """Test persistence of effectiveness data."""
    # Add some data
    effectiveness_tracker.track_validation(
        sample_rule,
        passed=True,
        severity=ValidationSeverity.WARNING
    )
    effectiveness_tracker.add_feedback(sample_rule.name, is_positive=True)
    
    # Create new tracker instance
    new_tracker = RuleEffectivenessTracker(Path(temp_dir), effectiveness_tracker.metrics_manager)
    
    # Check data persistence
    effectiveness = new_tracker.get_rule_effectiveness(sample_rule.name)
    assert effectiveness is not None
    assert effectiveness.total_validations == 1
    assert effectiveness.passed_validations == 1
    assert effectiveness.feedback_count == 1
    assert effectiveness.positive_feedback == 1

def test_get_effective_rules(effectiveness_tracker, sample_rule):
    """Test getting effective rules."""
    # Add enough validations and positive feedback
    for _ in range(10):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=True,
            severity=ValidationSeverity.WARNING
        )
    for _ in range(8):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=True)
    
    effective_rules = effectiveness_tracker.get_effective_rules()
    assert len(effective_rules) == 1
    assert effective_rules[0].rule_id == sample_rule.name

def test_get_ineffective_rules(effectiveness_tracker, sample_rule):
    """Test getting ineffective rules."""
    # Add validations with failures and negative feedback
    for _ in range(10):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=False,
            severity=ValidationSeverity.ERROR
        )
    for _ in range(8):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=False)
    
    ineffective_rules = effectiveness_tracker.get_ineffective_rules()
    assert len(ineffective_rules) == 1
    assert ineffective_rules[0].rule_id == sample_rule.name

def test_get_rules_needing_improvement(effectiveness_tracker, sample_rule):
    """Test getting rules needing improvement."""
    # Add mixed results
    for _ in range(10):
        effectiveness_tracker.track_validation(
            sample_rule,
            passed=True,
            severity=ValidationSeverity.WARNING
        )
    for _ in range(5):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=True)
    for _ in range(5):
        effectiveness_tracker.add_feedback(sample_rule.name, is_positive=False)
    
    improvement_rules = effectiveness_tracker.get_rules_needing_improvement()
    assert len(improvement_rules) == 1
    assert improvement_rules[0].rule_id == sample_rule.name 