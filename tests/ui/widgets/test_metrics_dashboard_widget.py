"""Tests for the MetricsDashboardWidget class."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QDateTime
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json

from kicad_pcb_generator.core.community.community_metrics import (
    CommunityMetricsManager,
    CommunityMetrics,
    UserMetrics,
    MetricTrend
)
from kicad_pcb_generator.ui.widgets.metrics_dashboard_widget import MetricsDashboardWidget

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
def metrics_manager(temp_dir):
    """Create a CommunityMetricsManager instance for testing."""
    return CommunityMetricsManager(temp_dir)

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
def metrics_widget(app, metrics_manager, sample_metrics, sample_users):
    """Create a MetricsDashboardWidget instance for testing."""
    # Update metrics
    metrics_manager.update_community_metrics(sample_metrics)
    for user in sample_users:
        metrics_manager.update_user_metrics(user)
    
    return MetricsDashboardWidget(metrics_manager)

def test_initial_state(metrics_widget):
    """Test the initial state of the widget."""
    assert metrics_widget.tab_widget.count() == 3
    assert metrics_widget.tab_widget.tabText(0) == "Overview"
    assert metrics_widget.tab_widget.tabText(1) == "Trends"
    assert metrics_widget.tab_widget.tabText(2) == "Users"
    
    # Check overview tab elements
    assert metrics_widget.total_users_label is not None
    assert metrics_widget.active_users_label is not None
    assert metrics_widget.engagement_label is not None
    assert metrics_widget.metrics_table is not None
    
    # Check trends tab elements
    assert metrics_widget.metric_combo is not None
    assert metrics_widget.trend_period_combo is not None
    assert metrics_widget.trend_chart is not None
    assert metrics_widget.trend_summary is not None
    
    # Check users tab elements
    assert metrics_widget.users_table is not None

def test_update_overview(metrics_widget, sample_metrics):
    """Test updating the overview tab."""
    metrics_widget._update_overview()
    
    # Check key metrics
    assert str(sample_metrics.total_users) in metrics_widget.total_users_label.text()
    assert str(sample_metrics.active_users) in metrics_widget.active_users_label.text()
    assert f"{sample_metrics.engagement_score:.2f}" in metrics_widget.engagement_label.text()
    assert str(sample_metrics.total_posts) in metrics_widget.total_posts_label.text()
    assert str(sample_metrics.total_projects) in metrics_widget.total_projects_label.text()
    assert str(sample_metrics.total_reviews) in metrics_widget.total_reviews_label.text()
    
    # Check metrics table
    assert metrics_widget.metrics_table.rowCount() > 0
    assert metrics_widget.metrics_table.columnCount() == 5

def test_update_trend_chart(metrics_widget, metrics_manager):
    """Test updating the trend chart."""
    # Create trend data
    now = datetime.now()
    metrics_manager.metrics_history["total_users"] = [
        (now - timedelta(days=2), 90),
        (now - timedelta(days=1), 95),
        (now, 100)
    ]
    
    # Update chart
    metrics_widget.metric_combo.setCurrentText("Total Users")
    metrics_widget._update_trend_chart()
    
    # Check chart elements
    assert metrics_widget.trend_chart.series()
    assert "increased" in metrics_widget.trend_summary.text()

def test_update_users_table(metrics_widget, sample_users):
    """Test updating the users table."""
    metrics_widget._update_users_table()
    
    # Check table content
    assert metrics_widget.users_table.rowCount() == len(sample_users)
    assert metrics_widget.users_table.columnCount() == 7
    
    # Check first user data
    assert metrics_widget.users_table.item(0, 0).text() == sample_users[0].user_id
    assert metrics_widget.users_table.item(0, 1).text() == str(sample_users[0].posts_count)
    assert metrics_widget.users_table.item(0, 2).text() == str(sample_users[0].projects_count)
    assert metrics_widget.users_table.item(0, 3).text() == str(sample_users[0].reviews_count)
    assert metrics_widget.users_table.item(0, 4).text() == f"{sample_users[0].average_rating:.2f}"
    assert metrics_widget.users_table.item(0, 5).text() == f"{sample_users[0].engagement_score:.2f}"

def test_export_data(metrics_widget, temp_dir):
    """Test exporting metrics data."""
    # Set up export path
    export_path = Path(temp_dir) / "metrics_export.json"
    
    # Mock file dialog
    def mock_get_save_file_name(*args, **kwargs):
        return str(export_path), ""
    
    metrics_widget.file_dialog = mock_get_save_file_name
    
    # Export data
    metrics_widget._export_data()
    
    # Check exported file
    assert export_path.exists()
    with open(export_path) as f:
        data = json.load(f)
        assert "community_metrics" in data
        assert "user_metrics" in data
        assert "metrics_history" in data

def test_period_selection(metrics_widget):
    """Test time period selection."""
    # Test different periods
    periods = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last year": 365
    }
    
    for period, days in periods.items():
        metrics_widget.period_combo.setCurrentText(period)
        assert metrics_widget._get_days_from_period(period) == days

def test_metric_selection(metrics_widget):
    """Test metric selection in trends tab."""
    metrics = [
        "Total Users", "Active Users", "Total Posts",
        "Total Projects", "Total Reviews", "Engagement Score"
    ]
    
    for metric in metrics:
        metrics_widget.metric_combo.setCurrentText(metric)
        metrics_widget._update_trend_chart()
        assert metrics_widget.trend_chart.title() == "Metric Trend"

def test_error_handling(metrics_widget, metrics_manager):
    """Test error handling in the widget."""
    # Test with invalid metric
    metrics_widget.metric_combo.setCurrentText("Invalid Metric")
    metrics_widget._update_trend_chart()
    assert metrics_widget.trend_chart.series() == []
    
    # Test with no data
    metrics_manager.community_metrics = None
    metrics_widget._update_overview()
    assert metrics_widget.total_users_label.text() == "Total Users: 0" 