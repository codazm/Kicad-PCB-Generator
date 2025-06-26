"""Tests for the CommunityFeedbackManager class."""

import pytest
from datetime import datetime
from pathlib import Path
import json
import shutil
import tempfile

from kicad_pcb_generator.core.community.community_feedback import (
    CommunityFeedbackManager,
    FeedbackItem
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def feedback_manager(temp_dir):
    """Create a CommunityFeedbackManager instance for testing."""
    return CommunityFeedbackManager(temp_dir)

def test_create_feedback(feedback_manager):
    """Test creating feedback."""
    feedback = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Test Bug",
        description="Test Description",
        priority="high"
    )
    
    assert feedback.user_id == "user1"
    assert feedback.type == "bug"
    assert feedback.title == "Test Bug"
    assert feedback.description == "Test Description"
    assert feedback.priority == "high"
    assert feedback.status == "new"
    assert feedback.votes == 0
    assert len(feedback.comments) == 0

def test_update_feedback(feedback_manager):
    """Test updating feedback."""
    feedback = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Test Bug",
        description="Test Description"
    )
    
    updated = feedback_manager.update_feedback(
        feedback.id,
        status="in_progress",
        priority="critical"
    )
    
    assert updated.status == "in_progress"
    assert updated.priority == "critical"
    assert updated.title == "Test Bug"  # Unchanged

def test_add_comment(feedback_manager):
    """Test adding a comment to feedback."""
    feedback = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Test Bug",
        description="Test Description"
    )
    
    comment = feedback_manager.add_comment(
        feedback.id,
        user_id="user2",
        content="Test Comment"
    )
    
    assert comment["user_id"] == "user2"
    assert comment["content"] == "Test Comment"
    
    updated_feedback = feedback_manager.get_feedback(feedback.id)
    assert len(updated_feedback.comments) == 1
    assert updated_feedback.comments[0]["content"] == "Test Comment"

def test_vote_feedback(feedback_manager):
    """Test voting on feedback."""
    feedback = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Test Bug",
        description="Test Description"
    )
    
    feedback_manager.vote_feedback(feedback.id, "user2")
    updated_feedback = feedback_manager.get_feedback(feedback.id)
    
    assert updated_feedback.votes == 1

def test_get_feedback_by_type(feedback_manager):
    """Test getting feedback by type."""
    # Create feedback of different types
    bug = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Bug Report",
        description="Test Bug"
    )
    
    feature = feedback_manager.create_feedback(
        user_id="user2",
        type="feature",
        title="Feature Request",
        description="Test Feature"
    )
    
    # Get bug feedback
    bug_feedback = feedback_manager.get_feedback_by_type("bug")
    assert len(bug_feedback) == 1
    assert bug_feedback[0].id == bug.id
    
    # Get feature feedback
    feature_feedback = feedback_manager.get_feedback_by_type("feature")
    assert len(feature_feedback) == 1
    assert feature_feedback[0].id == feature.id

def test_get_feedback_by_status(feedback_manager):
    """Test getting feedback by status."""
    # Create feedback with different statuses
    new = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="New Bug",
        description="Test Bug"
    )
    
    in_progress = feedback_manager.create_feedback(
        user_id="user2",
        type="bug",
        title="In Progress Bug",
        description="Test Bug"
    )
    feedback_manager.update_feedback(in_progress.id, status="in_progress")
    
    # Get new feedback
    new_feedback = feedback_manager.get_feedback_by_status("new")
    assert len(new_feedback) == 1
    assert new_feedback[0].id == new.id
    
    # Get in-progress feedback
    in_progress_feedback = feedback_manager.get_feedback_by_status("in_progress")
    assert len(in_progress_feedback) == 1
    assert in_progress_feedback[0].id == in_progress.id

def test_get_top_feedback(feedback_manager):
    """Test getting top feedback by votes."""
    # Create feedback with different vote counts
    feedback1 = feedback_manager.create_feedback(
        user_id="user1",
        type="bug",
        title="Bug 1",
        description="Test Bug"
    )
    feedback_manager.vote_feedback(feedback1.id, "user2")
    feedback_manager.vote_feedback(feedback1.id, "user3")
    
    feedback2 = feedback_manager.create_feedback(
        user_id="user2",
        type="bug",
        title="Bug 2",
        description="Test Bug"
    )
    feedback_manager.vote_feedback(feedback2.id, "user1")
    
    # Get top feedback
    top_feedback = feedback_manager.get_top_feedback(limit=1)
    assert len(top_feedback) == 1
    assert top_feedback[0].id == feedback1.id
    assert top_feedback[0].votes == 2

def test_invalid_feedback_id(feedback_manager):
    """Test handling invalid feedback ID."""
    with pytest.raises(ValueError, match="Feedback invalid_id not found"):
        feedback_manager.update_feedback(
            "invalid_id",
            status="in_progress"
        )
    
    with pytest.raises(ValueError, match="Feedback invalid_id not found"):
        feedback_manager.add_comment(
            "invalid_id",
            user_id="user1",
            content="Test Comment"
        )
    
    with pytest.raises(ValueError, match="Feedback invalid_id not found"):
        feedback_manager.vote_feedback("invalid_id", "user1") 
