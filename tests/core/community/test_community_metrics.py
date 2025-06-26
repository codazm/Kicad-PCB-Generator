"""Tests for the CommunityMetricsManager class."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import shutil
import tempfile

from kicad_pcb_generator.core.community.community_metrics import (
    CommunityMetricsManager,
    CommunityMetrics,
    UserMetrics
)

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

def test_create_community_metrics(metrics_manager):
    """Test creating community metrics."""
    metrics = CommunityMetrics(
        total_users=100,
        active_users=50,
        total_posts=200,
        total_projects=75,
        total_reviews=150,
        average_rating=4.5,
        engagement_score=0.75,
        last_updated=datetime.now()
    )
    
    metrics_manager.update_community_metrics(metrics)
    saved_metrics = metrics_manager.get_community_metrics()
    
    assert saved_metrics.total_users == 100
    assert saved_metrics.active_users == 50
    assert saved_metrics.total_posts == 200
    assert saved_metrics.total_projects == 75
    assert saved_metrics.total_reviews == 150
    assert saved_metrics.average_rating == 4.5
    assert saved_metrics.engagement_score == 0.75

def test_create_user_metrics(metrics_manager):
    """Test creating user metrics."""
    metrics = UserMetrics(
        user_id="user1",
        posts_count=10,
        projects_count=5,
        reviews_count=15,
        average_rating=4.8,
        engagement_score=0.9,
        last_active=datetime.now()
    )
    
    metrics_manager.update_user_metrics(metrics)
    saved_metrics = metrics_manager.get_user_metrics("user1")
    
    assert saved_metrics.user_id == "user1"
    assert saved_metrics.posts_count == 10
    assert saved_metrics.projects_count == 5
    assert saved_metrics.reviews_count == 15
    assert saved_metrics.average_rating == 4.8
    assert saved_metrics.engagement_score == 0.9

def test_get_top_users(metrics_manager):
    """Test getting top users by engagement score."""
    # Create users with different engagement scores
    user1 = UserMetrics(
        user_id="user1",
        posts_count=10,
        projects_count=5,
        reviews_count=15,
        average_rating=4.8,
        engagement_score=0.9,
        last_active=datetime.now()
    )
    
    user2 = UserMetrics(
        user_id="user2",
        posts_count=5,
        projects_count=3,
        reviews_count=8,
        average_rating=4.5,
        engagement_score=0.7,
        last_active=datetime.now()
    )
    
    user3 = UserMetrics(
        user_id="user3",
        posts_count=3,
        projects_count=2,
        reviews_count=5,
        average_rating=4.2,
        engagement_score=0.5,
        last_active=datetime.now()
    )
    
    metrics_manager.update_user_metrics(user1)
    metrics_manager.update_user_metrics(user2)
    metrics_manager.update_user_metrics(user3)
    
    # Get top 2 users
    top_users = metrics_manager.get_top_users(limit=2)
    assert len(top_users) == 2
    assert top_users[0].user_id == "user1"
    assert top_users[1].user_id == "user2"

def test_get_active_users(metrics_manager):
    """Test getting active users."""
    now = datetime.now()
    
    # Create active and inactive users
    active_user = UserMetrics(
        user_id="active",
        posts_count=10,
        projects_count=5,
        reviews_count=15,
        average_rating=4.8,
        engagement_score=0.9,
        last_active=now
    )
    
    inactive_user = UserMetrics(
        user_id="inactive",
        posts_count=5,
        projects_count=3,
        reviews_count=8,
        average_rating=4.5,
        engagement_score=0.7,
        last_active=now - timedelta(days=31)
    )
    
    metrics_manager.update_user_metrics(active_user)
    metrics_manager.update_user_metrics(inactive_user)
    
    # Get users active in last 30 days
    active_users = metrics_manager.get_active_users(days=30)
    assert len(active_users) == 1
    assert active_users[0].user_id == "active"

def test_invalid_user_metrics(metrics_manager):
    """Test handling invalid user metrics."""
    assert metrics_manager.get_user_metrics("nonexistent") is None 