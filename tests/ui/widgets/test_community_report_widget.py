"""Tests for the CommunityReportWidget class."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import shutil
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QDate

from kicad_pcb_generator.core.community.community_reports import (
    CommunityReportManager,
    CommunityReport
)
from kicad_pcb_generator.core.community.community_metrics import (
    CommunityMetrics,
    UserMetrics
)
from kicad_pcb_generator.core.community.community_feedback import FeedbackItem
from kicad_pcb_generator.ui.widgets.community_report_widget import CommunityReportWidget

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

@pytest.fixture
def report_widget(app, report_manager, sample_metrics, sample_users, sample_feedback):
    """Create a CommunityReportWidget instance for testing."""
    # Generate a report
    report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    return CommunityReportWidget(report_manager)

def test_widget_initialization(report_widget):
    """Test widget initialization."""
    assert report_widget.report_manager is not None
    assert report_widget.active_users_label is not None
    assert report_widget.engagement_label is not None
    assert report_widget.feedback_label is not None
    assert report_widget.users_table is not None
    assert report_widget.feedback_table is not None
    assert report_widget.recommendations_list is not None

def test_load_data(report_widget, sample_metrics, sample_users, sample_feedback):
    """Test loading and displaying report data."""
    # Trigger data load
    report_widget._load_data()
    
    # Check metrics display
    assert str(sample_metrics.active_users) in report_widget.active_users_label.text()
    assert "Engagement Trend" in report_widget.engagement_label.text()
    assert "Feedback Trend" in report_widget.feedback_label.text()
    
    # Check users table
    assert report_widget.users_table.rowCount() == len(sample_users)
    for i, user in enumerate(sample_users):
        assert report_widget.users_table.item(i, 0).text() == user.user_id
        assert report_widget.users_table.item(i, 1).text() == str(user.posts_count)
        assert report_widget.users_table.item(i, 2).text() == str(user.projects_count)
        assert report_widget.users_table.item(i, 3).text() == f"{user.average_rating:.1f}"
    
    # Check feedback table
    assert report_widget.feedback_table.rowCount() == len(sample_feedback)
    for i, feedback in enumerate(sample_feedback):
        assert report_widget.feedback_table.item(i, 0).text() == feedback.title
        assert report_widget.feedback_table.item(i, 1).text() == feedback.type
        assert report_widget.feedback_table.item(i, 2).text() == feedback.priority
        assert report_widget.feedback_table.item(i, 3).text() == feedback.status
        assert report_widget.feedback_table.item(i, 4).text() == str(feedback.votes)
    
    # Check recommendations
    assert "Recommendations" in report_widget.recommendations_list.text()

def test_date_range_selection(report_widget, report_manager, sample_metrics,
                            sample_users, sample_feedback):
    """Test date range selection."""
    # Generate reports with different dates
    now = datetime.now()
    
    # First report
    report1 = report_manager.generate_report(
        metrics=sample_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Second report (1 day later)
    updated_metrics = CommunityMetrics(
        total_users=110,
        active_users=55,
        total_posts=220,
        total_projects=80,
        total_reviews=160,
        average_rating=4.6,
        engagement_score=0.8,
        last_updated=now + timedelta(days=1)
    )
    
    report2 = report_manager.generate_report(
        metrics=updated_metrics,
        top_users=sample_users,
        top_feedback=sample_feedback
    )
    
    # Set date range to include both reports
    report_widget.start_date.setDate(QDate.currentDate().addDays(-2))
    report_widget.end_date.setDate(QDate.currentDate().addDays(2))
    report_widget._load_data()
    
    # Should show the latest report
    assert str(updated_metrics.active_users) in report_widget.active_users_label.text()
    
    # Set date range to include only first report
    report_widget.start_date.setDate(QDate.currentDate().addDays(-2))
    report_widget.end_date.setDate(QDate.currentDate())
    report_widget._load_data()
    
    # Should show the first report
    assert str(sample_metrics.active_users) in report_widget.active_users_label.text()

def test_no_reports_in_range(report_widget):
    """Test handling no reports in date range."""
    # Set date range to future
    report_widget.start_date.setDate(QDate.currentDate().addDays(1))
    report_widget.end_date.setDate(QDate.currentDate().addDays(2))
    
    # Should show message box
    with pytest.raises(AssertionError):  # QMessageBox.information raises this in test
        report_widget._load_data()

def test_error_handling(report_widget, report_manager):
    """Test error handling."""
    # Corrupt the report data
    for report_file in report_manager.reports_path.glob("*.json"):
        with open(report_file, "w") as f:
            f.write("invalid json")
    
    # Should show error message
    with pytest.raises(AssertionError):  # QMessageBox.critical raises this in test
        report_widget._load_data() 
