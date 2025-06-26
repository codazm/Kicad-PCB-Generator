"""Community management system for the KiCad PCB Generator."""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json
import os
import logging
from pathlib import Path

from ..base.base_manager import BaseManager
from ..base.results.manager_result import ManagerResult, ManagerOperation, ManagerStatus

@dataclass
class ForumPost:
    """Represents a forum post."""
    id: str
    title: str
    content: str
    author_id: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    replies: List['ForumPost']
    likes: int
    views: int

@dataclass
class ProjectShare:
    """Represents a shared project."""
    id: str
    title: str
    description: str
    author_id: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    files: Dict[str, str]  # filename -> filepath
    likes: int
    downloads: int
    comments: List[ForumPost]

@dataclass
class DesignReview:
    """Represents a design review."""
    id: str
    project_id: str
    reviewer_id: str
    created_at: datetime
    updated_at: datetime
    status: str  # pending, in_progress, completed
    feedback: List[Dict[str, Any]]
    rating: float
    comments: List[ForumPost]

class CommunityManager(BaseManager[ForumPost]):
    """Manages community features including forums, project sharing, and design reviews.
    
    Now inherits from BaseManager for standardized CRUD operations on ForumPost objects.
    """
    
    def __init__(self, storage_path: str, logger: Optional[logging.Logger] = None):
        """Initialize community manager.
        
        Args:
            storage_path: Path to store community data
            logger: Optional logger instance
        """
        super().__init__()
        self.storage_path = Path(storage_path)
        self.logger = logger or logging.getLogger(__name__)
        
        # Create storage directories
        self.forums_path = self.storage_path / "forums"
        self.projects_path = self.storage_path / "projects"
        self.reviews_path = self.storage_path / "reviews"
        
        for path in [self.forums_path, self.projects_path, self.reviews_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.shared_projects: Dict[str, ProjectShare] = {}
        self.design_reviews: Dict[str, DesignReview] = {}
        
        self._load_data()
    
    def _load_data(self) -> None:
        """Load community data from storage."""
        try:
            # Load forum posts using BaseManager
            for post_file in self.forums_path.glob("*.json"):
                with open(post_file, "r") as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    # Handle replies recursively
                    if 'replies' in data:
                        replies = []
                        for reply_data in data['replies']:
                            reply_data['created_at'] = datetime.fromisoformat(reply_data['created_at'])
                            reply_data['updated_at'] = datetime.fromisoformat(reply_data['updated_at'])
                            replies.append(ForumPost(**reply_data))
                        data['replies'] = replies
                    
                    post = ForumPost(**data)
                    # Use BaseManager's create method
                    self.create(post.id, post)
            
            # Load shared projects
            for project_file in self.projects_path.glob("*.json"):
                with open(project_file, "r") as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    # Handle comments
                    if 'comments' in data:
                        comments = []
                        for comment_data in data['comments']:
                            comment_data['created_at'] = datetime.fromisoformat(comment_data['created_at'])
                            comment_data['updated_at'] = datetime.fromisoformat(comment_data['updated_at'])
                            comments.append(ForumPost(**comment_data))
                        data['comments'] = comments
                    
                    project = ProjectShare(**data)
                    self.shared_projects[project.id] = project
            
            # Load design reviews
            for review_file in self.reviews_path.glob("*.json"):
                with open(review_file, "r") as f:
                    data = json.load(f)
                    # Convert datetime strings back to datetime objects
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    # Handle comments
                    if 'comments' in data:
                        comments = []
                        for comment_data in data['comments']:
                            comment_data['created_at'] = datetime.fromisoformat(comment_data['created_at'])
                            comment_data['updated_at'] = datetime.fromisoformat(comment_data['updated_at'])
                            comments.append(ForumPost(**comment_data))
                        data['comments'] = comments
                    
                    review = DesignReview(**data)
                    self.design_reviews[review.id] = review
        
        except Exception as e:
            self.logger.error(f"Error loading community data: {str(e)}")
            raise
    
    def create_forum_post(self, title: str, content: str, author_id: str,
                         tags: List[str]) -> ForumPost:
        """Create a new forum post.
        
        Args:
            title: Post title
            content: Post content
            author_id: Author's user ID
            tags: List of tags
            
        Returns:
            Created forum post
        """
        post = ForumPost(
            id=str(len(self._items) + 1),
            title=title,
            content=content,
            author_id=author_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags,
            replies=[],
            likes=0,
            views=0
        )
        
        # Use BaseManager's create method
        result = self.create(post.id, post)
        if result.success:
            self._save_forum_post(post)
            return post
        else:
            raise ValueError(f"Failed to create forum post: {result.message}")
    
    def create_project_share(self, title: str, description: str, author_id: str,
                            tags: List[str], files: Dict[str, str]) -> ProjectShare:
        """Share a project with the community.
        
        Args:
            title: Project title
            description: Project description
            author_id: Author's user ID
            tags: List of tags
            files: Dictionary of files to share
            
        Returns:
            Shared project
        """
        project = ProjectShare(
            id=str(len(self.shared_projects) + 1),
            title=title,
            description=description,
            author_id=author_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags,
            files=files,
            likes=0,
            downloads=0,
            comments=[]
        )
        
        self.shared_projects[project.id] = project
        self._save_project_share(project)
        
        return project
    
    def create_design_review(self, project_id: str, reviewer_id: str) -> DesignReview:
        """Create a new design review.
        
        Args:
            project_id: ID of project to review
            reviewer_id: Reviewer's user ID
            
        Returns:
            Created design review
        """
        review = DesignReview(
            id=str(len(self.design_reviews) + 1),
            project_id=project_id,
            reviewer_id=reviewer_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="pending",
            feedback=[],
            rating=0.0,
            comments=[]
        )
        
        self.design_reviews[review.id] = review
        self._save_design_review(review)
        
        return review
    
    def get_forum_posts(self, tags: Optional[List[str]] = None) -> List[ForumPost]:
        """Get forum posts, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            List of forum posts
        """
        result = self.list_all()
        if not result.success:
            return []
        
        posts = result.data
        
        if tags:
            # Filter by tags
            filtered_posts = []
            for post in posts:
                if any(tag in post.tags for tag in tags):
                    filtered_posts.append(post)
            return filtered_posts
        
        return posts
    
    def get_forum_post(self, post_id: str) -> Optional[ForumPost]:
        """Get a specific forum post.
        
        Args:
            post_id: Post ID
            
        Returns:
            Forum post if found
        """
        result = self.read(post_id)
        return result.data if result.success else None
    
    def update_forum_post(self, post_id: str, **kwargs) -> Optional[ForumPost]:
        """Update a forum post.
        
        Args:
            post_id: Post ID
            **kwargs: Fields to update
            
        Returns:
            Updated forum post if successful
        """
        result = self.read(post_id)
        if not result.success:
            return None
        
        post = result.data
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        post.updated_at = datetime.now()
        
        # Use BaseManager's update method
        update_result = self.update(post_id, post)
        if update_result.success:
            self._save_forum_post(post)
            return post
        else:
            self.logger.error(f"Failed to update forum post: {update_result.message}")
            return None
    
    def delete_forum_post(self, post_id: str) -> bool:
        """Delete a forum post.
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful
        """
        result = self.delete(post_id)
        if result.success:
            # Remove from disk
            post_file = self.forums_path / f"{post_id}.json"
            if post_file.exists():
                post_file.unlink()
            return True
        else:
            self.logger.error(f"Failed to delete forum post: {result.message}")
            return False
    
    def get_shared_projects(self, tags: Optional[List[str]] = None) -> List[ProjectShare]:
        """Get shared projects, optionally filtered by tags.
        
        Args:
            tags: Optional list of tags to filter by
            
        Returns:
            List of shared projects
        """
        projects = list(self.shared_projects.values())
        
        if tags:
            # Filter by tags
            filtered_projects = []
            for project in projects:
                if any(tag in project.tags for tag in tags):
                    filtered_projects.append(project)
            return filtered_projects
        
        return projects
    
    def get_design_reviews(self, project_id: Optional[str] = None) -> List[DesignReview]:
        """Get design reviews, optionally filtered by project ID.
        
        Args:
            project_id: Optional project ID to filter by
            
        Returns:
            List of design reviews
        """
        reviews = list(self.design_reviews.values())
        
        if project_id:
            # Filter by project ID
            return [review for review in reviews if review.project_id == project_id]
        
        return reviews
    
    def add_reply(self, post_id: str, content: str, author_id: str) -> ForumPost:
        """Add a reply to a forum post.
        
        Args:
            post_id: Parent post ID
            content: Reply content
            author_id: Author's user ID
            
        Returns:
            Created reply
        """
        # Get parent post
        parent_result = self.read(post_id)
        if not parent_result.success:
            raise ValueError(f"Parent post {post_id} not found")
        
        parent_post = parent_result.data
        
        # Create reply
        reply = ForumPost(
            id=f"{post_id}_reply_{len(parent_post.replies) + 1}",
            title=f"Re: {parent_post.title}",
            content=content,
            author_id=author_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=parent_post.tags,
            replies=[],
            likes=0,
            views=0
        )
        
        # Add reply to parent post
        parent_post.replies.append(reply)
        parent_post.updated_at = datetime.now()
        
        # Update parent post using BaseManager
        update_result = self.update(post_id, parent_post)
        if update_result.success:
            self._save_forum_post(parent_post)
            return reply
        else:
            raise ValueError(f"Failed to add reply: {update_result.message}")
    
    def add_review_feedback(self, review_id: str, feedback: Dict[str, Any]) -> None:
        """Add feedback to a design review.
        
        Args:
            review_id: Review ID
            feedback: Feedback data
        """
        if review_id not in self.design_reviews:
            raise ValueError(f"Review {review_id} not found")
        
        review = self.design_reviews[review_id]
        review.feedback.append(feedback)
        review.updated_at = datetime.now()
        
        self._save_design_review(review)
    
    def update_review_status(self, review_id: str, status: str) -> None:
        """Update the status of a design review.
        
        Args:
            review_id: Review ID
            status: New status
        """
        if review_id not in self.design_reviews:
            raise ValueError(f"Review {review_id} not found")
        
        review = self.design_reviews[review_id]
        review.status = status
        review.updated_at = datetime.now()
        
        self._save_design_review(review)
    
    def _validate_data(self, data: ForumPost) -> ManagerResult:
        """Validate data before storage.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result
        """
        try:
            if not data.id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Forum post ID is required",
                    errors=["Forum post ID cannot be empty"]
                )
            
            if not data.title:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Forum post title is required",
                    errors=["Forum post title cannot be empty"]
                )
            
            if not data.content:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Forum post content is required",
                    errors=["Forum post content cannot be empty"]
                )
            
            if not data.author_id:
                return ManagerResult(
                    success=False,
                    operation=ManagerOperation.VALIDATE,
                    status=ManagerStatus.FAILED,
                    message="Forum post author ID is required",
                    errors=["Forum post author ID cannot be empty"]
                )
            
            return ManagerResult(
                success=True,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.SUCCESS,
                message="Forum post validation successful"
            )
        except Exception as e:
            return ManagerResult(
                success=False,
                operation=ManagerOperation.VALIDATE,
                status=ManagerStatus.FAILED,
                message=f"Forum post validation failed: {e}",
                errors=[str(e)]
            )
    
    def _cleanup_item(self, key: str) -> None:
        """Clean up resources for a forum post.
        
        Args:
            key: Forum post ID to clean up
        """
        # Remove from disk
        post_file = self.forums_path / f"{key}.json"
        if post_file.exists():
            post_file.unlink()
    
    def _clear_cache(self) -> None:
        """Clear cache after data changes."""
        # Clear the cache - no additional disk operations needed
        super()._clear_cache()
    
    def _save_forum_post(self, post: ForumPost) -> None:
        """Save forum post to file.
        
        Args:
            post: Forum post to save
        """
        try:
            # Convert to dict for JSON serialization
            post_data = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author_id': post.author_id,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'tags': post.tags,
                'replies': [
                    {
                        'id': reply.id,
                        'title': reply.title,
                        'content': reply.content,
                        'author_id': reply.author_id,
                        'created_at': reply.created_at.isoformat(),
                        'updated_at': reply.updated_at.isoformat(),
                        'tags': reply.tags,
                        'replies': reply.replies,
                        'likes': reply.likes,
                        'views': reply.views
                    }
                    for reply in post.replies
                ],
                'likes': post.likes,
                'views': post.views
            }
            
            post_file = self.forums_path / f"{post.id}.json"
            with open(post_file, "w") as f:
                json.dump(post_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving forum post: {e}")
    
    def _save_project_share(self, project: ProjectShare) -> None:
        """Save project share to file.
        
        Args:
            project: Project share to save
        """
        try:
            # Convert to dict for JSON serialization
            project_data = {
                'id': project.id,
                'title': project.title,
                'description': project.description,
                'author_id': project.author_id,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
                'tags': project.tags,
                'files': project.files,
                'likes': project.likes,
                'downloads': project.downloads,
                'comments': [
                    {
                        'id': comment.id,
                        'title': comment.title,
                        'content': comment.content,
                        'author_id': comment.author_id,
                        'created_at': comment.created_at.isoformat(),
                        'updated_at': comment.updated_at.isoformat(),
                        'tags': comment.tags,
                        'replies': comment.replies,
                        'likes': comment.likes,
                        'views': comment.views
                    }
                    for comment in project.comments
                ]
            }
            
            project_file = self.projects_path / f"{project.id}.json"
            with open(project_file, "w") as f:
                json.dump(project_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving project share: {e}")
    
    def _save_design_review(self, review: DesignReview) -> None:
        """Save design review to file.
        
        Args:
            review: Design review to save
        """
        try:
            # Convert to dict for JSON serialization
            review_data = {
                'id': review.id,
                'project_id': review.project_id,
                'reviewer_id': review.reviewer_id,
                'created_at': review.created_at.isoformat(),
                'updated_at': review.updated_at.isoformat(),
                'status': review.status,
                'feedback': review.feedback,
                'rating': review.rating,
                'comments': [
                    {
                        'id': comment.id,
                        'title': comment.title,
                        'content': comment.content,
                        'author_id': comment.author_id,
                        'created_at': comment.created_at.isoformat(),
                        'updated_at': comment.updated_at.isoformat(),
                        'tags': comment.tags,
                        'replies': comment.replies,
                        'likes': comment.likes,
                        'views': comment.views
                    }
                    for comment in review.comments
                ]
            }
            
            review_file = self.reviews_path / f"{review.id}.json"
            with open(review_file, "w") as f:
                json.dump(review_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving design review: {e}") 
