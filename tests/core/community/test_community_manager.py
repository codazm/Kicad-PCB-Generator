"""Tests for the CommunityManager class."""

import pytest
from datetime import datetime
from pathlib import Path
import json
import shutil
import tempfile

from kicad_pcb_generator.core.community.community_manager import (
    CommunityManager,
    ForumPost,
    ProjectShare,
    DesignReview
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def community_manager(temp_dir):
    """Create a CommunityManager instance for testing."""
    return CommunityManager(temp_dir)

def test_create_forum_post(community_manager):
    """Test creating a forum post."""
    post = community_manager.create_forum_post(
        title="Test Post",
        content="Test Content",
        author_id="user1",
        tags=["test", "audio"]
    )
    
    assert post.title == "Test Post"
    assert post.content == "Test Content"
    assert post.author_id == "user1"
    assert post.tags == ["test", "audio"]
    assert post.likes == 0
    assert post.views == 0
    assert len(post.replies) == 0
    
    # Verify post was saved
    posts = community_manager.get_forum_posts()
    assert len(posts) == 1
    assert posts[0].id == post.id

def test_create_project_share(community_manager):
    """Test sharing a project."""
    project = community_manager.create_project_share(
        title="Test Project",
        description="Test Description",
        author_id="user1",
        tags=["test", "audio"],
        files={"schematic.kicad_sch": "/path/to/schematic.kicad_sch"}
    )
    
    assert project.title == "Test Project"
    assert project.description == "Test Description"
    assert project.author_id == "user1"
    assert project.tags == ["test", "audio"]
    assert project.files == {"schematic.kicad_sch": "/path/to/schematic.kicad_sch"}
    assert project.likes == 0
    assert project.downloads == 0
    assert len(project.comments) == 0
    
    # Verify project was saved
    projects = community_manager.get_shared_projects()
    assert len(projects) == 1
    assert projects[0].id == project.id

def test_create_design_review(community_manager):
    """Test creating a design review."""
    # First create a project to review
    project = community_manager.create_project_share(
        title="Test Project",
        description="Test Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    review = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user2"
    )
    
    assert review.project_id == project.id
    assert review.reviewer_id == "user2"
    assert review.status == "pending"
    assert len(review.feedback) == 0
    assert review.rating == 0.0
    assert len(review.comments) == 0
    
    # Verify review was saved
    reviews = community_manager.get_design_reviews()
    assert len(reviews) == 1
    assert reviews[0].id == review.id

def test_add_reply(community_manager):
    """Test adding a reply to a forum post."""
    # Create original post
    post = community_manager.create_forum_post(
        title="Original Post",
        content="Original Content",
        author_id="user1",
        tags=["test"]
    )
    
    # Add reply
    reply = community_manager.add_reply(
        post_id=post.id,
        content="Reply Content",
        author_id="user2"
    )
    
    assert reply.title == f"Re: {post.title}"
    assert reply.content == "Reply Content"
    assert reply.author_id == "user2"
    assert reply.tags == post.tags
    
    # Verify reply was added to original post
    updated_post = community_manager.forum_posts[post.id]
    assert len(updated_post.replies) == 1
    assert updated_post.replies[0].id == reply.id

def test_add_review_feedback(community_manager):
    """Test adding feedback to a design review."""
    # Create project and review
    project = community_manager.create_project_share(
        title="Test Project",
        description="Test Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    review = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user2"
    )
    
    # Add feedback
    feedback = {
        "category": "layout",
        "severity": "warning",
        "message": "Consider increasing trace width for power traces"
    }
    
    community_manager.add_review_feedback(review.id, feedback)
    
    # Verify feedback was added
    updated_review = community_manager.design_reviews[review.id]
    assert len(updated_review.feedback) == 1
    assert updated_review.feedback[0] == feedback

def test_update_review_status(community_manager):
    """Test updating a design review status."""
    # Create project and review
    project = community_manager.create_project_share(
        title="Test Project",
        description="Test Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    review = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user2"
    )
    
    # Update status
    community_manager.update_review_status(review.id, "in_progress")
    
    # Verify status was updated
    updated_review = community_manager.design_reviews[review.id]
    assert updated_review.status == "in_progress"

def test_get_forum_posts_with_tags(community_manager):
    """Test getting forum posts filtered by tags."""
    # Create posts with different tags
    post1 = community_manager.create_forum_post(
        title="Audio Post",
        content="Audio Content",
        author_id="user1",
        tags=["audio", "design"]
    )
    
    post2 = community_manager.create_forum_post(
        title="Layout Post",
        content="Layout Content",
        author_id="user2",
        tags=["layout", "design"]
    )
    
    # Get posts with audio tag
    audio_posts = community_manager.get_forum_posts(tags=["audio"])
    assert len(audio_posts) == 1
    assert audio_posts[0].id == post1.id
    
    # Get posts with design tag
    design_posts = community_manager.get_forum_posts(tags=["design"])
    assert len(design_posts) == 2
    
    # Get posts with non-existent tag
    no_posts = community_manager.get_forum_posts(tags=["nonexistent"])
    assert len(no_posts) == 0

def test_get_shared_projects_with_tags(community_manager):
    """Test getting shared projects filtered by tags."""
    # Create projects with different tags
    project1 = community_manager.create_project_share(
        title="Audio Project",
        description="Audio Description",
        author_id="user1",
        tags=["audio", "design"],
        files={}
    )
    
    project2 = community_manager.create_project_share(
        title="Layout Project",
        description="Layout Description",
        author_id="user2",
        tags=["layout", "design"],
        files={}
    )
    
    # Get projects with audio tag
    audio_projects = community_manager.get_shared_projects(tags=["audio"])
    assert len(audio_projects) == 1
    assert audio_projects[0].id == project1.id
    
    # Get projects with design tag
    design_projects = community_manager.get_shared_projects(tags=["design"])
    assert len(design_projects) == 2
    
    # Get projects with non-existent tag
    no_projects = community_manager.get_shared_projects(tags=["nonexistent"])
    assert len(no_projects) == 0

def test_get_design_reviews_by_project(community_manager):
    """Test getting design reviews filtered by project."""
    # Create projects and reviews
    project1 = community_manager.create_project_share(
        title="Project 1",
        description="Description 1",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    project2 = community_manager.create_project_share(
        title="Project 2",
        description="Description 2",
        author_id="user2",
        tags=["test"],
        files={}
    )
    
    review1 = community_manager.create_design_review(
        project_id=project1.id,
        reviewer_id="user3"
    )
    
    review2 = community_manager.create_design_review(
        project_id=project2.id,
        reviewer_id="user4"
    )
    
    # Get reviews for project1
    project1_reviews = community_manager.get_design_reviews(project_id=project1.id)
    assert len(project1_reviews) == 1
    assert project1_reviews[0].id == review1.id
    
    # Get reviews for project2
    project2_reviews = community_manager.get_design_reviews(project_id=project2.id)
    assert len(project2_reviews) == 1
    assert project2_reviews[0].id == review2.id
    
    # Get all reviews
    all_reviews = community_manager.get_design_reviews()
    assert len(all_reviews) == 2

def test_invalid_post_id(community_manager):
    """Test handling invalid post ID."""
    with pytest.raises(ValueError, match="Post invalid_id not found"):
        community_manager.add_reply(
            post_id="invalid_id",
            content="Test Content",
            author_id="user1"
        )

def test_invalid_review_id(community_manager):
    """Test handling invalid review ID."""
    with pytest.raises(ValueError, match="Review invalid_id not found"):
        community_manager.add_review_feedback(
            review_id="invalid_id",
            feedback={"message": "Test feedback"}
        )
    
    with pytest.raises(ValueError, match="Review invalid_id not found"):
        community_manager.update_review_status(
            review_id="invalid_id",
            status="in_progress"
        ) 