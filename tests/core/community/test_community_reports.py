"""Tests for the CommunityReportManager class."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import shutil
import tempfile

from kicad_pcb_generator.core.community.community_reports import (
    CommunityReportManager,
    CommunityReport
)
from kicad_pcb_generator.core.community.community_metrics import (
    CommunityMetrics,
    UserMetrics
)
from kicad_pcb_generator.core.community.community_feedback import FeedbackItem

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def report_manager(temp_dir):
    """Create a CommunityReportManager instance for testing."""
    return CommunityReportManager(temp_dir)

@pytest.fixture
def sample_metrics():
    """Create sample community metrics."""
    return CommunityMetrics(
        total_users=100,
        active_users=50,
        total_posts=200,
        total_projects=75,
        total_reviews=150,
        average_rating=4.5,
        engagement_score=0.75,
        last_updated=datetime.now()
    )

@pytest.fixture
def sample_users():
    """Create sample user metrics."""
    return [
        UserMetrics(
            user_id="user1",
            posts_count=10,
            projects_count=5,
            reviews_count=15,
            average_rating=4.8,
            engagement_score=0.9,
            last_active=datetime.now()
        ),
        UserMetrics(
            user_id="user2",
            posts_count=5,
            projects_count=3,
            reviews_count=8,
            average_rating=4.5,
            engagement_score=0.7,
            last_active=datetime.now()
        )
    ]

@pytest.fixture
def sample_feedback():
    """Create sample feedback items."""
    return [
        FeedbackItem(
            id="1",
            user_id="user1",
            type="bug",
            title="Bug 1",
            description="Test Bug",
            status="new",
            priority="high",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            votes=5,
            comments=[]
        ),
        FeedbackItem(
            id="2",
            user_id="user2",
            type="feature",
            title="Feature 1",
            description="Test Feature",
            status="in_progress",
            priority="medium",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            votes=3,
            comments=[]
        )
    ]

def test_generate_report(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test generating a community report."""
    report = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    assert report.metrics == sample_metrics
    assert report.top_users == sample_users
    assert report.top_feedback == sample_feedback
    assert report.active_users_count == sample_metrics.active_users
    assert isinstance(report.engagement_trend, float)
    assert isinstance(report.feedback_trend, float)
    assert isinstance(report.recommendations, list)

def test_get_report(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test getting a specific report."""
    report = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    retrieved = report_manager.get_report(report.id)
    assert retrieved == report

def test_get_latest_report(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test getting the latest report."""
    # Generate reports with different timestamps
    report1 = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Update metrics for second report
    updated_metrics = CommunityMetrics(
        total_users=110,
        active_users=55,
        total_posts=220,
        total_projects=80,
        total_reviews=160,
        average_rating=4.6,
        engagement_score=0.8,
        last_updated=datetime.now()
    )
    
    report2 = report_manager.generate_report(
        metrics=updated_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    latest = report_manager.get_latest_report()
    assert latest.id == report2.id

def test_get_reports_by_date_range(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test getting reports within a date range."""
    # Generate reports
    report1 = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Update metrics for second report
    updated_metrics = CommunityMetrics(
        total_users=110,
        active_users=55,
        total_posts=220,
        total_projects=80,
        total_reviews=160,
        average_rating=4.6,
        engagement_score=0.8,
        last_updated=datetime.now()
    )
    
    report2 = report_manager.generate_report(
        metrics=updated_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Get reports in date range
    start_date = report1.created_at - timedelta(days=1)
    end_date = report2.created_at + timedelta(days=1)
    
    reports = report_manager.get_reports_by_date_range(start_date, end_date)
    assert len(reports) == 2
    
    # Get reports outside date range
    future_date = report2.created_at + timedelta(days=2)
    future_reports = report_manager.get_reports_by_date_range(future_date, future_date)
    assert len(future_reports) == 0

def test_calculate_trends(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test calculating engagement and feedback trends."""
    # Generate first report
    report1 = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Update metrics for second report
    updated_metrics = CommunityMetrics(
        total_users=110,
        active_users=55,
        total_posts=220,
        total_projects=80,
        total_reviews=160,
        average_rating=4.6,
        engagement_score=0.8,
        last_updated=datetime.now()
    )
    
    report2 = report_manager.generate_report(
        metrics=updated_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Check trends
    assert report2.engagement_trend > 0  # Increased engagement
    assert report2.feedback_trend > 0  # Increased feedback

def test_generate_recommendations(report_manager, sample_metrics, sample_users, sample_feedback):
    """Test generating recommendations."""
    # Create metrics with low engagement
    low_engagement_metrics = CommunityMetrics(
        total_users=100,
        active_users=20,  # Low active users
        total_posts=50,
        total_projects=10,
        total_reviews=30,
        average_rating=4.0,
        engagement_score=0.3,  # Low engagement
        last_updated=datetime.now()
    )
    
    # Create feedback with critical items
    critical_feedback = [
        FeedbackItem(
            id="1",
            user_id="user1",
            type="bug",
            title="Critical Bug",
            description="Test Bug",
            status="new",
            priority="critical",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            votes=5,
            comments=[]
        )
    ]
    
    report = report_manager.generate_report(
        metrics=low_engagement_metrics,
        top_users=sample_users,
        top_feedback=critical_feedback
    )
    
    # Check recommendations
    assert len(report.recommendations) > 0
    assert any("engagement" in rec.lower() for rec in report.recommendations)
    assert any("critical" in rec.lower() for rec in report.recommendations) 