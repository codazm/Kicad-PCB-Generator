"""Tests for the CommunityWidget class."""

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import tempfile
import shutil
from pathlib import Path

from kicad_pcb_generator.core.community.community_manager import (
    CommunityManager,
    ForumPost,
    ProjectShare,
    DesignReview
)
from kicad_pcb_generator.ui.widgets.community_widget import CommunityWidget

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
def community_manager(temp_dir):
    """Create a CommunityManager instance for testing."""
    return CommunityManager(temp_dir)

@pytest.fixture
def community_widget(app, community_manager):
    """Create a CommunityWidget instance for testing."""
    return CommunityWidget(community_manager)

def test_initial_state(community_widget):
    """Test the initial state of the widget."""
    assert community_widget.tab_widget.count() == 3
    assert community_widget.tab_widget.tabText(0) == "Forum"
    assert community_widget.tab_widget.tabText(1) == "Projects"
    assert community_widget.tab_widget.tabText(2) == "Reviews"
    
    assert community_widget.posts_list.count() == 0
    assert community_widget.projects_list.count() == 0
    assert community_widget.reviews_list.topLevelItemCount() == 0

def test_load_forum_posts(community_widget, community_manager):
    """Test loading forum posts."""
    # Create test posts
    post1 = community_manager.create_forum_post(
        title="Test Post 1",
        content="Content 1",
        author_id="user1",
        tags=["test"]
    )
    
    post2 = community_manager.create_forum_post(
        title="Test Post 2",
        content="Content 2",
        author_id="user2",
        tags=["test"]
    )
    
    # Load posts
    community_widget._load_forum_posts()
    
    assert community_widget.posts_list.count() == 2
    assert community_widget.posts_list.item(0).text() == post1.title
    assert community_widget.posts_list.item(1).text() == post2.title

def test_load_projects(community_widget, community_manager):
    """Test loading shared projects."""
    # Create test projects
    project1 = community_manager.create_project_share(
        title="Test Project 1",
        description="Description 1",
        author_id="user1",
        tags=["test"],
        files={"schematic.kicad_sch": "/path/to/schematic1.kicad_sch"}
    )
    
    project2 = community_manager.create_project_share(
        title="Test Project 2",
        description="Description 2",
        author_id="user2",
        tags=["test"],
        files={"schematic.kicad_sch": "/path/to/schematic2.kicad_sch"}
    )
    
    # Load projects
    community_widget._load_projects()
    
    assert community_widget.projects_list.count() == 2
    assert community_widget.projects_list.item(0).text() == project1.title
    assert community_widget.projects_list.item(1).text() == project2.title

def test_load_reviews(community_widget, community_manager):
    """Test loading design reviews."""
    # Create test project and reviews
    project = community_manager.create_project_share(
        title="Test Project",
        description="Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    review1 = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user2"
    )
    
    review2 = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user3"
    )
    
    # Load reviews
    community_widget._load_reviews()
    
    assert community_widget.reviews_list.topLevelItemCount() == 2
    assert community_widget.reviews_list.topLevelItem(0).text(0) == project.title
    assert community_widget.reviews_list.topLevelItem(1).text(0) == project.title

def test_filter_forum_posts(community_widget, community_manager):
    """Test filtering forum posts."""
    # Create test posts
    post1 = community_manager.create_forum_post(
        title="Audio Post",
        content="Audio content",
        author_id="user1",
        tags=["audio"]
    )
    
    post2 = community_manager.create_forum_post(
        title="Layout Post",
        content="Layout content",
        author_id="user2",
        tags=["layout"]
    )
    
    # Load posts
    community_widget._load_forum_posts()
    
    # Filter by title
    community_widget.forum_search.setText("Audio")
    community_widget._filter_forum_posts()
    assert community_widget.posts_list.count() == 1
    assert community_widget.posts_list.item(0).text() == post1.title
    
    # Filter by content
    community_widget.forum_search.setText("Layout")
    community_widget._filter_forum_posts()
    assert community_widget.posts_list.count() == 1
    assert community_widget.posts_list.item(0).text() == post2.title
    
    # Filter by tag
    community_widget.forum_search.setText("audio")
    community_widget._filter_forum_posts()
    assert community_widget.posts_list.count() == 1
    assert community_widget.posts_list.item(0).text() == post1.title

def test_filter_projects(community_widget, community_manager):
    """Test filtering projects."""
    # Create test projects
    project1 = community_manager.create_project_share(
        title="Audio Project",
        description="Audio description",
        author_id="user1",
        tags=["audio"],
        files={}
    )
    
    project2 = community_manager.create_project_share(
        title="Layout Project",
        description="Layout description",
        author_id="user2",
        tags=["layout"],
        files={}
    )
    
    # Load projects
    community_widget._load_projects()
    
    # Filter by title
    community_widget.project_search.setText("Audio")
    community_widget._filter_projects()
    assert community_widget.projects_list.count() == 1
    assert community_widget.projects_list.item(0).text() == project1.title
    
    # Filter by description
    community_widget.project_search.setText("Layout")
    community_widget._filter_projects()
    assert community_widget.projects_list.count() == 1
    assert community_widget.projects_list.item(0).text() == project2.title
    
    # Filter by tag
    community_widget.project_search.setText("audio")
    community_widget._filter_projects()
    assert community_widget.projects_list.count() == 1
    assert community_widget.projects_list.item(0).text() == project1.title

def test_show_post_content(community_widget, community_manager):
    """Test showing post content."""
    # Create test post
    post = community_manager.create_forum_post(
        title="Test Post",
        content="Test Content",
        author_id="user1",
        tags=["test"]
    )
    
    # Load posts
    community_widget._load_forum_posts()
    
    # Select post
    community_widget.posts_list.setCurrentRow(0)
    
    assert community_widget.post_title.text() == post.title
    assert community_widget.post_content.toPlainText() == post.content

def test_show_project_details(community_widget, community_manager):
    """Test showing project details."""
    # Create test project
    project = community_manager.create_project_share(
        title="Test Project",
        description="Test Description",
        author_id="user1",
        tags=["test"],
        files={
            "schematic.kicad_sch": "/path/to/schematic.kicad_sch",
            "board.kicad_pcb": "/path/to/board.kicad_pcb"
        }
    )
    
    # Load projects
    community_widget._load_projects()
    
    # Select project
    community_widget.projects_list.setCurrentRow(0)
    
    assert community_widget.project_title.text() == project.title
    assert community_widget.project_description.toPlainText() == project.description
    
    # Check files list
    assert community_widget.files_list.topLevelItemCount() == 2
    assert community_widget.files_list.topLevelItem(0).text(0) == "schematic.kicad_sch"
    assert community_widget.files_list.topLevelItem(0).text(1) == "Schematic"
    assert community_widget.files_list.topLevelItem(1).text(0) == "board.kicad_pcb"
    assert community_widget.files_list.topLevelItem(1).text(1) == "PCB"

def test_show_review_details(community_widget, community_manager):
    """Test showing review details."""
    # Create test project and review
    project = community_manager.create_project_share(
        title="Test Project",
        description="Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    review = community_manager.create_design_review(
        project_id=project.id,
        reviewer_id="user2"
    )
    
    # Add feedback and comments
    feedback = {
        "category": "layout",
        "severity": "warning",
        "message": "Test feedback"
    }
    community_manager.add_review_feedback(review.id, feedback)
    
    comment = community_manager.create_forum_post(
        title="Test Comment",
        content="Test comment content",
        author_id="user3",
        tags=["test"]
    )
    review.comments.append(comment)
    
    # Load reviews
    community_widget._load_reviews()
    
    # Select review
    community_widget.reviews_list.setCurrentItem(
        community_widget.reviews_list.topLevelItem(0)
    )
    
    assert community_widget.review_status.text() == f"Status: {review.status}"
    
    # Check feedback tree
    assert community_widget.feedback_tree.topLevelItemCount() == 1
    assert community_widget.feedback_tree.topLevelItem(0).text(0) == feedback["category"]
    assert community_widget.feedback_tree.topLevelItem(0).text(1) == feedback["severity"]
    assert community_widget.feedback_tree.topLevelItem(0).text(2) == feedback["message"]
    
    # Check comments list
    assert community_widget.comments_list.count() == 1
    assert community_widget.comments_list.item(0).text() == f"{comment.author_id}: {comment.content}"

def test_add_reply(community_widget, community_manager):
    """Test adding a reply to a forum post."""
    # Create test post
    post = community_manager.create_forum_post(
        title="Test Post",
        content="Test Content",
        author_id="user1",
        tags=["test"]
    )
    
    # Load posts
    community_widget._load_forum_posts()
    
    # Select post
    community_widget.posts_list.setCurrentRow(0)
    
    # Add reply
    community_widget.reply_input.setText("Test Reply")
    community_widget._add_reply()
    
    # Check reply was added
    updated_post = community_manager.forum_posts[post.id]
    assert len(updated_post.replies) == 1
    assert updated_post.replies[0].content == "Test Reply"
    assert updated_post.replies[0].author_id == "current_user"

def test_request_review(community_widget, community_manager):
    """Test requesting a review."""
    # Create test project
    project = community_manager.create_project_share(
        title="Test Project",
        description="Description",
        author_id="user1",
        tags=["test"],
        files={}
    )
    
    # Load projects
    community_widget._load_projects()
    
    # Select project
    community_widget.projects_list.setCurrentRow(0)
    
    # Connect signal
    requested_project_id = None
    def on_review_requested(project_id):
        nonlocal requested_project_id
        requested_project_id = project_id
    
    community_widget.review_requested.connect(on_review_requested)
    
    # Request review
    community_widget._request_review()
    
    assert requested_project_id == project.id 